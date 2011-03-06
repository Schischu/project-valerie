from enigma import eTimer, eWidget, eRect, eServiceReference, iServiceInformation, iPlayableService, ePicLoad
from Screens.Screen import Screen
from Screens.ServiceInfo import ServiceInfoList, ServiceInfoListEntry
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.Pixmap import Pixmap, MovingPixmap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.Sources.StaticText import StaticText

from Components.Sources.List import List
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen

from Components.ServicePosition import ServicePositionGauge
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase

from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import *

from Tools.Directories import resolveFilename, fileExists, pathExists, createDir, SCOPE_MEDIA, SCOPE_SKIN_IMAGE, SCOPE_PLUGINS, SCOPE_LANGUAGE
from Components.FileList import FileList
from Components.AVSwitch import AVSwitch
from Screens.InfoBar import MoviePlayer

from Plugins.Plugin import PluginDescriptor

#from enigma import eStillPicture
from Components.MenuList import MenuList

import os
from os import path as os_path

from DMC_Global import printl

def getAspect():
	val = AVSwitch().getAspectRatioSetting()
	return val/2

from DMC_Global import Showiframe
from DMC_Player import PVMC_Player 
from DataElement import DataElement
import math

from TraktAPI import TraktAPI 

from os import environ
import gettext
from Components.Language import language

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

class PVMC_Movies(Screen, HelpableScreen, InfoBarBase):

	ShowStillPicture = False

	def __init__(self, session):
		Screen.__init__(self, session)
		InfoBarBase.__init__(self)
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
		self.moviedb = {}
		self.genreFilter = ""
		self.Sort = ""
		
		list = []
		
		if self.APILevel == 1:
			self["listview"] = MenuList(list)
		elif self.APILevel >= 2:
			self["listview"] = List(list, True)
		self["title"] = Label()
		if self.APILevel == 1:
			self["otitle"] = Label()
		self["tag"] = Label()
		self["poster"] = Pixmap()
		self["shortDescription"] = Label()
		if self.APILevel == 1:
			self["director"] = Label()
			self["writer"] = Label()
		self["genre"] = Label()
		self["year"] = Label()
		self["runtime"] = Label()
		
		if self.APILevel >= 2:
			self["total"] = Label()
			self["current"] = Label()
		
		self["key_red"] = StaticText(_("Sort"))
		self["key_blue"] = StaticText(_("Categories"))
		
		try:
			from StillPicture import StillPicture
			self["backdrop"] = StillPicture(session)
			self.ShowStillPicture = True
		except Exception, ex:
			print ex
		
		if self.APILevel >= 2:
			self["listview_itemsperpage"] = DataElement()
		
		for i in range(10):
			stars = "star" + str(i)
			print stars
			self[stars] = Pixmap()
			if self[stars].instance is not None:
				self[stars].instance.hide()

		for i in range(10):
			stars = "nostar" + str(i)
			print stars
			self[stars] = Pixmap()
		
		self.backdropquality = ""
		if config.plugins.pvmc.backdropquality.value == "Low":
			self.backdropquality = "_low"
		
		if os.path.exists(u"/hdd/valerie/movies.txd"):
				self.USE_DB_VERSION = self.DB_TXD
		
		self["actions"] = HelpableActionMap(self, "PVMC_AudioPlayerActions", 
			{
				"ok": (self.KeyOk, "Play selected file"),
				"cancel": (self.Exit, "Exit Audio Player"),
				"left": (self.leftUp, "List Top"),
				"right": (self.rightDown, "List Bottom"),
				"up": (self.up, "List up"),
				"down": (self.down, "List down"),
				"up_quick": (self.up_quick, "List up"),
				"down_quick": (self.down_quick, "List down"),
				"blue": (self.KeyGenres, _("Categories")),
				"red": (self.KeySort, _("Sort")),
				"stop": (self.leaveMoviePlayer, "Stop Playback"),
				"info": (self.KeyInfo, "show Plot"),
			}, -2)
		
		self.loadMovies()
		
		print "TRAKT.TV: ", config.plugins.pvmc.trakt.value
		if config.plugins.pvmc.trakt.value is True:
			self.trakt = TraktAPI("pvmc")
			self.trakt.setUsernameAndPassword(config.plugins.pvmc.traktuser.value, config.plugins.pvmc.traktpass.value)
			self.trakt.setType(TraktAPI.TYPE_MOVIE)
		
		self.onLayoutFinish.append(self.setCustomTitle)
		self.onFirstExecBegin.append(self.refresh)

	def setCustomTitle(self):
		self.setTitle(_("movies"))

	DB_TXT = 1
	DB_TXD = 2
	DB_PICKLE = 3
	DB_SQLITE= 4
	USE_DB_VERSION = DB_TXT

	FAST_STILLPIC = False

	def sortList(self,x, y):
		if self.moviedb[x[1]][self.Sort]>self.moviedb[y[1]][self.Sort]:
			return 1
		elif self.moviedb[x[1]][self.Sort]==self.moviedb[y[1]][self.Sort]:
			return 0
		else: # x<y
			return -1

	def loadMovies(self):
		if self.USE_DB_VERSION == self.DB_TXT:
			self.loadMoviesDB()
		elif self.USE_DB_VERSION == self.DB_TXD:
			self.loadMoviesTxd()

	def loadMoviesTxd(self):
		list =[]
		try:
			self.serieslist=[]
			db = open("/hdd/valerie/movies.txd").read()[:-1]
			
			lines = db.split("\n")
			version = lines[0]
			linesLen = len(lines)
			print "Lines:", linesLen
			
			size = 11
			if int(version) >= 3:
				size = 13
			else:
				size = 11
			
			for i in range(1, linesLen, size):
				if lines[i+0] == "EOF":
					break
				d = {} 
				if int(version) >=3:
					d["ImdbId"]     = lines[i+0]
					d["Title"]      = lines[i+1]
					d["Tag"]        = lines[i+2]
					d["Year"]       = int(lines[i+3])
					d["Month"]      = int(lines[i+4])
					d["Day"]        = int(lines[i+5])
					d["Path"]       = lines[i+6] + "/" + lines[i+7] + "." + lines[i+8]
					d["Plot"]       = lines[i+9]
					d["Runtime"]    = lines[i+10]
					d["Popularity"] = lines[i+11]
					d["Genres"]     = lines[i+12]
				else:
					d["ImdbId"]    = lines[i+0]
					d["Title"]     = lines[i+1]
					d["Tag"]       = lines[i+2]
					d["Year"]      = int(lines[i+3])
					d["Path"] = lines[i+4] + "/" + lines[i+5] + "." + lines[i+6]
					d["Plot"]       = lines[i+7]
					d["Runtime"]    = lines[i+8]
					d["Popularity"] = lines[i+9]
					d["Genres"] = lines[i+10]
				
				try:
					d["Creation"] = os.stat(d["Path"]).st_mtime
				except:
					d["Creation"] = 0
				
				# deprecated
				d["Directors"] = ""
				d["Writers"]   = ""
				d["OTitle"]    = ""
				
				if self.genreFilter != "" and d["Genres"] != "" and not self.genreFilter in d["Genres"]:
					print "skipping ", d["Title"]
					continue
				self.moviedb[d["ImdbId"]] = d
				
				print "adding ", d["Title"]
				list.append(("  " + d["Title"], d["ImdbId"], "menu_globalsettings", "45"))
		
		except OSError, e: 
			print "OSError: ", e
		except IOError, e: 
			print "OSError: ", e
		
		if self.Sort == "":
			list.sort()
		else:
			list.sort(self.sortList,reverse=True)
		self["listview"].setList(list)
		if self.APILevel >= 2:
			self["listview"].setIndex(0)
		self.refresh()

	def loadMoviesDB(self):
		filter = []
		list = []
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
		filter.append("Path")
		
		try:
			db = open("/hdd/valerie/moviedb.txt").read()[:-1]
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
					
					try:
						d["Creation"] = os.stat(d["Path"]).st_mtime
					except:
						d["Creation"] = 0
					
					#print d
					if self.genreFilter != "" and d["Genres"] != "" and not self.genreFilter in d["Genres"]:
						print "skipping ", d["Title"]
						continue
					self.moviedb[d["ImdbId"]] = d
					
					print "adding ", d["Title"]
					list.append(("  " + d["Title"], d["ImdbId"], "menu_globalsettings", "45"))
		
		except OSError, e: 
			print "OSError: ", e
		except IOError, e: 
			print "OSError: ", e
		
		if self.Sort == "":
			list.sort()
		else:
			list.sort(self.sortList, reverse=True)
		self["listview"].setList(list)
		if self.APILevel >= 2:
			self["listview"].setIndex(0)
		self.refresh()

	def getAvailGenres(self):
		list = []
		for movie in self.moviedb.values():
			genres = movie["Genres"]
			for genre in genres.split("|"):
				if len(genre) > 0 and (_(genre), genre) not in list:
					list.append((_(genre), genre))
		
		list.sort()
		list.insert(0,(_("All"), "all"))
		return list

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
			print "setText::", ex

	def refresh(self, changeBackdrop=True):
		selection = self["listview"].getCurrent()
		print "SELECTION", selection
		if selection is not None and type(selection) != bool:
			if changeBackdrop is True:
				if self.ShowStillPicture is True:
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
				self.setText("otitle", "---")
			
			self.setText("tag", self.moviedb[selection[1]]["Tag"], True)
			self.setText("shortDescription", self.moviedb[selection[1]]["Plot"], what=_("Overview"))
			
			if self.APILevel == 1:
				if self.moviedb[selection[1]].has_key("Directors"):
					self.setText("director", self.moviedb[selection[1]]["Directors"])
				if self.moviedb[selection[1]].has_key("Writers"):
					self.setText("writer", self.moviedb[selection[1]]["Writers"])
			
			self.setText("genre", self.moviedb[selection[1]]["Genres"].replace('|', ", "), what=_("Genre"))
			sele = self.moviedb[selection[1]]
			date = str(sele["Year"])
			if sele.has_key("Month") and sele.has_key("Day"):
				if sele["Month"] > 0 and sele["Day"] > 0:
					date = "%04d-%02d-%02d" % (sele["Year"], sele["Month"], sele["Day"], )
			self.setText("year", date)
			self.setText("runtime", self.moviedb[selection[1]]["Runtime"] + ' ' + _("min"))
			
			if self.APILevel >= 2:
				itemsPerPage = int(self["listview_itemsperpage"].getData())
				itemsTotal = self["listview"].count()
				#print "itemsPerPage", itemsPerPage
				pageTotal = int(math.ceil((itemsTotal / itemsPerPage) + 0.5))
				pageCurrent = int(math.ceil((self["listview"].getIndex() / itemsPerPage) + 0.5))
				self.setText("total", _("Total movies:") + ' ' + str(itemsTotal))
				self.setText("current", _("Pages:") + ' ' + str(pageCurrent) + "/" + str(pageTotal))
			
			for i in range(int(self.moviedb[selection[1]]["Popularity"])):
				if self["star" + str(i)].instance is not None:
					self["star" + str(i)].instance.show()
			
			for i in range(10 - int(self.moviedb[selection[1]]["Popularity"])):
				if self["star" + str(9 - i)].instance is not None:
					self["star" + str(9 - i)].instance.hide()

	def up(self):
		print "PVMC_Movies::up"
		if self.FAST_STILLPIC is False:
			self.refresh()

	def up_first(self):
		print "PVMC_Movies::up_first"
		if self.FAST_STILLPIC is False:
			self.refresh()

	def up_quick(self):
		print "PVMC_Movies::up_quick"
		if self.APILevel == 1:
			self["listview"].up()
		elif self.APILevel >= 2:
			self["listview"].selectPrevious()
		if self.FAST_STILLPIC is False:
			self.refresh(False)
		else:
			self.refresh()

	def down(self):
		print "PVMC_Movies::down"
		if self.FAST_STILLPIC is False:
			self.refresh()

	def down_first(self):
		print "PVMC_Movies::down_first"
		if self.FAST_STILLPIC is False:
			self.refresh()

	def down_quick(self):
		print "PVMC_Movies::down_quick"
		if self.APILevel == 1:
			self["listview"].down()
		elif self.APILevel >= 2:
			self["listview"].selectNext()
		if self.FAST_STILLPIC is False:
			self.refresh(False)
		else:
			self.refresh()

	def leftUp(self):
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
		if self.isVisible == False:
			self.visibility()
			return
		
		selection = self["listview"].getCurrent()
		if selection is not None:
			playbackPath = self.moviedb[selection[1]]["Path"]
			if os.path.isfile(playbackPath):
				self.showiframe.finishStillPicture()
				
				if config.plugins.pvmc.trakt.value is True:
					self.trakt.setName(self.moviedb[selection[1]]["Title"])
					self.trakt.setYear(self.moviedb[selection[1]]["Year"])
					self.trakt.setStatus(TraktAPI.STATUS_WATCHING)
					self.trakt.setImdbId(self.moviedb[selection[1]]["ImdbId"])
					self.trakt.setProgress(1)
					self.trakt.setDuration(90)
					self.trakt.send()
				
				isDVD = False
				dvdFilelist = [ ]
				dvdDevice = None
				
				if self.moviedb[selection[1]]["Path"].lower().endswith(u"ifo"): # DVD
					isDVD = True
					dvdFilelist.append(str(self.moviedb[selection[1]]["Path"].replace(u"/VIDEO_TS.IFO", "").strip()))
				elif self.moviedb[selection[1]]["Path"].lower().endswith(u"iso"): # DVD
					isDVD = True
					dvdFilelist.append(self.moviedb[selection[1]]["Path"])
				
				if isDVD:
					try:
						from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
						# when iso -> filelist, when folder -> device
						self.session.openWithCallback(self.leaveMoviePlayer, DVDPlayer, dvd_device = dvdDevice, dvd_filelist = dvdFilelist)
					except Exception, ex:
						print "KeyOk::", ex
				else:
					playbackList = []
					playbackList.append( (self.moviedb[selection[1]]["Path"], self.moviedb[selection[1]]["Title"]), )
					
					print "PLAYBACK: ", playbackList
					
					self.session.openWithCallback(self.leaveMoviePlayer, PVMC_Player, playbackList)
			else:
				self.session.open(MessageBox, "Not found!\n" + self.moviedb[selection[1]]["Path"] + "\n\nPlease make sure that your drive is connected/mounted.", type = MessageBox.TYPE_ERROR)
		

	def leaveMoviePlayer(self): 
		if config.plugins.pvmc.trakt.value is True:
			self.trakt.setStatus(TraktAPI.STATUS_WATCHED)
			self.trakt.send()
		self.session.nav.playService(None) 
		self.refresh()
		#selection = self["listview"].getCurrent()
		#if selection is not None:
		#	if os.access("/hdd/valerie/media/tt" + selection[1] + "_backdrop" + self.backdropquality + ".m1v", os.F_OK):
		#		self.showiframe.showStillpicture("/hdd/valerie/media/tt" + selection[1] + "_backdrop" + self.backdropquality + ".m1v")
		#	else:
		#		self.showiframe.showStillpicture("/hdd/valerie/media/defaultbackdrop.m1v")

	def KeyGenres(self):
		menu = self.getAvailGenres()
		self.session.openWithCallback(self.genresCallback, ChoiceBox, title=_("Select Category"), list = menu)

	def genresCallback(self, choice):
		if choice is None:
			return
		
		if choice[1] == "all":
			self.genreFilter = ""
		else:
			self.genreFilter = choice[1]
		self.loadMovies()

	def KeySort(self):
		menu = []
		menu.append((_("Title"), "Title"))
		menu.append((_("Aired"), "Year"))
		menu.append((_("Creation"), "Creation"))
		menu.append((_("Popularity"), "Popularity"))
		self.session.openWithCallback(self.sortCallback, ChoiceBox, title=_("Sort by"), list=menu)

	def sortCallback(self, choice):
		if choice is None:
			return

		if choice[1] == "Title":
			self.Sort = ""
		else:
			self.Sort = choice[1]
		self.loadMovies()

	def Exit(self):
		if self.isVisible == False:
			self.visibility()
			return
		
#		finishStillPicture()
		self.showiframe.finishStillPicture()
		
		self.close()

	#class PVMC_MessageBoxInfo(MessageBox):
	#	def __init__(self, session, title, plot):
	#		text = _("Title:\n") + title + _("\n\nPlot:\n") + plot
	#		MessageBox.__init__(self, session, text, type = MessageBox.TYPE_INFO)

	def KeyInfo(self):
		selection = self["listview"].getCurrent()
		if selection is not None:
			#self.session.open(self.PVMC_MessageBoxInfo, self.moviedb[selection[1]]["Title"], self.moviedb[selection[1]]["Plot"])
			self.session.open(MessageBox, _("Title:\n") + self.moviedb[selection[1]]["Title"] + _("\n\nPlot:\n") + self.moviedb[selection[1]]["Plot"], type = MessageBox.TYPE_INFO)

from Plugins.Extensions.ProjectValerie.__plugin__ import Plugin, registerPlugin
registerPlugin(Plugin(name=_("Movies"), start=PVMC_Movies, where=Plugin.MENU_VIDEOS))
