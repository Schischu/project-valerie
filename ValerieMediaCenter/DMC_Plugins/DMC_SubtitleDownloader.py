# -*- coding: utf-8 -*-

import sys

from Components.config import config
from Screens.ChoiceBox import ChoiceBox

from Plugins.Extensions.ProjectValerie.__common__ import printl2 as printl
from Plugins.Extensions.ProjectValerie.__plugin__ import Plugin, registerPlugin

#------------------------------------------------------------------------------------------

gAvailable = False
try:
	from Plugins.Extensions.ProjectValerieSync.Utf8 import *
	sys.path.append(config.plugins.pvmc.pluginfolderpath.value + "DMC_Plugins/DMC_SubtitleDownloaderExtras")
	gAvailable = True
except:
	printl("Is not available", "DMC_SubtitleDownloader")
	gAvailable = False

class DMC_SubtitleDownloader(ChoiceBox):
	service = "OpenSubtitles"

	def __init__(self, session, args):
		self.session = session
		
		year = args["Year"]
		title = args["Title"]
		if args.has_key("Season"):
			season = args["Season"]
			episode = args["Episode"]
			tvshow = self.title
		else:
			season = ""
			episode = ""
			tvshow = ""
		
		
		self.language_1 = "English"
		self.language_2 = "German"
		self.language_3 = "None"
		
		file_original_path = args["Path"]
		set_temp = False
		rar = False
		
		exec ( "from DMC_SubtitleDownloaderExtras.services.%s import service as Service" % (self.service))
		print "searching sub for", file_original_path
		self.subtitles_list, self.session_id, msg = Service.search_subtitles( file_original_path, title, tvshow, year, season, episode, set_temp, rar, self.language_1, self.language_2, self.language_3 )
		
		
		subtitleList = []
		for subtitle in self.subtitles_list:
			subtitleList.append((utf8ToLatin(subtitle["filename"]), subtitle, ))
		
		ChoiceBox.__init__(self, self.session, list = subtitleList, title = file_original_path)

gsubdown = None

def autostart(session):
	global gsubdown

if gAvailable is True:
	printl("Is available", __name__)
	#registerPlugin(Plugin(name=_("trakt.tv"), fnc=settings, where=Plugin.SETTINGS))
	registerPlugin(Plugin(name=_("SubtitleDownloader"), fnc=autostart, where=Plugin.AUTOSTART))
	registerPlugin(Plugin(name=_("SubtitleDownloader"), start=DMC_SubtitleDownloader, where=Plugin.MENU_MOVIES_PLUGINS))