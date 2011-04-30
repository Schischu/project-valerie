# -*- coding: utf-8 -*-

import gettext
import math
import os
from   os import environ

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import *
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, fileExists, pathExists, createDir, SCOPE_MEDIA, SCOPE_SKIN_IMAGE, SCOPE_PLUGINS, SCOPE_LANGUAGE

from DataElement import DataElement
from DMC_Global import Showiframe
from DMC_Player import PVMC_Player

from Plugins.Extensions.ProjectValerie.__common__ import printl2 as printl
from Plugins.Extensions.ProjectValerie.__plugin__ import getPlugins, Plugin, registerPlugin

#------------------------------------------------------------------------------------------

def localeInit():
	lang = language.getLanguage()
	environ["LANGUAGE"] = lang[:2]
	gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
	gettext.textdomain("enigma2")
	gettext.bindtextdomain("ProjectValerie", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/ProjectValerie/locale/"))

def _(txt):
	t = gettext.dgettext("ProjectValerie", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)
#------------------------------------------------------------------------------------------

class PVMC_Series(Screen, HelpableScreen):

	ShowStillPicture = False

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.showiframe = Showiframe()
		
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		
		self.APILevel = 1 
		try:
			self.APILevel = int(DataElement().getDataPreloading(self, "API"))
		except Exception, ex:
			printl(str(ex))
			self.APILevel = 1
		
		printl("APILevel=" + str(self.APILevel))
		
		if self.APILevel >= 2:
			self["API"] = DataElement()
		
		self.isVisible = True
		self.inSeries = True
		self.inSeasons = False
		self.inEpisode = False
		self.rememeberSeriesIndex = 0
		self.rememeberSeasonIndex = 0
		self.selectedSeries = 0
		self.serieslist = []
		self.seasonlist = []
		self.moviedb = {}
		self.episodesdb = {}
		
		list = []
		if self.APILevel == 1:
			self["listview"] = MenuList(list)
		elif self.APILevel >= 2:
			self["listview"] = List(list, True)
		self["poster"] 				= Pixmap()
		self["title"] 				= Label()
		if self.APILevel == 1:
			self["otitle"] 				= Label()
		self["tag"] 				= Label()
		self["shortDescription"] 	= Label()
		if self.APILevel == 1:
			self["director"] 			= Label()
			self["writer"] 				= Label()
		self["genre"] 				= Label()
		self["year"] 				= Label()
		self["runtime"] 			= Label()
		
		if self.APILevel >= 2:
			self["total"] = Label()
			self["current"] = Label()
		
		try:
			from StillPicture import StillPicture
			self["backdrop"] = StillPicture(session)
			self.ShowStillPicture = True
		except Exception, ex:
			printl("Exception: " + str(ex), self)
		
		if self.APILevel >= 2:
			self["listview_itemsperpage"] = DataElement()
		
		for i in range(10):
			stars = "star" + str(i)
			printl("stars: " + stars, self)
			self[stars] = Pixmap()
			if self[stars].instance is not None:
				self[stars].instance.hide()

		for i in range(10):
			stars = "nostar" + str(i)
			printl("stars: " + stars, self)
			self[stars] = Pixmap()
		
		self.backdropquality = ""
		if config.plugins.pvmc.backdropquality.value == "Low":
			self.backdropquality = "_low"
		
		if os.path.exists(u"/hdd/valerie/tvshows.txd"):
				self.USE_DB_VERSION = self.DB_TXD
		
		self["actions"] = HelpableActionMap(self, "PVMC_AudioPlayerActions", 
			{
				"ok": (self.KeyOk, "Play selected file"),
				"cancel": (self.KeyExit, "Exit Audio Player"),
				"left": (self.leftUp, "List Top"),
				"right": (self.rightDown, "List Bottom"),
				"up": (self.up, "List up"),
				"down": (self.down, "List down"),
				"up_quick": (self.up_quick, "List up"),
				"down_quick": (self.down_quick, "List down"),
				"up_first": (self.up_quick, "List up"),
				"down_first": (self.down_quick, "List down"),
				"info": (self.KeyInfo, "show Plot"),
				"menu": (self.KeyPlugins, "show Plugins"),
			}, -2)
		
		if self.USE_DB_VERSION == self.DB_TXT:
			self.loadSeriesDB()
		elif self.USE_DB_VERSION == self.DB_TXD:
			self.loadSeriesTxd()
		
		self.onLayoutFinish.append(self.setCustomTitle)
		self.onFirstExecBegin.append(self.refresh)

	def setCustomTitle(self):
		self.setTitle(_("tv shows"))

	DB_TXT = 1
	DB_TXD = 2
	DB_PICKLE = 3
	DB_SQLITE= 4
	USE_DB_VERSION = DB_TXT

	FAST_STILLPIC = False

	def loadSeriesTxd(self):
		list =[]
		entrys =[]
		try:
			if self.inSeries:
				self.serieslist = []
				db = open("/hdd/valerie/tvshows.txd").read()[:-1]
			elif self.inSeasons:
				self.seasonlist = []
				db = open("/hdd/valerie/episodes/" + self.selectedSeries + ".txd").read()[:-1]
			
			if not self.inEpisode:
				lines = db.split("\n")
				version = lines[0]
				linesLen = len(lines)
			
			if self.inSeries:
				#self.moviedb.clear()
				
				size = 9
				if int(version) >= 3:
					size = 11
				else:
					size = 9
				
				for i in range(1, linesLen, size):
					#print lines[i+0]
					if lines[i+0] == "EOF":
						break
					d = {} 
					if int(version) >=3:
						d["ImdbId"]     = lines[i+0]
						d["TheTvDb"]    = lines[i+1]
						d["Title"]      = lines[i+2]
						d["Tag"]        = lines[i+3]
						d["Year"]       = int(lines[i+4])
						d["Month"]      = int(lines[i+5])
						d["Day"]        = int(lines[i+6])
						d["Plot"]       = lines[i+7]
						d["Runtime"]    = lines[i+8]
						d["Popularity"] = lines[i+9]
						d["Genres"] = lines[i+10]
					else:
						d["ImdbId"]     = lines[i+0]
						d["TheTvDb"]    = lines[i+1]
						d["Title"]      = lines[i+2]
						d["Tag"]        = lines[i+3]
						d["Year"]       = int(lines[i+4])
						d["Plot"]       = lines[i+5]
						d["Runtime"]    = lines[i+6]
						d["Popularity"] = lines[i+7]
						d["Genres"]     = lines[i+8]
					
					# deprecated
					d["Directors"] = ""
					d["Writers"]   = ""
					d["OTitle"]    = ""
					
					self.moviedb[d["TheTvDb"]] = d
					if not d["Title"] in entrys:
						entrys.append(d["Title"])
						self.serieslist.append(("  " + d["Title"], d["TheTvDb"], "menu_globalsettings", "50"))
					
			elif self.inSeasons:
				self.episodesdb.clear()
				
				size = 12
				if int(version) >= 3:
					size = 14
				else:
					size = 12
				
				for i in range(1, linesLen, size):
					if lines[i+0] == "EOF":
						break
					d = {} 
					if int(version) >=3:
						d["TheTvDb"]    = lines[i+0]
						d["Title"]      = lines[i+1]
						d["Tag"]        = ""
						d["Year"]       = int(lines[i+2])
						d["Month"]      = int(lines[i+3])
						d["Day"]        = int(lines[i+4])
						d["Path"]       = lines[i+5] + "/" + lines[i+6] + "." + lines[i+7]
						d["Season"]     = int(lines[i+8])
						d["Episode"]    = int(lines[i+9])
						d["Plot"]       = lines[i+10]
						d["Runtime"]    = lines[i+11]
						d["Popularity"] = lines[i+12]
						d["Genres"]     = lines[i+13]
					else:
						d["TheTvDb"]    = lines[i+0]
						d["Title"]      = lines[i+1]
						d["Tag"]        = ""
						d["Year"]       = int(lines[i+2])
						d["Path"]       = lines[i+3] + "/" + lines[i+4] + "." + lines[i+5]
						d["Season"]     = int(lines[i+6])
						d["Episode"]    = int(lines[i+7])
						d["Plot"]       = lines[i+8]
						d["Runtime"]    = lines[i+9]
						d["Popularity"] = lines[i+10]
						d["Genres"]     = lines[i+11]
					
					# deprecated
					d["Directors"] = ""
					d["Writers"]   = ""
					d["OTitle"]    = ""
					
					if d["Season"] == -1:
						continue
					
					self.episodesdb[d["Season"] * 1000 + d["Episode"]] = d
					if not d["Season"] in entrys:
						entrys.append(d["Season"])
						self.seasonlist.append(("  " + "Season " + str(d["Season"]), d["Season"], "menu_globalsettings", "50"))
			else:
				for episode in self.episodesdb:
					d = self.episodesdb[episode]
					if d["Season"] == self.selectedSeason:
						if not d["Episode"] in entrys:
							entrys.append(d["Episode"])
							list.append(("  " + str(d["Season"])+"x"+("%02d" % d["Episode"]) + ": " + d["Title"], d["Season"] * 1000 + d["Episode"], "menu_globalsettings", "50"))
							
		except OSError, ex: 
			printl("OSError: " + str(ex), self)
		except IOError, ex: 
			printl("IOError: " + str(ex), self)
		
		if self.inSeries:
			self.serieslist.sort()
			self["listview"].setList(self.serieslist)
		elif self.inSeasons:
		#	self.seasonlist.sort()
			self.seasonlist.sort(key=lambda x: x[1])
			self["listview"].setList(self.seasonlist)
		elif self.inEpisode:
			#list.sort()
			list.sort(key=lambda x: x[1])
			self["listview"].setList(list)
		
		if self.APILevel >= 2:
			self["listview"].setIndex(0)
		self.refresh()

	def loadSeriesDB(self):
		list =[]
		filter = []
		entrys =[]
		if self.inSeries or self.inEpisode:
			filter.append("Tag")
			filter.append("Plot")
			filter.append("Directors")
			filter.append("Writers")
			filter.append("Genres")
			filter.append("Year")
			filter.append("Runtime")
			filter.append("Popularity")
			filter.append("ImdbId")
			filter.append("Title")
			filter.append("OTitle")
			filter.append("TheTvDb")
			filter.append("Path")
		if self.inSeasons or self.inEpisode:
			filter.append("Season")
			filter.append("Episode")
		
		try:
			if self.inSeries:
				self.serieslist = []
				db = open("/hdd/valerie/seriesdb.txt").read()[:-1]
			else:
				self.seasonlist = []
				db = open("/hdd/valerie/episodes/" + self.selectedSeries + ".txt").read()[:-1]
			
			movies = db.split("\n----END----\n")
			
			for movie in movies:
				movie = movie.split("---BEGIN---\n")
				if len(movie) == 2: 
					d = {} 
					lines = movie[1].split('\n')
					for line in lines: 
						#print "Line: ", line
						if ":" in line: 
							key, text = (s.strip() for s in line.split(":", 1)) 
						if key in filter: 
							d[key] = text
					
					if "Season" in d:
						d["Season"] = int(d["Season"])
					
					if "Episode" in d:
						d["Episode"] = int(d["Episode"])
					
					if "Year" in d:
						d["Year"] = int(d["Year"])
					
					#print d
					if self.inSeries:
						self.moviedb[d["TheTvDb"]] = d
						if not d["Title"] in entrys:
							entrys.append(d["Title"])
							self.serieslist.append(("  " + d["Title"], d["TheTvDb"], "menu_globalsettings", "50"))
					elif self.inSeasons:
						self.episodesdb[d["Season"] * 1000 + d["Episode"]] = d
						if not d["Season"] in entrys:
							entrys.append(d["Season"])
							list.append(("  " + "Season " + str(d["Season"]), str(d["Season"]), "menu_globalsettings", "50"))
					else:
						for episode in self.episodesdb:
							d = self.episodesdb[episode]
							if d["Season"] == self.selectedSeason:
								if not d["Episode"] in entrys:
									entrys.append(d["Episode"])
									self.seasonlist.append(("  " + str(d["Season"])+"x"+("%02d" % d["Episode"]) + ": " + d["Title"], d["Season"] * 1000 + d["Episode"], "menu_globalsettings", "50"))
		
		except OSError, ex:
			printl("OSError: " + str(ex), self)
		except IOError, ex:
			printl("IOError: " + str(ex), self)
		
		if self.inSeries:
			self.serieslist.sort()
			self["listview"].setList(self.serieslist)	
		elif self.inSeasons:
			self.seasonlist.sort()
			self["listview"].setList(self.seasonlist)
		elif self.inEpisode:
			list.sort()
			self["listview"].setList(list)
		
		if self.APILevel >= 2:
			self["listview"].setIndex(0)
		self.refresh()

	def setText(self, name, value, ignore=False, what=None):
		try:
			if self[name]:
				if len(value) > 0:
					self[name].setText(value)
				elif ignore is False:
					if what is None:
						self[name].setText(_("Not available"))
					else:
						self[name].setText(what + ' ' + _("not available"))
				else:
					self[name].setText(" ")
		except Exception, ex:
			printl("Exception: " + str(ex), self)

	def refresh(self, changeBackdrop=True):
		selection = self["listview"].getCurrent()
		if selection is not None and type(selection) != bool:
			if self.inSeries is True:
				if self.ShowStillPicture is True:
					if changeBackdrop is True:
						if os.access("/hdd/valerie/media/" + selection[1] + "_backdrop" + self.backdropquality + ".m1v", os.F_OK):
							self["backdrop"].setStillPicture("/hdd/valerie/media/" + selection[1] + "_backdrop" + self.backdropquality + ".m1v")
						elif os.access("/hdd/valerie/media/" + selection[1] + "_backdrop" + self.backdropquality + ".mvi", os.F_OK):
							self["backdrop"].setStillPicture("/hdd/valerie/media/" + selection[1] + "_backdrop" + self.backdropquality + ".mvi")
						else:
							self["backdrop"].setStillPictureToDefault()
				
				if self["poster"].instance is not None:
					if os.access("/hdd/valerie/media/" + selection[1] + "_poster.png", os.F_OK):
						self["poster"].instance.setPixmapFromFile("/hdd/valerie/media/" + selection[1] + "_poster.png")
					else:
						self["poster"].instance.setPixmapFromFile("/hdd/valerie/media/defaultposter.png")
				
				self.setText("title", selection[0])
				if self.APILevel == 1:
					self.setText("otitle", "---") #self.moviedb[selection[1]]["OTitle"])
				self.setText("tag", self.moviedb[selection[1]]["Tag"], True)
				
				self.setText("shortDescription", self.moviedb[selection[1]]["Plot"], what=_("Overview"))
				
				if self.APILevel == 1:
					if self.moviedb[selection[1]].has_key("Directors"):
						self.setText("director", self.moviedb[selection[1]]["Directors"])
					if self.moviedb[selection[1]].has_key("Writers"):
						self.setText("writer", self.moviedb[selection[1]]["Writers"])
				
				self.setText("genre", self.moviedb[selection[1]]["Genres"].replace('|', ", "), what=_("Genre"))
				#self.setText("year", str(self.moviedb[selection[1]]["Year"]))
				sele = self.moviedb[selection[1]]
				date = str(sele["Year"])
				if sele.has_key("Month") and sele.has_key("Day"):
					if sele["Month"] > 0 and sele["Day"] > 0:
						date = "%04d-%02d-%02d" % (sele["Year"], sele["Month"], sele["Day"], )
				self.setText("year", date)
				self.setText("runtime", self.moviedb[selection[1]]["Runtime"] + ' ' + _("min"))
				
				for i in range(int(self.moviedb[selection[1]]["Popularity"])):
					if self["star" + str(i)].instance is not None:
						self["star" + str(i)].instance.show()
				
				for i in range(10 - int(self.moviedb[selection[1]]["Popularity"])):
					if self["star" + str(9 - i)].instance is not None:
						self["star" + str(9 - i)].instance.hide()
			
			elif self.inEpisode is True:
				self.setText("title", selection[0])
				self.setText("shortDescription", self.episodesdb[selection[1]]["Plot"], what=_("Overview"))
				
				self.setText("genre", self.episodesdb[selection[1]]["Genres"].replace('|', ", "), what=_("Genre"))
				#self.setText("year", str(self.episodesdb[selection[1]]["Year"]))
				sele = self.episodesdb[selection[1]]
				date = str(sele["Year"])
				if sele.has_key("Month") and sele.has_key("Day"):
					if sele["Month"] > 0 and sele["Day"] > 0:
						date = "%04d-%02d-%02d" % (sele["Year"], sele["Month"], sele["Day"], )
				self.setText("year", date)
				self.setText("runtime", self.episodesdb[selection[1]]["Runtime"] + ' ' + _("min"))
			
			if self.APILevel >= 2:
				itemsPerPage = int(self["listview_itemsperpage"].getData())
				itemsTotal = self["listview"].count()
				#print "itemsPerPage", itemsPerPage
				pageTotal = int(math.ceil((itemsTotal / itemsPerPage) + 0.5))
				pageCurrent = int(math.ceil((self["listview"].getIndex() / itemsPerPage) + 0.5))
				if self.inSeries:
					self.setText("total", _("Total tv shows:") + ' ' + str(itemsTotal))
				elif self.inSeasons:
					self.setText("total", _("Total seasons:") + ' ' + str(itemsTotal))
				elif self.inEpisode:
					self.setText("total", _("Total episodes:") + ' ' + str(itemsTotal))
				self.setText("current", _("Pages:") + ' ' + str(pageCurrent) + "/" + str(pageTotal))

	def up(self):
		printl("", self)
		if self.FAST_STILLPIC is False:
			self.refresh()

	def up_first(self):
		printl("", self)
		if self.FAST_STILLPIC is False:
			self.refresh()

	def up_quick(self):
		printl("", self)
		if self.APILevel == 1:
			self["listview"].up()
		elif self.APILevel >= 2:
			self["listview"].selectPrevious()
		if self.FAST_STILLPIC is False:
			self.refresh(False)
		else:
			self.refresh()

	def down(self):
		printl("", self)
		if self.FAST_STILLPIC is False:
			self.refresh()

	def down_first(self):
		printl("", self)
		if self.FAST_STILLPIC is False:
			self.refresh()

	def down_quick(self):
		printl("", self)
		if self.APILevel == 1:
			self["listview"].down()
		elif self.APILevel >= 2:
			self["listview"].selectNext()
		if self.FAST_STILLPIC is False:
			self.refresh(False)
		else:
			self.refresh()

	def leftUp(self):
		printl("", self)
		if self.APILevel == 1:
			self["listview"].pageUp()
		elif self.APILevel >= 2:
			itemsPerPage = int(self["listview_itemsperpage"].getData())
			itemsTotal = self["listview"].count()
			index = self["listview"].getIndex() - itemsPerPage
			if index < 0:
				index = 0
			self["listview"].setIndex(index)
		self.refresh()

	def rightDown(self):
		printl("", self)
		if self.APILevel == 1:
			self["listview"].pageDown()
		elif self.APILevel >= 2:
			itemsPerPage = int(self["listview_itemsperpage"].getData())
			itemsTotal = self["listview"].count()
			index = self["listview"].getIndex() + itemsPerPage
			if index >= itemsTotal:
				index = itemsTotal - 1
			self["listview"].setIndex(index)
		self.refresh()

	def KeyOk(self):
		printl("", self)
		selection = self["listview"].getCurrent()
		if selection is not None:
			if self.inSeries is True:
				self.inSeries = False
				self.inSeasons = True
				self.inEpisode = False
				
				self.selectedSeries = selection[1]
				self.rememeberSeriesIndex = self["listview"].getIndex()
				
				seasonslist = []
				self.seasonsdb = {}
				
				
				if self.USE_DB_VERSION == self.DB_TXT:
					self.loadSeriesDB()
				elif self.USE_DB_VERSION == self.DB_TXD:
					self.loadSeriesTxd()
				
				self.refresh()
				
			elif self.inSeasons is True:
				self.inSeries = False
				self.inSeasons = False
				self.inEpisode = True
				
				self.selectedSeason = int(selection[1])
				self.rememeberSeasonIndex = self["listview"].getIndex()
				
				if self.USE_DB_VERSION == self.DB_TXT:
					self.loadSeriesDB()
				elif self.USE_DB_VERSION == self.DB_TXD:
					self.loadSeriesTxd()
				
				self.refresh()
			
			elif self.inEpisode is True:
				if self.isVisible == False:
					self.visibility()
					return
				
				selection = self["listview"].getCurrent()
				if selection is not None:
					playbackPath = self.episodesdb[selection[1]]["Path"]
					if os.path.isfile(playbackPath):
						self.showiframe.finishStillPicture()
						
						self.currentSeasonNumber = self.episodesdb[selection[1]]["Season"]
						self.currentEpisodeNumber = self.episodesdb[selection[1]]["Episode"]
						
						args = {}
						args["title"]   = self.moviedb[self.episodesdb[selection[1]]["TheTvDb"]]["Title"]
						args["year"]    = self.moviedb[self.episodesdb[selection[1]]["TheTvDb"]]["Year"]
						args["thetvdb"] = self.episodesdb[selection[1]]["TheTvDb"]
						args["season"]  = self.currentSeasonNumber
						args["episode"] = self.currentEpisodeNumber
						args["status"]  = "playing"
						args["type"]    = "tvshow"
						plugins = getPlugins(where=Plugin.INFO_PLAYBACK)
						for plugin in plugins:
							print plugin.name
							plugin.fnc(args)
						
						isDVD = False
						dvdFilelist = [ ]
						dvdDevice = None
						
						if self.episodesdb[selection[1]]["Path"].lower().endswith(u"ifo"): # DVD
							isDVD = True
							dvdFilelist.append(str(self.episodesdb[selection[1]]["Path"].replace(u"/VIDEO_TS.IFO", "").strip()))
						elif self.episodesdb[selection[1]]["Path"].lower().endswith(u"iso"): # DVD
							isDVD = True
							dvdFilelist.append(self.episodesdb[selection[1]]["Path"])
						
						if isDVD:
							try:
								from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
								# when iso -> filelist, when folder -> device
								self.session.openWithCallback(self.leaveMoviePlayer, DVDPlayer, dvd_device = dvdDevice, dvd_filelist = dvdFilelist)
							except Exception, ex:
								printl("Exception: " + str(ex), self)
						else:
							playbackList = []
							i = 0
							while True:
								key = self.currentSeasonNumber *1000 + self.currentEpisodeNumber + i
								if key in self.episodesdb:
									d = self.episodesdb[key]
									playbackList.append( (self.episodesdb[key]["Path"], str(d["Season"])+"x"+("%02d" % d["Episode"]) + ": " + self.episodesdb[key]["Title"]), )
									i = i + 1
								else:
									break
							
							printl("playbackList: " + str(playbackList), self)
							
							self.session.openWithCallback(self.leaveMoviePlayer, PVMC_Player, playbackList, self.notifyNextEntry)
					else:
						self.session.open(MessageBox, _("Not found!\n") + self.episodesdb[selection[1]]["Path"] + _("\n\nPlease make sure that your drive is connected/mounted."), type = MessageBox.TYPE_ERROR)

	def notifyNextEntry(self):
		printl("", self)
		args = {}
		args["status"] = "stopped"
		plugins = getPlugins(where=Plugin.INFO_PLAYBACK)
		for plugin in plugins:
			plugin.fnc(args) 
		
		self.currentEpisodeNumber = str(int(self.currentEpisodeNumber) + 1)
		
		argsNE = {}
		argsNE["season"]  = self.currentSeasonNumber
		argsNE["episode"] = self.currentEpisodeNumber
		argsNE["status"]  = "playing"
		plugins = getPlugins(where=Plugin.INFO_PLAYBACK)
		for plugin in plugins:
			plugin.fnc(argsNE) 

	def leaveMoviePlayer(self): 
		args = {}
		args["status"] = "stopped"
		plugins = getPlugins(where=Plugin.INFO_PLAYBACK)
		for plugin in plugins:
			plugin.fnc(args) 
		
		self.session.nav.playService(None) 
		self.refresh()

	def KeyExit(self):
		if self.inSeries is True:
			if self.isVisible == False:
				self.visibility()
				return
			
			self.showiframe.finishStillPicture()
			self.close()
		elif self.inEpisode is True:
			self.inSeries  = False
			self.inSeasons = True
			self.inEpisode = False
			self["listview"].setList(self.seasonlist)
			self["listview"].setIndex(self.rememeberSeasonIndex)
			self.setText("title", self.serieslist[self.rememeberSeriesIndex][0])
			self.refresh()
		elif self.inSeasons is True:
			self.inSeries  = True
			self.inSeasons = False
			self.inEpisode = False
			self["listview"].setList(self.serieslist)
			self["listview"].setIndex(self.rememeberSeriesIndex)
			self.refresh()

	def KeyInfo(self):
		selection = self["listview"].getCurrent()
		if self.inEpisode is True:
			self.session.open(MessageBox, _("Title:\n") + self.episodesdb[selection[1]]["Title"] + _("\n\nPlot:\n") + self.episodesdb[selection[1]]["Plot"], type = MessageBox.TYPE_INFO)
		elif self.inSeries is True:
			if selection is not None:
				self.session.open(MessageBox, _("Title:\n") + self.moviedb[selection[1]]["Title"] + _("\n\nPlot:\n") + self.moviedb[selection[1]]["Plot"], type = MessageBox.TYPE_INFO)

	def KeyPlugins(self):
		if self.inEpisode is False:
			return
		
		pluginList = []
		plugins = getPlugins(where=Plugin.MENU_MOVIES_PLUGINS)
		for plugin in plugins:
			pluginList.append((plugin.name, plugin.start, ))
		
		if len(pluginList) == 0:
			pluginList.append((_("No plugins available"), None, ))
		
		self.session.openWithCallback(self.KeyPluginsConfirmed, ChoiceBox, title=_("Plugins available"), list=pluginList)

	def KeyPluginsConfirmed(self, choice):
		if choice is None or choice[1] is None:
			return
		
		selection = self["listview"].getCurrent()
		if selection is not None and type(selection) != bool:
			episode = self.episodesdb[selection[1]]
			episode["Title"] = self.moviedb[episode["TheTvDb"]]["Title"]
			self.session.open(choice[1], episode)

registerPlugin(Plugin(name=_("TV Shows"), start=PVMC_Series, where=Plugin.MENU_VIDEOS))
