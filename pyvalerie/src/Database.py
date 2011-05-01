# -*- coding: utf-8 -*-

import cPickle   as pickle
from   datetime import date
import os
import time

import Config
import DirectoryScanner
from   FailedEntry       import FailedEntry
import Genres
from   MediaInfo         import MediaInfo
import Utf8
from   db_handler import db_handler
from Plugins.Extensions.ProjectValerie.__common__ import printl2 as printl

#------------------------------------------------------------------------------------------

class Database(object):

	def __init__(self):
		self.dbMovies = {}
		self.dbSeries = {}
		self.dbEpisodes = {}
		
		self.dbFailed = []
		
		self.duplicateDetector = []

	def reload(self):
		self.dbMovies = {}
		self.dbSeries = {}
		self.dbEpisodes = {}
		
		self.dbFailed = []
		
		self.duplicateDetector = []
		
		self.load()

	def transformGenres(self):
		if Config.getBoolean("sqlite") is True:
			db = db_handler()
			db.queryMultipleRows("SELECT DISTINCT genre_text from genres")
		else:  
			for key in self.dbMovies:
				transformedGenre = ""
				for genre in self.dbMovies[key].Genres.split("|"):
					if Genres.isGenre(genre) is False:
						newGenre = Genres.getGenre(genre)
						if newGenre != "Unknown":
							printl("GENRE: " + str(genre) + " -> " + str(newGenre), self)
							transformedGenre += newGenre + u"|"
					else:
						transformedGenre += genre + u"|"
				if len(transformedGenre) > 0:
					transformedGenre = transformedGenre[:len(transformedGenre) - 1] # Remove the last pipe
				self.dbMovies[key].Genres = transformedGenre
			
			for key in self.dbSeries:
				transformedGenre = ""
				for genre in self.dbSeries[key].Genres.split("|"):
					if Genres.isGenre(genre) is False:
						newGenre = Genres.getGenre(genre)
						if newGenre != "Unknown":
							printl("GENRE: " + str(genre) + " -> " + str(newGenre), self)
							transformedGenre += newGenre + u"|"
					else:
						transformedGenre += genre + u"|"
				if len(transformedGenre) > 0:
					transformedGenre = transformedGenre[:len(transformedGenre) - 1] # Remove the last pipe
				self.dbSeries[key].Genres = transformedGenre
				
				if key in self.dbEpisodes:
					for season in self.dbEpisodes[key]:
						for episode in self.dbEpisodes[key][season]:
							transformedGenre = ""
							for genre in self.dbEpisodes[key][season][episode].Genres.split("|"):
								if Genres.isGenre(genre) is False:
									newGenre = Genres.getGenre(genre)
									if newGenre != "Unknown":
										printl("GENRE: " + str(genre) + " -> " + str(newGenre), self)
										transformedGenre += newGenre + u"|"
								else:
									transformedGenre += genre + u"|"
							if len(transformedGenre) > 0:
								transformedGenre = transformedGenre[:len(transformedGenre) - 1] # Remove the last pipe
							self.dbEpisodes[key][season][episode].Genres = transformedGenre

	def clearFailed(self):
		try:
			del self.dbFailed[:]
			#self.dbFailed = []
		except Exception, ex:
			printl("Exception: " + str(ex), self)

	def addFailed(self, entry):
		self.dbFailed.append(entry)

	def removeFailed(self, entry):
		if entry in self.dbFailed:
			self.dbFailed.remove(entry)

	def deleteMissingFiles(self):
		listMissing = []
		
		for key in self.dbMovies:
			m = self.dbMovies[key]
			path = m.Path + u"/" + m.Filename + u"." + m.Extension
			if os.path.exists(Utf8.utf8ToLatin(path)) is False:
				listMissing.append(m)
		
		for key in self.dbSeries:
			if key in self.dbEpisodes:
				for season in self.dbEpisodes[key]:
					for episode in self.dbEpisodes[key][season]:
						m = self.dbEpisodes[key][season][episode]
						path = m.Path + u"/" + m.Filename + u"." + m.Extension
						if os.path.exists(Utf8.utf8ToLatin(path)) is False:
							listMissing.append(m)
		
		printl("Missing: " + str(len(listMissing)), self)
		for m in listMissing:
			self.remove(m)

	def searchDeleted(self):
		for key in self.dbMovies:
			m = self.dbMovies[key]
			path = m.Path + u"/" + m.Filename + u"." + m.Extension
			if os.path.exists(Utf8.utf8ToLatin(path)) is False:
				printl(":-( " + Utf8.utf8ToLatin(path), self)
		
		for key in self.dbSeries:
			if key in self.dbEpisodes:
				for season in self.dbEpisodes[key]:
					for episode in self.dbEpisodes[key][season]:
						m = self.dbEpisodes[key][season][episode]
						path = m.Path + u"/" + m.Filename + u"." + m.Extension
						if os.path.exists(Utf8.utf8ToLatin(path)) is False:
							printl(":-( " + Utf8.utf8ToLatin(path), self)

	##
	# Checks if file is already in the db
	# @param path: utf-8 
	# @param filename: utf-8 
	# @param extension: utf-8 
	# @return: True if already in db, False if not
	def checkDuplicate(self, path, filename, extension):
		for key in self.dbMovies:
			if self.dbMovies[key].Path == path:
				if self.dbMovies[key].Filename == filename:
					if self.dbMovies[key].Extension == extension:
						return True
		
		for key in self.dbSeries:
			if key in self.dbEpisodes:
				for season in self.dbEpisodes[key]:
					for episode in self.dbEpisodes[key][season]:
						if self.dbEpisodes[key][season][episode].Path == path:
							if self.dbEpisodes[key][season][episode].Filename == filename:
								if self.dbEpisodes[key][season][episode].Extension == extension:
									return True
		return False

	def remove(self, media, isMovie=False, isSerie=False, isEpisode=False):
		printl("isMovie=" + str(media.isMovie) + " isSerie=" + str(media.isSerie) + " isEpisode=" + str(media.isEpisode), self)
		if media.isMovie or isMovie:
			if self.dbMovies.has_key(media.ImdbId) is True:
				del(self.dbMovies[media.ImdbId])
				return True
		if media.isSerie or isSerie:
			if self.dbSeries.has_key(media.TheTvDbId) is True:
				del(self.dbSeries[media.TheTvDbId])
				return True
		if media.isEpisode or isEpisode:
			if self.dbEpisodes.has_key(media.TheTvDbId) is True:
				if self.dbEpisodes[media.TheTvDbId].has_key(media.Season) is True:
					if self.dbEpisodes[media.TheTvDbId][media.Season].has_key(media.Episode) is True:
						del(self.dbEpisodes[media.TheTvDbId][media.Season][media.Episode])
						if len(self.dbEpisodes[media.TheTvDbId][media.Season]) == 0:
							del(self.dbEpisodes[media.TheTvDbId][media.Season])
						if len(self.dbEpisodes[media.TheTvDbId]) == 0:
							del(self.dbEpisodes[media.TheTvDbId])
							if self.dbSeries.has_key(media.TheTvDbId) is True:
								del(self.dbSeries[media.TheTvDbId])
						return True
		return False

	_addFailedCauseOf = None

	def getAddFailedCauseOf(self):
		cause = self._addFailedCauseOf
		self._addFailedCauseOf = None
		return cause.Path + u"/" + cause.Filename + u"." + cause.Extension

	##
	# Adds media files to the db
	# @param media: The media file
	# @return: False if file is already in db or movie already in db, else True 
	def add(self, media):
		# Checks if a tvshow is already in the db, if so then we dont have to readd it a second time
		if media.isSerie:
			if self.dbSeries.has_key(media.TheTvDbId) is False:
				self.dbSeries[media.TheTvDbId] = media
				return True
			else:
				#self._addFailedCauseOf = self.dbSeries[media.TheTvDbId]
				#return False
				return True # We return true here cause this is not a failure but simply means that the tvshow already exists in the db
		
		media.Path = media.Path.replace("\\", "/")
		# Checks if the file is already in db
		if self.checkDuplicate(media.Path, media.Filename, media.Extension):
			# This should never happen, this means that the same file is already in the db
			# But is a failure describtion here necessary ?
			return False
		
		pth = media.Path + "/" + media.Filename + "." + media.Extension
		self.duplicateDetector.append(pth)
		
		if media.isMovie:
			if self.dbMovies.has_key(media.ImdbId) is False:
				self.dbMovies[media.ImdbId] = media
			else: 
				self._addFailedCauseOf = self.dbMovies[media.ImdbId]
				return False
		elif media.isEpisode:
			if self.dbEpisodes.has_key(media.TheTvDbId) is False:
				self.dbEpisodes[media.TheTvDbId] = {}
			
			if self.dbEpisodes[media.TheTvDbId].has_key(media.Season) is False:
				self.dbEpisodes[media.TheTvDbId][media.Season] = {}
			
			if self.dbEpisodes[media.TheTvDbId][media.Season].has_key(media.Episode) is False:
				self.dbEpisodes[media.TheTvDbId][media.Season][media.Episode] = media
			else:
				self._addFailedCauseOf = self.dbEpisodes[media.TheTvDbId][media.Season][media.Episode]
				return False
		return True

	def __str__(self):
		epcount = 0
		for key in self.dbSeries:
			if key in self.dbEpisodes:
				for season in self.dbEpisodes[key]:
					epcount +=  len(self.dbEpisodes[key][season])
		rtv = unicode(len(self.dbMovies)) + \
				u" " + \
				unicode(len(self.dbSeries)) + \
				u" " + \
				unicode(epcount)
		return Utf8.utf8ToLatin(rtv)

	FAILEDDB = "/hdd/valerie/failed.db"

	MOVIESDB = "/hdd/valerie/movies.db"
	TVSHOWSDB = "/hdd/valerie/tvshows.db"
	EPISODESDB = "/hdd/valerie/episodes.db"

	MOVIESTXD = "/hdd/valerie/movies.txd"
	TVSHOWSTXD = "/hdd/valerie/tvshows.txd"

	MOVIESTXT = "/hdd/valerie/moviedb.txt"
	TVSHOWSTXT = "/hdd/valerie/seriesdb.txt"
	
	DB_TXT = 1
	DB_TXD = 2
	DB_PICKLE = 3
	DB_SQLITE= 4
	USE_DB_VERSION = DB_TXD

	TXD_VERSION = 3

	def rmTxt(self):
		try:
			os.remove(self.MOVIESTXT)
		except Exception, ex:
			printl("Exception: " + str(ex), self)
		try:
			os.remove(self.TVSHOWSTXT)
		except Exception, ex:
			printl("Exception: " + str(ex), self)
			
		ds = DirectoryScanner.DirectoryScanner()
		ds.clear()
		ds.setDirectory("/hdd/valerie/episodes")
		filetypes = []
		filetypes.append("txt")
		ds.listDirectory(filetypes, None, 0)
		for ele in ds.getFileList():
			printl("TO BE DELETED: " + str(ele), self)

	def save(self):
		if self.USE_DB_VERSION == self.DB_TXT:
			self.saveTxt()
		elif self.USE_DB_VERSION == self.DB_TXD:
			self.saveTxd()
			self.rmTxt()
		
		# Always safe pickel as this increses fastsync a lot
		#elif self.USE_DB_VERSION == self.DB_PICKLE:
		self.savePickel()

	def saveTxt(self):
		start_time = time.time()	
		f = Utf8.Utf8(u"/hdd/valerie/moviedb.txt", 'w')
		f.write(unicode(date.today()))
		for key in self.dbMovies:
			f.write(self.dbMovies[key].export())
			self.dbMovies[key].setValerieInfoLastAccessTime(self.dbMovies[key].Path)
		f.close()
		elapsed_time = time.time() - start_time
		printl("Took (moviedb.txt): " + str(elapsed_time), self)
		
		start_time = time.time()	
		f = Utf8.Utf8(u"/hdd/valerie/seriesdb.txt", 'w')
		f.write(unicode(date.today()))
		for key in self.dbSeries:
			if self.dbEpisodes.has_key(key): # Check if we have episodes for that serie
				f.write(self.dbSeries[key].export())
		f.close()
		elapsed_time = time.time() - start_time
		printl("Took (seriesdb.txt): " + str(elapsed_time), self)
		
		start_time = time.time()  
		for serie in self.dbEpisodes:
			f = Utf8.Utf8(u"/hdd/valerie/episodes/" + serie + u".txt", 'w')
			f.write(unicode(date.today()))
			for season in self.dbEpisodes[serie]:
				for episode in self.dbEpisodes[serie][season]:
					f.write(self.dbEpisodes[serie][season][episode].export())
					self.dbEpisodes[serie][season][episode].setValerieInfoLastAccessTime(self.dbEpisodes[serie][season][episode].Path)
			f.close()
		elapsed_time = time.time() - start_time
		printl("Took (episodes/*.txt): " + str(elapsed_time), self)

	def saveTxd(self):
		start_time = time.time()	
		f = Utf8.Utf8(self.MOVIESTXD, 'w')
		f.write(unicode(self.TXD_VERSION) + u"\n")
		for movie in self.dbMovies.values():
			f.write(movie.exportDefined(self.TXD_VERSION))
		f.write("EOF\n")
		f.close()
		elapsed_time = time.time() - start_time
		printl("Took (movies.txd): " + str(elapsed_time), self)
		
		start_time = time.time()	
		f = Utf8.Utf8(self.TVSHOWSTXD, 'w')
		f.write(unicode(self.TXD_VERSION) + u"\n")
		for key in self.dbSeries:
			if self.dbEpisodes.has_key(key): # Check if we have episodes for that serie
				f.write(self.dbSeries[key].exportDefined(self.TXD_VERSION))
		f.write("EOF\n")
		f.close()
		elapsed_time = time.time() - start_time
		printl("Took (tvshows.txd): " + str(elapsed_time), self)
		
		start_time = time.time()  
		for serie in self.dbEpisodes:
			f = Utf8.Utf8(u"/hdd/valerie/episodes/" + serie + u".txd", 'w')
			f.write(unicode(self.TXD_VERSION) + u"\n")
			for season in self.dbEpisodes[serie]:
				for episode in self.dbEpisodes[serie][season].values():
					f.write(episode.exportDefined(self.TXD_VERSION))
			f.write("EOF\n")
			f.close()
		elapsed_time = time.time() - start_time
		printl("Took (episodes/*.txd): " + str(elapsed_time), self)

	def savePickel(self):
		start_time = time.time()  
		fd = open(self.FAILEDDB, "wb")
		pickle.dump(self.dbFailed, fd, pickle.HIGHEST_PROTOCOL)
		fd.close()
		elapsed_time = time.time() - start_time
		printl("Took (failed.db): " + str(elapsed_time), self)
		
		start_time = time.time()  
		fd = open(self.MOVIESDB, "wb")
		pickle.dump(self.dbMovies, fd, pickle.HIGHEST_PROTOCOL)
		fd.close()
		elapsed_time = time.time() - start_time
		printl("Took (movies.db): " + str(elapsed_time), self)
		
		
		#dbMovies2 = []
		#for movie in self.dbMovies.values():
		#	#print movie
		#	from struct.Media import MediaMovie
		#	m = MediaMovie()
		#	m.Path         = movie.Path
		#	m.Filename     = movie.Filename
		#	m.Extension    = movie.Extension
		#	m.Title        = movie.Title
		#	m.AiredYear    = movie.Year
		#	m.AiredMonth   = movie.Month
		#	m.AiredDay     = movie.Day
		#	m.CreatedYear  = 0
		#	m.CreatedMonth = 0
		#	m.CreatedDay   = 0
		#	m.Runtime      = movie.Runtime
		#	
		#	m.ImdbId       = movie.ImdbId
		#	m.TmDbId       = movie.TmDbId
		#	m.Tag          = movie.Tag
		#	m.Popularity   = movie.Popularity
		#	m.Resolution   = movie.Resolution
		#	m.Sound        = movie.Sound
		#	dbMovies2.append(m)
		#
		#start_time = time.time()  
		#fd = open(self.MOVIESDB+"2", "wb")
		#pickle.dump(dbMovies2, fd, pickle.HIGHEST_PROTOCOL)
		#fd.close()
		#elapsed_time = time.time() - start_time
		#printl("Took (movies.db): " + str(elapsed_time), self)
		
		start_time = time.time()  
		fd = open(self.TVSHOWSDB, "wb")
		pickle.dump(self.dbSeries, fd, pickle.HIGHEST_PROTOCOL)
		fd.close()
		elapsed_time = time.time() - start_time
		printl("Took (tvshows.db): " + str(elapsed_time), self)
		
		#start_time = time.time()
		#for serie in self.dbEpisodes:
		#	fd = open(u"/hdd/valerie/episodes/" + serie + u".db", "wb")
		#	pickle.dump(self.dbEpisodes[serie], fd, pickle.HIGHEST_PROTOCOL)
		#	fd.close()
		#elapsed_time = time.time() - start_time
		#print "Took (episodes/*.db): ", elapsed_time
		
		start_time = time.time()
		fd = open(self.EPISODESDB, "wb")
		pickle.dump(self.dbEpisodes, fd, pickle.HIGHEST_PROTOCOL)
		fd.close()
		elapsed_time = time.time() - start_time
		printl("Took (episodes.db): " + str(elapsed_time), self)

	def load(self):
		if os.path.isfile(self.FAILEDDB):
			fd = open(self.FAILEDDB, "rb")
			self.dbFailed = pickle.load(fd)
			fd.close()
		
		if os.path.isfile(self.MOVIESDB):
			self.loadPickle(True, False) 
		elif os.path.isfile(self.MOVIESTXD):
			self.loadTxd(True, False) 
		else:
			self.loadTxt(True, False)
		
		if os.path.isfile(self.TVSHOWSDB) and os.path.isfile(self.EPISODESDB):
			self.loadPickle(False, True) 
		elif os.path.isfile(self.TVSHOWSTXD):
			self.loadTxd(False, True) 
		else:
			self.loadTxt(False, True)
		
		# FIX: GHOSTFILES
		if self.dbEpisodes.has_key("0"):
			ghost = self.dbEpisodes["0"].values()
			for season in ghost:
				for episode in season.values():
					self.remove(episode)
			if self.dbEpisodes.has_key("0"):
				del self.dbEpisodes["0"]
		
		for tvshow in self.dbEpisodes.values():
			for season in tvshow.values():
				for episode in season.values():
					if episode.isEpisode is False:
						b = self.remove(episode, isEpisode=True)
						printl("RM: " + str(b), self)

	def loadTxt(self, loadMovie, loadTVShow):
		if loadMovie:
			start_time = time.time()
			try:
				db = Utf8.Utf8(u"/hdd/valerie/moviedb.txt", "r").read()
				if db is not None:
					movies = db.split("\n----END----\n")
					for movie in movies:
						movie = movie.split("---BEGIN---\n")
						if len(movie) == 2: 
							m = MediaInfo("","","")
							m.importStr(movie[1], True, False, False)
							path = m.Path + u"/" + m.Filename + u"." + m.Extension
							printl("Not found: " + Utf8.utf8ToLatin(path), self)
			except Exception, ex:
				print ex
				print '-'*60
				import sys, traceback
				traceback.print_exc(file=sys.stdout)
				print '-'*60
			
			elapsed_time = time.time() - start_time
			printl("Took (moviedb.txt): " + str(elapsed_time), self)
		
		if loadTVShow:
			start_time = time.time()
			try:
				db = Utf8.Utf8(u"/hdd/valerie/seriesdb.txt", "r").read()
				if db is not None:
					movies = db.split(u"\n----END----\n")
					for movie in movies:
						movie = movie.split(u"---BEGIN---\n")
						if len(movie) == 2: 
							m = MediaInfo("","","")
							m.importStr(movie[1], False, True, False)
							self.add(m)
			except Exception, ex:
				print ex
				print '-'*60
				import sys, traceback
				traceback.print_exc(file=sys.stdout)
				print '-'*60
			elapsed_time = time.time() - start_time
			printl("Took (seriesdb.txt): " + str(elapsed_time), self)
			
			start_time = time.time()
			try:	
				for key in self.dbSeries:
					db = Utf8.Utf8(u"/hdd/valerie/episodes/" + key + u".txt", "r").read()
					if db is not None:
						movies = db.split("\n----END----\n")
						for movie in movies:
							movie = movie.split("---BEGIN---\n")
							if len(movie) == 2: 
								m = MediaInfo("","","")
								m.importStr(movie[1], False, False, True)
								path = m.Path + u"/" + m.Filename + u"." + m.Extension
								if Config.getBoolean("delete") is False or os.path.isfile(Utf8.utf8ToLatin(path)):
									if m.isValerieInfoAvailable(m.Path):
										if m.getValerieInfoAccessTime(m.Path) == m.getValerieInfoLastAccessTime(m.Path):
											self.add(m)
									else:
										self.add(m)
								else:
									printl("Not found: " + Utf8.utf8ToLatin(path), self)
									printl(str(os.path.isfile(Utf8.utf8ToLatin(path))), self)
									printl(str(m.getValerieInfoAccessTime(m.Path)), self)
									printl(str(m.getValerieInfoLastAccessTime(m.Path)), self)
			except Exception, ex:
				print ex
				print '-'*60
				import sys, traceback
				traceback.print_exc(file=sys.stdout)
				print '-'*60
			elapsed_time = time.time() - start_time
			printl("Took (episodes/*.txt): " + str(elapsed_time), self)

	def loadTxd(self, loadMovie, loadTVShow):
		if loadMovie:
			start_time = time.time()
			try:
				db = Utf8.Utf8(self.MOVIESTXD, "r").read()
				if db is not None:
					lines = db.split("\n")
					version = lines[0]
					linesLen = len(lines)
					for i in range(1, linesLen, 11):
						if lines[i] == "EOF":
							break
						m = MediaInfo()
						m.importDefined(lines[i:i+11], True, False, False)
						self.add(m)
			except Exception, ex:
				print ex
				print '-'*60
				import sys, traceback
				traceback.print_exc(file=sys.stdout)
				print '-'*60
			
			elapsed_time = time.time() - start_time
			printl("Took (movies.txd): " + str(elapsed_time), self)
		
		if loadTVShow:
			start_time = time.time()
			try:
				db = Utf8.Utf8(self.TVSHOWSTXD, "r").read()
				if db is not None:
					lines = db.split("\n")
					version = lines[0]
					linesLen = len(lines)
					for i in range(1, linesLen, 9):
						if lines[i] == "EOF":
							break
						m = MediaInfo()
						m.importDefined(lines[i:i+9], False, True, False)
						self.add(m)
			except Exception, ex:
				print ex
				print '-'*60
				import sys, traceback
				traceback.print_exc(file=sys.stdout)
				print '-'*60
			
			elapsed_time = time.time() - start_time
			printl("Took (tvshows.txd): " + str(elapsed_time), self)
			
			start_time = time.time()
			try:	
				for key in self.dbSeries:
					db = Utf8.Utf8(u"/hdd/valerie/episodes/" + key + u".txd", "r").read()
					if db is not None:
						lines = db.split("\n")
						version = lines[0]
						linesLen = len(lines)
						for i in range(1, linesLen, 12):
							if lines[i] == "EOF":
								break
							m = MediaInfo()
							m.importDefined(lines[i:i+12], False, False, True)
							self.add(m)
			except Exception, ex:
				print ex
				print '-'*60
				import sys, traceback
				traceback.print_exc(file=sys.stdout)
				print '-'*60
			elapsed_time = time.time() - start_time
			printl("Took (episodes/*.txd): " + str(elapsed_time), self)

	def loadPickle(self, loadMovie, loadTVShow):
		if loadMovie:
			try:
				start_time = time.time()
				fd = open(self.MOVIESDB, "rb")
				self.dbMovies = pickle.load(fd)
				fd.close()
				elapsed_time = time.time() - start_time
				printl("Took (movies.db): " + str(elapsed_time), self)
			except Exception, ex:
				printl("Exception: " + str(ex), self)
		
		if loadTVShow:
			try:
				start_time = time.time()
				fd = open(self.TVSHOWSDB, "rb")
				self.dbSeries = pickle.load(fd)
				fd.close()
				elapsed_time = time.time() - start_time
				printl("Took (tvshows.db): " + str(elapsed_time), self)
			except Exception, ex:
				printl("Exception: " + str(ex), self)
			
			#start_time = time.time()
			#self.dbEpisodes = {}
			#for key in self.dbSeries:
			#	episode = {}
			#	fd = open(u"/hdd/valerie/episodes/" + key + u".db", "wb")
			#	self.dbEpisodes[key] = pickle.load(fd)
			#	fd.close()
			#elapsed_time = time.time() - start_time
			#print "Took (episodes/*.db): ", elapsed_time
			
			try:
				start_time = time.time()
				self.dbEpisodes = {}
				fd = open(self.EPISODESDB, "rb")
				self.dbEpisodes = pickle.load(fd)
				fd.close()
				elapsed_time = time.time() - start_time
				printl("Took (episodes.db): " + str(elapsed_time), self)
			except Exception, ex:
				printl("Exception: " + str(ex), self)
