# -*- coding: utf-8 -*-
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   MediaInfo.py
#   Project Valerie - Class to support media information
#
#   Created by user on 00/00/0000.
#   MediaInfo
#   
#   Revisions:
#   v1 - 15/07/2011 - Zuki - minor changes future to support SQL DB
#
#   v
#
#   v
#
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import os
import re
import replace
import Utf8

from Plugins.Extensions.ProjectValerie.__common__ import printl2 as printl
from Plugins.Extensions.ProjectValerie.__common__ import log

#------------------------------------------------------------------------------------------

## WORKAROUND

# Note a DVD is an Entry with Extension "ifo"
# These entries need special threatment

## WORKAROUND

class MediaInfo(object):
	#RecordStatus
	REC_NEW 	= 1
	REC_CHANGED 	= 2 
	REC_FROM_DB	= 3

	#MediaType
	MOVIE  		= 1
	SERIE 		= 2
	EPISODE 	= 3
	
	FAILEDSYNC 	= 0

	RecordStatus = REC_NEW  
	
	Id = None	# for Sql - Primary Key
			# in TXD initialized with:
			#    dbMovies:ImdbID   dbSeries/dbEpisodes:TheTvdbId
	MediaType = None # Not Used - only after db version 2 of Pickle
	isMovie   = False
	isSerie   = False
	isEpisode = False
	
	isEnigma2MetaRecording = False
	
	isXbmcNfo = False
	
	LanguageOfPlot = u"en"
	
	Path         = u""
	Filename     = u""
	Extension    = u""
	SearchString = u""
	
	Title = u""
	Alternatives = {}
	
	Year  = -1
	Month = -1
	Day   = -1
	ImdbIdNull     = u"tt0000000"
	ImdbId        = ImdbIdNull
	TheTvDbIdNull = u"0"
	TheTvDbId     = TheTvDbIdNull
	TmDbIdNull    = u"0"
	TmDbId        = TmDbIdNull
	
	Runtime	= 0
	Resolution = u"576"
	Sound	  = u"Stereo"
	Plot	   = u""
	
	Directors  = []
	Writers    = []
	Genres     = u""
	Tag        = u""
	Popularity = 0
	
	Season  = -1
	Episode = -1		
	EpisodeText = u""	 # for example: Episode Number:Special / Pilot (not numbered)
	syncStatus  = 0
	syncFailedCause = u""
	
	Poster   = u""
	Backdrop = u""
	Banner   = u""

	def __init__(self, path = None, filename = None, extension = None):
		try:
			if path is not None and filename is not None and extension is not None:
				self.Path      = path
				self.Filename  = filename
				self.Extension = extension
				
				self.Alternatives = {}
				self.Directors    = []
				self.Writers      = []
		except Exception, ex:
			printls("Exception (ef): " + str(ex), self, "E")

	def copy(self):
		try:
			m = MediaInfo(self.Path, self.Filename, self.Extension)
			
			m.Alternatives = self.Alternatives
			m.Directors    = self.Directors
			m.Writers      = self.Writers
			m.Genres       = self.Genres
			m.Runtime      = self.Runtime
			m.Tag          = self.Tag
			m.Popularity   = self.Popularity
			m.Plot         = self.Plot
			
			m.Id           = self.Id
			m.ImdbId       = self.ImdbId
			m.isXbmcNfo    = self.isXbmcNfo
			m.TheTvDbId    = self.TheTvDbId
			m.Title        = self.Title
			m.Year         = self.Year
			m.Month        = self.Month
			m.Day          = self.Day
			m.Resolution   = self.Resolution
			m.Sound        = self.Sound
			m.isMovie      = self.isMovie
			m.isSerie      = self.isSerie
			m.isEpisode    = self.isEpisode
			m.Poster       = self.Poster
			m.Backdrop     = self.Backdrop
			m.Season       = self.Season
			m.Episode      = self.Episode
			m.SearchString = self.SearchString
			m.MediaType    = self.MediaType
			m.RecordStatus = self.RecordStatus
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")
		return m

	def isEnigma2Recording(self, name):
		try:
			printl("META: " + str(Utf8.utf8ToLatin(name + u".meta")), self)
			if os.path.isfile(Utf8.utf8ToLatin(name + u".meta")):
				return True
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")
		return False

	class Enimga2MetaInfo:
		MovieName = u""
		EpisodeName  = u""
		IsMovie = False
		IsEpisode = False
		
		def __init__(self, movieName, episodeName):
			try:
				self.MovieName = movieName.strip()
				self.EpisodeName = episodeName.strip()
				
				if self.MovieName == self.EpisodeName:
					printl("IS Movie", self)
					self.IsMovie = True
					self.IsEpisode = False
					self.MediaType = MediaInfo.MOVIE
				else:
					printl("IS Episode", self)
					self.IsMovie = False
					self.IsEpisode = True
					self.MediaType = MediaInfo.EPISODE
			except Exception, ex:
				printl("Exception (ef): " + str(ex), self, "E")

	def getEnigma2RecordingName(self, name):
		try:
			e2info = None
			printl("Read from '" + name + u".meta" + "'", self, "I")
			f = Utf8.Utf8(name + u".meta", "r")
			lines = f.read()
			if lines is None:
				f.close()
				f = open(name + u".meta", "r")
				lines = f.read()
				lines = Utf8.stringToUtf8(lines)
			if lines is not None:
				lines = lines.split(u"\n")
				if len(lines) > 2:
					printl("MovieName = '" + lines[1] + "' - EpisodeName = '" + lines[2] + "'", self, "I")
					e2info = self.Enimga2MetaInfo(lines[1], lines[2])
			f.close()
			return e2info
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")
			return None
		return None

	def isValerieInfoAvailable(self, path):
		try:
			if os.path.isfile(Utf8.utf8ToLatin(path + u"/valerie.info")):
				return True
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")
		return False

	def getValerieInfo(self, path):
		try:
			f = Utf8.Utf8(path + u"/valerie.info", "r")
			lines = f.read()
			if lines is not None:
				lines = lines.split(u"\n")
				name = None
				if len(lines) >= 1:
					name = lines[0]
			f.close()
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")
		return name

	def getValerieInfoLastAccessTime(self, path):
		time = 0
		try:
			if os.path.isfile(Utf8.utf8ToLatin(path + u"/.access")):
				f = Utf8.Utf8(path + u"/.access", "r")
				lines = f.read()
				if lines is not None:
					lines = lines.split(u"\n")
					if len(lines) >= 1:
						try:
							lines = lines[0].split(".")
							time = int(lines[0])
						except Exception, ex:
							printl("Exception: " + str(ex), self)
							printl("\t" + str(Utf8.utf8ToLatin(path + u"/.access")), self)
				f.close()
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")
		return time

	def getValerieInfoAccessTime(self, path):
		time = 0
		try:
			if os.path.isfile(Utf8.utf8ToLatin(path + u"/valerie.info")):
				try:
					time = int(os.path.getctime(Utf8.utf8ToLatin(path + u"/valerie.info")))
				except Exception, ex:
							printl("Exception: " + str(ex), self)
							printl("\t" + str(Utf8.utf8ToLatin(path + u"/valerie.info")), self)
		
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")
		return time

	def setValerieInfoLastAccessTime(self, path):
		try:
			if os.path.isfile(Utf8.utf8ToLatin(path + u"/valerie.info")):
				time = int(os.path.getctime(Utf8.utf8ToLatin(path + u"/valerie.info")))
				f = Utf8.Utf8(path + u"/.access", "w")
				time = f.write(str(time) + u"\n")
				f.close()
			elif os.path.isfile(Utf8.utf8ToLatin(path + u"/.access")):
				os.remove(Utf8.utf8ToLatin(path + u"/.access"))
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")

	def isNfoAvailable(self, name):
		try:
			printl("Check presence of nfo file: " + Utf8.utf8ToLatin(name + u".nfo"), self, "I")
			if os.path.isfile(Utf8.utf8ToLatin(name + u".nfo")):
				return True
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")
		return False

	def parseNfo(self, name):
		try:
			printl("About to read from nfo-file: " + name + u".nfo", self, "I")
			f = Utf8.Utf8(name + u".nfo", "r")
			lines = f.read()
			if lines is not None:
				printl("Checking type of file...", self, "I")
				lines = lines.split(u"\n")
				if len(lines) > 1:
					lines[1] = lines[1].strip()
					if lines[1].startswith("<movie") or lines[1].startswith("<episodedetails>"):
						printl("Found xbmc-style nfo...", self, "I")
						self.isXbmcNfo = True
						f.close()
						return self.parseNfoXbmc(lines)
					else:
						printl("Might be IMDb-ID nfo...", self, "I")
						f.close()
						return self.getImdbIdFromNfo(lines)
				else:
					f.close()
					return None
			f.close()
			return None
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")

	def parseNfoXbmc(self, lines):
		printl("", self)
		try:
			for line in lines:
				line = line.strip()
				if line.startswith("<id>"):
					line = line.replace("id", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					if lines[1].startswith("<movie"):
						self.isMovie = True
						self.isSerie = False
						self.isEpisode = False
						self.MediaType = self.MOVIE
						
						self.ImdbId = line
					elif lines[1].startswith("<episodedetails>"):
						self.isMovie = False
						self.isSerie = True
						self.isEpisode = False
						self.MediaType = self.SERIE
						
						self.TheTvDbId = line
				elif line.startswith("<title>"):
					line = line.replace("title", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					self.Title = line
				elif line.startswith("<season>"):
					line = line.replace("season", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					self.Season = int(re.sub(r'\D+', '', line))
				elif line.startswith("<episode>"):
					line = line.replace("episode", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					self.Episode = int(re.sub(r'\D+', '', line))
				elif line.startswith("<year>"):
					line = line.replace("year", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					self.Year = int(re.sub(r'\D+', '', line))
				elif line.startswith("<plot>"):
					line = line.replace("plot", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					self.Plot = line
				elif line.startswith("<runtime>"):
					line = line.replace("runtime", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					self.Runtime = int(re.sub(r'\D+', '', line))
				elif line.startswith("<genre>"):
					line = line.replace("genre", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					self.Genres = line
				elif line.startswith("<rating>"):
					line = line.replace("rating", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					self.Popularity = int(round(float(line)))
				elif line.startswith("<tagline>"):
					line = line.replace("tagline", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					self.Tag = line
				elif line.startswith("<codec>"):
					line = line.replace("codec", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					self.Sound = line
				elif line.startswith("<width>"):
					line = line.replace("width", "")
					line = line.replace("<>", "")
					line = line.replace("</>", "")
					self.Resolution = line
			return self
		
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")
		return self

	def getImdbIdFromNfo(self, lines):
		printl("", self)
		try:
			for line in lines:
				m = re.search(r'(?P<imdbid>tt\d{7})', line)
				if m and m.group("imdbid"):
					self.ImdbId = m.group("imdbid")
					printl("Found IMDb-ID = " + str(self.ImdbId), self, "I")
					return self
				else:
					return None
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")
		return None

	def parse(self, useParentFoldernameAsSearchstring=False):
		absFilename = self.Path + u"/" + self.Filename + u"." + self.Extension
		name = self.Filename.lower()
		self.SearchString = name
		valerieInfoSearchString = None
		
		if self.isValerieInfoAvailable(self.Path) is True:
			valerieInfoSearchString = self.getValerieInfo(self.Path).strip()
			printl("Found valerie.info containing: " + str(Utf8.utf8ToLatin(valerieInfoSearchString)), self)
			if valerieInfoSearchString == u"ignore":
				printl("=> found 'ignore'... Returning to sync process and skipping!", self, "I")
				return False
		
		#################### DVD #####################
		
		if self.Extension.lower() == u"ifo":
			dirs = self.Path.split(u"/")
			#vidoets = dirs[len(dirs) - 1]
			printl("dirs=" + str(dirs), self)
			self.SearchString = dirs[len(dirs) - 2]
			printl("DVD: " + str(Utf8.utf8ToLatin(self.SearchString)), self)
			#return True
		
		#################### DVD ######################
		
		### Replacements PRE
		printl("[pre] - " + str(self.SearchString), self)
		for replacement in replace.replacements(u"pre"):
			log("[pre] " + str(replacement[0]) + " --> " + str(replacement[1]), self)
			self.SearchString = re.sub(replacement[0], replacement[1], self.SearchString)
			log("\t" + str(self.SearchString), self)
		
		printl(":-1: " + str(Utf8.utf8ToLatin(self.SearchString)), self)
		
		###
		printl("Check for IMDb-ID in filename '" + name + "'", self, "I")
		m = re.search(r'(?P<imdbid>tt\d{7})', name)
		if m and m.group("imdbid"):
			self.ImdbId = m.group("imdbid")
			printl(" => found IMDb-ID = " + str(self.ImdbId), self, "I")
		
		if self.isNfoAvailable(self.Path + u"/" + self.Filename):
			printl("nfo File present - now parsing: " + self.Path + u"/" + self.Filename, self, "I")
			result = self.parseNfo(self.Path + u"/" + self.Filename)
			if result is not None:
				printl(" => nfo File successfully parsed!", self, "I")
				self.isMovie = result.isMovie
				self.isEpisode = result.isEpisode
				self.isSerie = result.isSerie
				self.MediaType = self.MediaType
				
				self.TheTvDbId = result.TheTvDbId
				self.ImdbId = result.ImdbId
				self.Title = result.Title
				self.Plot = result.Plot
				
				self.Season = result.Season
				self.Episode = result.Episode
				
				self.Year = result.Year
				self.Genres = result.Genres
				self.Runtime = result.Runtime
				
				if self.isXbmcNfo == True:
					printl("XBMC-style nfo => return to sync()", self, "I")
					return True
			else:
				printl("Something went wrong while reading from nfo :-(", self, "I")
		
		###  
		if self.Year == -1:
			m = re.search(r'\s(?P<year>\d{4})\s', self.SearchString)
			if m and m.group("year"):
				year = int(m.group("year"))
				printl("year=" + str(year), self)
				if year > 1940 and year < 2012:
					self.Year = year
					# removing year from searchstring
					#self.SearchString = re.sub(str(year), u" ", self.SearchString)
					#self.SearchString = name[:m.start()]
		
		printl(":0: " + str(Utf8.utf8ToLatin(self.SearchString)), self)
		
		###	
		m = re.search(r'720p', name)
		if m:
			self.Resolution = u"720p"
		else:
			m = re.search(r'1080i', name)
			if m:
				self.Resolution = u"1080i"
			else:
				m = re.search(r'1080p', name)
				if m:
					self.Resolution = u"1080p"
		
		###	
		m = re.search(r'dts', name)
		if m:
			self.Sound = u"dts"
		else:
			m = re.search(r'dd5', name)
			if m:
				self.Sound = u"ac3"
			else:
				m = re.search(r'ac3', name)
				if m:
					self.Sound = u"ac3"
		
		#nameConverted = name
		
		if not self.isTypeMovie():
			printl("(isMovie is False) => assuming TV show - trying to get season and episode from SearchString: " + self.SearchString, self, "I")
			#####
			#####  s03e05
			#####
			
			if self.Season == -1 or self.Episode == -1:
				m = re.search(r'\Ws(?P<season>\d+)\s?e(?P<episode>\d+)(\D|$)', self.SearchString)
				if m and m.group("season") and m.group("episode"):
					self.isSerie = True
					self.isMovie = False
					self.MediaType = self.SERIE
					
					self.Season = int(m.group("season"))
					self.Episode = int(m.group("episode"))
					
					self.SearchString = re.sub(r's(?P<season>\d+)\s?e(?P<episode>\d+).*', u" ", self.SearchString)
			
			#####
			#####  s03e05e06 s03e05-e06
			#####
			
			if self.Season == -1 or self.Episode == -1:
				m = re.search(r'\Ws(?P<season>\d+)\s?e(?P<episode>\d+)[-]?\s?e?(?P<episode2>\d+)(\D|$)', self.SearchString)
				if m and m.group("season") and m.group("episode"):
					self.isSerie = True
					self.isMovie = False
					self.MediaType = self.SERIE
					
					self.Season = int(m.group("season"))
					self.Episode = int(m.group("episode"))
					
					self.SearchString = re.sub(r's(?P<season>\d+)\s?e(?P<episode>\d+)[-]?\s?e?(?P<episode2>\d+).*', u" ", self.SearchString)
			
			#####
			#####  3x05
			#####
			
			if self.Season == -1 or self.Episode == -1:  
				m = re.search(r'\D(?P<season>\d+)x(?P<episode>\d+)(\D|$)', self.SearchString)
				if m and m.group("season") and m.group("episode"):
					self.isSerie = True
					self.isMovie = False
					self.MediaType = self.SERIE

					self.Season = int(m.group("season"))
					self.Episode = int(m.group("episode"))
					
					self.SearchString = re.sub(r'(?P<season>\d+)x(?P<episode>\d+).*', u" ", self.SearchString)
			
			#####
			#####  part 3
			#####
			
			if self.Season == -1 or self.Episode == -1:
				m = re.search(r'\W(part|pt)\s?(?P<episode>\d+)(\D|$)', self.SearchString)
				if m and m.group("episode"):
					self.isSerie = True
					self.isMovie = False
					self.MediaType = self.SERIE
					
					self.Season = int(0)
					self.Episode = int(m.group("episode"))
					
					self.SearchString = re.sub(r'(part|pt)\s?(?P<episode>\d+).*', u" ", self.SearchString)
			
			#####
			#####  305
			#####
			
			if self.Season == -1 or self.Episode == -1:
			
				nameConverted = u""
				prevc = u"a"
				for c in self.SearchString:
					if (prevc.isdigit() and c.isdigit()) or (prevc.isdigit() is False and c.isdigit() is False):
						nameConverted += c
					else:
						nameConverted += " " + c
					prevc = c
				
				printl("[[[ " + str(Utf8.utf8ToLatin(nameConverted)), self)
				
				nameConverted = nameConverted.strip()
				
				m = re.search(r'\D(?P<seasonepisode>\d{3,4})(\D|$)', nameConverted)
				if m and m.group("seasonepisode"):
					se = int(-1)
					s = int(-1)
					e = int(-1)
					
					se = int(m.group("seasonepisode"))
					
					s = se / 100
					e = se % 100
					
					if (s == 2 and e == 64 or s == 7 and e == 20 or s == 10 and e == 80 or s == 0 or s == 19 and e >= 40 or s == 20 and e <= 14) is False:
						self.isSerie = True
						self.isMovie = False
						self.MediaType = self.SERIE
						
						self.Season = s
						self.Episode = e
						
						self.SearchString = re.sub(r'(?P<seasonepisode>\d{3,4}).*', u" ", nameConverted)
		
		printl(":2: " + str(Utf8.utf8ToLatin(self.SearchString)) + " " + str(self.Season) + " " + str(self.Episode) + " " + str(self.Year), self)
		
		if self.Extension == u"ts" and self.isEnigma2Recording(absFilename) is True:
			printl("Extension == 'ts' and E2 meta file found => retrieving name from '" + absFilename + "'", self, "I")
			e2info = self.getEnigma2RecordingName(absFilename)
			if e2info is not None:
				printl("e2info: "+ str(Utf8.utf8ToLatin(e2info.MovieName)) + " - " + str(Utf8.utf8ToLatin(e2info.EpisodeName) + "," + str(e2info.IsMovie) + "," + str(e2info.IsEpisode)), self)
				if self.isTypeMovie():
					printl("Assuming Movie...", self, "I")
					self.SearchString = e2info.MovieName
					self.isMovie = True
					self.isSerie = False
					self.MediaType = self.MOVIE
				elif self.isTypeEpisode():
					# Issue #205, efo => since we have dedicated name + episode name use quotes to enhance google search result
					self.SearchString = "\"" + e2info.MovieName +"\"" +  ":: " + "\"" + e2info.EpisodeName + "\""
					printl("Assuming TV-Show", self, "I")
					self.isMovie = False
					self.isSerie = True
					self.MediaType = self.SERIE
					
				self.isEnigma2MetaRecording = True
				printl("e2info:: Returning to sync process using SearchString '" + str(Utf8.utf8ToLatin(self.SearchString)) + "'", self)
				return True
		
		if valerieInfoSearchString is not None:
			self.SearchString = valerieInfoSearchString
			printl("Returning to sync process using SearchString '" + str(Utf8.utf8ToLatin(self.SearchString)) + "'", self)
			return True
		
		if self.isSerie == False:
			self.isMovie = True
			self.MediaType = self.MOVIE
		
		# So we got year and season and episode 
		# now we can delete everything after the year
		# but only if the year is not the first word in the string
		if self.Year != -1:
			printl("Adapt SearchString due to year...", self, "I")
			pos = self.SearchString.find(str(self.Year))
			if pos > 0:
				self.SearchString = self.SearchString[:pos]
				printl(" => SearchString now set to '" + self.SearchString + "'", self, "I")
		
		#print ":1: ", self.SearchString
		### Replacements POST
		printl("rpost: " + str(Utf8.utf8ToLatin(self.SearchString)), self)
		self.SearchString = re.sub(r'[-]', u" ", self.SearchString)
		self.SearchString = re.sub(r' +', u" ", self.SearchString)
		printl("rpost:: " + str(Utf8.utf8ToLatin(self.SearchString)), self)
		
		self.SearchString = self.SearchString.strip()
		
		post = u"post"
		if self.isSerie:
			post = u"post_tv"
		elif self.isTypeMovie():
			post = u"post_movie"
			
		for replacement in replace.replacements(post):
			#print "[" + post + "] ", replacement[0], " --> ", replacement[1]
			self.SearchString = re.sub(replacement[0], replacement[1], self.SearchString)
		
		if useParentFoldernameAsSearchstring:
			printl("Building search string from parent folder names...", self, "I")
			try:
				folders = self.Path.split("/")
				self.SearchString = folders[len(folders) - 1]
			except Exception, ex:
				printl("Exception: " + str(ex), self, "E")
		
		self.SearchString = self.SearchString.strip()
		printl("eof: SearchString:" + str(Utf8.utf8ToLatin(self.SearchString)), self)
		
		return True

	def __str__(self):
		ustr = u""
		try:
			ustr = self.Path + u" / " + self.Filename + u" . " + self.Extension
			#printl("type(ustr): " + str(type(ustr)), self)
			ustr += u"\n\tImdbId:	   " + self.ImdbId
			ustr += u"\n\tTheTvDbId:	" + self.TheTvDbId
			ustr += u"\n\tTitle:		" + self.Title
			ustr += u"\n\tSearchString: " + self.SearchString
			ustr += u"\n\tYear:		 " + unicode(self.Year)
			ustr += u"\n\tMonth:		" + unicode(self.Month)
			ustr += u"\n\tDay:		  " + unicode(self.Day)
			ustr += u"\n\tResolution:   " + self.Resolution
			ustr += u"\n\tSound:		" + self.Sound
			#ustr += "\n\tAlternatives: " + unicode(self.Alternatives)
			#ustr += "\n\tDirectors:	" + unicode(self.Directors)
			#ustr += "\n\tWriters:	  " + unicode(self.Writers)
			ustr += "\n\tRuntime:	  " + unicode(self.Runtime)
			ustr += "\n\tGenres:	   " + unicode(self.Genres)
			ustr += "\n\tTagLine:	  " + self.Tag
			ustr += "\n\tPopularity:   " + unicode(self.Popularity)
			ustr += "\n\tPlot:		 " + self.Plot
			if self.isEpisode:
				ustr += "\n\tSeason:	   " + unicode(self.Season)
				ustr += "\n\tEpisode:	  " + unicode(self.Episode)
			ustr += "\n\n"
			#ustr += "\n\tPoster:	   " + unicode(self.Poster)
			#ustr += "\n\tBackdrop:	 " + unicode(self.Backdrop)
			#ustr += "\n\n"
			#printl("type(ustr): " + str(type(ustr)), self)
		
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")
		return Utf8.utf8ToLatin(ustr)

	def importStr(self, string, isMovie=False, isSerie=False, isEpisode=False):
		try:
			self.isMovie = isMovie
			self.isSerie = isSerie
			self.isEpisode = isEpisode
			
			lines = string.split(u'\n')
			for line in lines: 
				#print "Line: ", line
				if u":" in line: 
					key, value = (s.strip() for s in line.split(u":", 1)) 
				
				if key == u"ImdbId":
					self.ImdbId = value
				if key == u"TheTvDb":
					self.TheTvDbId = value
				
				elif key == u"Title":
					self.Title = value
				
				elif key == u"Year":
					if len(value) > 0:
						try:
							self.Year = int(value)
						except Exception, ex:
							printl("Exception: " + str(ex), self)
							self.Year = 0
					else:
						self.Year = 0
				
				elif key == u"Path":
					self.Path, self.Filename = value.rsplit(u"/", 1)
					#print self.Filename
					self.Filename, self.Extension = self.Filename.rsplit(u'.', 1)
				
				elif key == u"Plot":
					self.Plot = value
				elif key == u"Runtime":
					if len(value) > 0:
						value = value.replace(u"min", "").strip()
						try:
							self.Runtime = int(value)
						except Exception, ex:
							printl("Exception: " + str(ex), self)
							self.Runtime = 0
					else:
						self.Runtime = 0
				elif key == u"Tag":
					self.Tag = value  
				elif key == u"Popularity":
					if len(value) > 0:
						try:
							self.Popularity = int(value)
						except Exception, ex:
							printl("Exception: " + str(ex), self)
							self.Popularity = 0
					else:
						self.Popularity = 0
				elif key == u"Season":
					if len(value) > 0:
						try:
							self.Season = int(value)
						except Exception, ex:
							printl("Exception: " + str(ex), self)
							self.Season = 0
					else:
						self.Season = 0
				elif key == u"Episode":
					if len(value) > 0:
						try:
							self.Episode = int(value)
						except Exception, ex:
							printl("Exception: " + str(ex), self)
							self.Episode = 0
					else:
						self.Episode = 0
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")

	def importDefined(self, lines, level, isMovie=False, isSerie=False, isEpisode=False):
		try:
			self.isMovie = isMovie
			self.isSerie = isSerie
			self.isEpisode = isEpisode
			
			if self.isTypeMovie():
				if level >=3:
					self.Id     = lines[0]
					self.ImdbId = lines[0]
					self.Title  = lines[1]
					self.Tag    = lines[2]
					self.Year   = int(lines[3])
					self.Month  = int(lines[4])
					self.Day    = int(lines[5])
					
					self.Path      = lines[6]
					self.Filename  = lines[7]
					self.Extension = lines[8]
					
					self.Plot       = lines[9]
					self.Runtime    = int(lines[10])
					self.Popularity = int(lines[11])
					
					self.Genres = lines[12]
				else:
					self.Id     = lines[0]
					self.ImdbId = lines[0]
					self.Title  = lines[1]
					self.Tag    = lines[2]
					self.Year   = int(lines[3])
					
					self.Path      = lines[4]
					self.Filename  = lines[5]
					self.Extension = lines[6]
					
					self.Plot       = lines[7]
					self.Runtime    = int(lines[8])
					self.Popularity = int(lines[9])
					
					self.Genres = lines[10]
			
			elif self.isTypeSerie():
				if level >=3:
					self.Id        = lines[1]
					self.ImdbId    = lines[0]
					self.TheTvDbId = lines[1]
					self.Title     = lines[2]
					self.Tag       = lines[3]
					self.Year      = int(lines[4])
					self.Month     = int(lines[5])
					self.Day       = int(lines[6])
					
					self.Plot       = lines[7]
					self.Runtime    = int(lines[8])
					self.Popularity = int(lines[9])
					
					self.Genres = lines[10]
				else:
					self.Id        = lines[1]
					self.ImdbId    = lines[0]
					self.TheTvDbId = lines[1]
					self.Title     = lines[2]
					self.Tag       = lines[3]
					self.Year      = int(lines[4])
					
					self.Plot       = lines[5]
					self.Runtime    = int(lines[6])
					self.Popularity = int(lines[7])
					
					self.Genres = lines[8]
			
			elif self.isTypeEpisode():
				if level >=3:
					self.Id        = lines[0]
					self.TheTvDbId = lines[0]
					self.Title     = lines[1]
					self.Year      = int(lines[2])
					self.Month     = int(lines[3])
					self.Day       = int(lines[4])
					
					self.Path      = lines[5]
					self.Filename  = lines[6]
					self.Extension = lines[7]
					
					self.Season    = int(lines[8])
					self.Episode   = int(lines[9])
					
					self.Plot       = lines[10]
					self.Runtime    = int(lines[11])
					self.Popularity = int(lines[12])
					
					self.Genres = lines[13]
				else:
					self.Id        = lines[0]
					self.TheTvDbId = lines[0]
					self.Title     = lines[1]
					self.Year      = int(lines[2])
					
					self.Path      = lines[3]
					self.Filename  = lines[4]
					self.Extension = lines[5]
					
					self.Season    = int(lines[6])
					self.Episode   = int(lines[7])
					
					self.Plot       = lines[8]
					self.Runtime    = int(lines[9])
					self.Popularity = int(lines[10])
					
					self.Genres = lines[11]
		except Exception, ex:
			printl("Exception (ef): " + str(ex), self, "E")

	def export(self):
		stri = u'\n---BEGIN---'
		if self.isTypeMovie():
			stri += u'\nImdbId: ' +	 self.ImdbId
			stri += u'\nTitle: ' +	  self.Title
			stri += u'\nYear: ' +	   unicode(self.Year)
			stri += u'\nPath: ' +	   self.Path + u"/" + self.Filename + u"." + self.Extension
			stri += u'\nPlot: ' +	   self.Plot
			stri += u'\nRuntime: ' +	unicode(self.Runtime)
			stri += u'\nGenres: ' +	 self.Genres
			stri += u'\nTag: ' +		self.Tag
			stri += u'\nPopularity: ' + unicode(self.Popularity)
			stri += u'\nDirectors: ' +  u"---"
			stri += u'\nWriters: ' +	u"---"
		
		elif self.isTypeSerie():
			stri += u'\nImdbId: ' +	 self.ImdbId
			stri += u'\nTheTvDb: ' +	self.TheTvDbId
			stri += u'\nTitle: ' +	  self.Title
			stri += u'\nYear: ' +	   unicode(self.Year)
			stri += u'\nPlot: ' +	   self.Plot
			stri += u'\nRuntime: ' +	unicode(self.Runtime)
			stri += u'\nGenres: ' +	 self.Genres
			stri += u'\nTag: ' +		self.Tag
			stri += u'\nPopularity: ' + unicode(self.Popularity)
			stri += u'\nDirectors: ' +  u"---"
			stri += u'\nWriters: ' +	u"---"
		
		elif self.isTypeEpisode():
			stri += u'\nImdbId: ' +	 self.ImdbId
			stri += u'\nTheTvDb: ' +	self.TheTvDbId
			stri += u'\nTitle: ' +	  self.Title
			stri += u'\nYear: ' +	   unicode(self.Year)
			stri += u'\nPath: ' +	   self.Path + u"/" + self.Filename + u"." + self.Extension
			stri += u'\nPlot: ' +	   self.Plot
			stri += u'\nRuntime: ' +	unicode(self.Runtime)
			stri += u'\nGenres: ' +	 self.Genres
			stri += u'\nTag: ' +		self.Tag
			stri += u'\nPopularity: ' + unicode(self.Popularity)
			stri += u'\nSeason: ' +	 unicode(self.Season)
			stri += u'\nEpisode: ' +	unicode(self.Episode)
			stri += u'\nDirectors: ' +  u"---"
			stri += u'\nWriters: ' +	u"---"
		
		stri += u'\n----END----\n\n'
		return stri

	def exportDefined(self, level):
		# Workaround, can be removed in the future
		self.Plot = re.sub("\n", " ", self.Plot).strip()
		
		stri = u''
		try:
			if self.isTypeMovie():
				stri += self.ImdbId + u'\n'
				stri += self.Title + u'\n'
				stri += self.Tag + u'\n'
				stri += unicode(self.Year) + u'\n'
				if level >=3:
					stri += unicode(self.Month) + u'\n'
					stri += unicode(self.Day) + u'\n'
				
				stri += self.Path + u'\n'
				stri += self.Filename + u'\n'
				stri += self.Extension + u'\n'
				
				stri += self.Plot + u'\n'
				stri += unicode(self.Runtime) + u'\n'
				stri += unicode(self.Popularity) + u'\n'
				
				stri += self.Genres + u'\n'
			
			elif self.isTypeSerie():
				stri += self.ImdbId + u'\n'
				stri += self.TheTvDbId + u'\n'
				stri += self.Title + u'\n'
				stri += self.Tag + u'\n'
				stri += unicode(self.Year) + u'\n'
				if level >=3:
					stri += unicode(self.Month) + u'\n'
					stri += unicode(self.Day) + u'\n'
				
				stri += self.Plot + u'\n'
				stri += unicode(self.Runtime) + u'\n'
				stri += unicode(self.Popularity) + u'\n'
				
				stri += self.Genres + u'\n'
			
			elif self.isTypeEpisode():
				stri += self.TheTvDbId + u'\n'
				stri += self.Title + u'\n'
				stri += unicode(self.Year) + u'\n'
				if level >=3:
					stri += unicode(self.Month) + u'\n'
					stri += unicode(self.Day) + u'\n'
				
				stri += self.Path + u'\n'
				stri += self.Filename + u'\n'
				stri += self.Extension + u'\n'
	
				stri += unicode(self.Season) + u'\n'
				stri += unicode(self.Episode) + u'\n'
	
				stri += self.Plot + u'\n'
				stri += unicode(self.Runtime) + u'\n'
				stri += unicode(self.Popularity) + u'\n'
				
				stri += self.Genres + u'\n'
		except Exception, ex:
			printl("Exception: " + str(ex), self, "E")
		stri += u''
		return stri


	def getMediaType(self):		
		if self.MediaType is None:
			if self.isSerie:
				self.MediaType = self.SERIE
			elif self.isMovie:
				self.MediaType = self.MOVIE
			elif self.isEpisode:
				self.MediaType = self.EPISODE
		return self.MediaType
	
	def setMediaType(self, value):
		printl("->", self)
		self.MediaType = value
		#compatibility
		self.isSerie   = False;
		self.isMovie   = False;
		self.isEpisode = False;
		if self.MediaType == self.SERIE:
			self.isSerie = True
		elif self.MediaType == self.MOVIE:
			self.isMovie = True
		elif self.MediaType == self.EPISODE:
			self.isEpisode = True
	
	def isTypeMovie(self):
		return (self.getMediaType()==self.MOVIE)
	def isTypeSerie(self):
		return (self.getMediaType()==self.SERIE)
	def isTypeEpisode(self):
		return (self.getMediaType()==self.EPISODE)
		
		
		