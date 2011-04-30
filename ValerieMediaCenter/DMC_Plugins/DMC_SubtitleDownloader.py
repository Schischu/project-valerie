# -*- coding: utf-8 -*-


import os
import shutil
import sys



from Components.config import config
from Screens.ChoiceBox import ChoiceBox

from DMC_SubtitleDownloaderExtras.utilities import *

from Plugins.Extensions.ProjectValerie.__common__ import printl2 as printl
from Plugins.Extensions.ProjectValerie.__plugin__ import Plugin, registerPlugin

have_unzip = False
try:
	import unzip
	have_unzip = True
except:
	have_unzip = False

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
		
		self.file_original_path = args["Path"]
		set_temp = False
		rar = False
		
		self.tmp_sub_dir = "/tmp/subdir"
		try:
			os.removedirs(str(self.tmp_sub_dir))
		except:
			pass
		os.mkdir(str(self.tmp_sub_dir))
		self.sub_folder = self.file_original_path.rsplit("/", 1)[0]
		
		exec ( "from DMC_SubtitleDownloaderExtras.services.%s import service as Service" % (self.service))
		self.Service = Service
		print "searching sub for", self.file_original_path
		self.subtitles_list, self.session_id, msg = self.Service.search_subtitles( self.file_original_path, title, tvshow, year, season, episode, set_temp, rar, self.language_1, self.language_2, self.language_3 )
		
		
		subtitleList = []
		for subtitle in self.subtitles_list:
			subtitleList.append((utf8ToLatin(subtitle["filename"]), "CALLFUNC", self.Download_Subtitles, subtitle))
		
		ChoiceBox.__init__(self, self.session, list = subtitleList, title = self.file_original_path)

	def Download_Subtitles(self, subtitle):
		print "subtitle", subtitle[3]
		fakeSubtitleList = []
		fakeSubtitleList.append(subtitle[3])
		zip_subs = os.path.join( self.tmp_sub_dir, "zipsubs.zip")
		zipped, language, file = self.Service.download_subtitles(fakeSubtitleList, 0, zip_subs, self.tmp_sub_dir, self.sub_folder,self.session_id)
		sub_lang = str(toOpenSubtitles_two(language))
		print "zipped", zipped
		print "language", language
		print "file", file
		
		if zipped :
			self.Extract_Subtitles(zip_subs, sub_lang)
		else:
			sub_ext  = os.path.splitext( file )[1]
			sub_name = os.path.splitext( os.path.basename( self.file_original_path ) )[0]
			#if (__settings__.getSetting( "lang_to_end" ) == "true"):
			file_name = "%s.%s%s" % ( sub_name, sub_lang, sub_ext )
			#else:
			#	file_name = "%s%s" % ( sub_name, sub_ext )
			file_from = file.replace('\\','/')
			file_to = os.path.join(self.sub_folder, file_name).replace('\\','/')
			try:
				print "c", file_from, file_to
				shutil.copyfile(file_from, file_to)
			except IOError, e:
				print e
		#xbmc.Player().setSubtitles(file_to)
		try:
			os.removedirs(str(self.tmp_sub_dir))
		except:
			pass
		self.close()

	def Extract_Subtitles( self, zip_subs, subtitle_lang ):
		if have_unzip:
			un = unzip.unzip()
			files = un.get_file_list( zip_subs )
		sub_filename = os.path.basename( self.file_original_path )
		exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass" ]
		if have_unzip and len(files) < 1 :
			print "len(files) < 1"
		else :
			if have_unzip:
				un.extract( zip_subs, self.tmp_sub_dir )
			else:
				print "unzip " + str(zip_subs) + " -d " + str(self.tmp_sub_dir)
				os.system("unzip " + str(zip_subs) + " -d " + str(self.tmp_sub_dir))
				files = os.listdir(str(self.tmp_sub_dir))
			subtitle_set = False
			movie_sub = False
			episode = 0
			for zip_entry in files:
				if os.path.splitext( zip_entry )[1] in exts:
					subtitle_file, file_path = self.create_name(zip_entry,sub_filename,subtitle_lang)
					if False: #len(self.tvshow) > 0:
						#title, season, episode = regex_tvshow(False, zip_entry)
						if not episode : episode = -1
					else:
						if os.path.splitext( zip_entry )[1] in exts:
							movie_sub = True
					print "a",subtitle_file, file_path
					#if ( movie_sub or len(files) < 2 or int(episode) == int(self.episode) ):
					#	subtitle_set,file_path = self.copy_files( subtitle_file, file_path )
			
			if not subtitle_set:
				for zip_entry in files:
					if os.path.splitext( zip_entry )[1] in exts:
						subtitle_file, file_path = self.create_name(zip_entry,sub_filename,subtitle_lang)
						print "b", subtitle_file, file_path
						#subtitle_set,file_path  = self.copy_files( subtitle_file, file_path )            

		try:
			os.removedirs(str(self.tmp_sub_dir))
		except:
			pass
      #xbmc.Player().setSubtitles(file_path)


	def create_name(self,zip_entry,sub_filename,subtitle_lang):
		sub_ext  = os.path.splitext( zip_entry )[1]
		sub_name = os.path.splitext( sub_filename )[0]
		file_name = "%s.%s%s" % ( sub_name, subtitle_lang, sub_ext )   
		file_path = os.path.join(self.sub_folder, file_name)
		subtitle_file = os.path.join(self.tmp_sub_dir, zip_entry)
		return subtitle_file, file_path

gsubdown = None

def autostart(session):
	global gsubdown

if gAvailable is True:
	printl("Is available", __name__)
	#registerPlugin(Plugin(name=_("trakt.tv"), fnc=settings, where=Plugin.SETTINGS))
	registerPlugin(Plugin(name=_("SubtitleDownloader"), fnc=autostart, where=Plugin.AUTOSTART))
	registerPlugin(Plugin(name=_("Download subtitles"), start=DMC_SubtitleDownloader, where=Plugin.MENU_MOVIES_PLUGINS))