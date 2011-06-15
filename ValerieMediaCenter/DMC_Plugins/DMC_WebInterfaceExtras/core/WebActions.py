# -*- coding: utf-8 -*-
from threading import Thread

from Components.config import config
from Components.config import ConfigInteger
from Components.config import ConfigSubsection

from Plugins.Extensions.ProjectValerie.__common__ import printl2 as printl
from Plugins.Extensions.ProjectValerie.__plugin__ import Plugin, registerPlugin

from Plugins.Extensions.ProjectValerie.DMC_Plugins.DMC_WebInterfaceExtras.core.WebData import WebData
from Plugins.Extensions.ProjectValerie.DMC_Plugins.DMC_WebInterfaceExtras.core.WebHelper import WebHelper


#------------------------------------------------------------------------------------------

# +++ LAZY IMPORTS +++
Manager = None
utf8ToLatin = None
# --- LAZY IMPORTS ---

gAvailable = False
try:
	from twisted.web.server import Site
	from twisted.web.static import File
	from twisted.internet   import reactor, threads
	from twisted.web.resource import Resource
	
	gAvailable = True
except Exception, ex:
	printl("DMC_WebInterfaceExtras::isAvailable Is not available", None, "E")
	printl("DMC_WebInterfaceExtras::isAvailable Exception: " + str(ex), None, "E")
	gAvailable = False

config.plugins.pvmc.plugins.webinterface = ConfigSubsection()
config.plugins.pvmc.plugins.webinterface.port = ConfigInteger(default = 8888, limits=(1, 65535) )

##
#
##
class WebActions(Resource):

	def render_GET(self, request):
		return self.action(request)

	def render_POST(self, request):
		return self.action(request)

	def action(self, request):
		global Manager
		global utf8ToLatin
		if Manager is None:
			from Plugins.Extensions.ProjectValerieSync.Manager import Manager
		if utf8ToLatin is None:
			from Plugins.Extensions.ProjectValerieSync.Utf8 import utf8ToLatin
		
		printl("request: " + str(request), self)
		printl("request.args: " + str(request.args), self)
		printl("request.args[method]: " + str(request.args["method"]), self)
		
		##
		# extras section
		##
		if request.args["method"][0] == "backup":
			import zipfile, os

			zipf = zipfile.ZipFile('/hdd/valerie-backup.zip', mode='w', compression=zipfile.ZIP_STORED )
			path = utf8ToLatin(config.plugins.pvmc.tmpfolderpath.value)
			WebHelper().recursive_zip(zipf, path)
			zipf.close()

			return WebHelper().redirectMeTo("/elog/valerie-backup.zip")	

		elif request.args["method"][0] == "restore":
			#http://webpython.codepoint.net/cgi_file_upload
			outputStream = open(filename, '/hdd/test.zip')
			outputStream.write(request.args['myFile'])
			outputStream.close()
			
		
		##
		# add section	
		##
		elif request.args["method"][0] == "add":
			# add movies
			if request.args["what"][0] == "isMovie":
				key_value_dict = {}
				for key in request.args.keys():
					key_value_dict[key] = request.args[key][0]
				
				primary_key = {}
				primary_key["imdbid"] = request.args["ImdbId"][0]
				
				manager = Manager()
				manager.addByUsingPrimaryKey(Manager.MOVIES, primary_key, key_value_dict)
				return WebHelper().redirectMeTo("/mediainfo?mode=done&target=movies")
			
			# add tvshows
			elif request.args["what"][0] == "isTvShow":
				key_value_dict = {}
				for key in request.args.keys():
					key_value_dict[key] = request.args[key][0]
				
				primary_key = {}
				primary_key["thetvdbid"] = request.args["TheTvDbId"][0]
				
				manager = Manager()
				manager.addByUsingPrimaryKey(Manager.TVSHOWS, primary_key, key_value_dict)
				return WebHelper().redirectMeTo("/mediainfo?mode=done&target=tvshows")	
			
			# add tvshowepisodes
			elif request.args["what"][0] == "isEpisode":
				key_value_dict = {}
				for key in request.args.keys():
					key_value_dict[key] = request.args[key][0]
				
				primary_key = {}
				primary_key["thetvdbid"] = request.args["TheTvDbId"][0]
				primary_key["season"] = request.args["Season"][0]
				primary_key["episode"] = request.args["Episode"][0]
				
				manager = Manager()
				manager.addByUsingPrimaryKey(Manager.TVSHOWSEPISODES, primary_key, key_value_dict)
				return WebHelper().redirectMeTo("/mediainfo?mode=done&target=episodes&TheTvDbId=" + request.args["TheTvDbId"][0])
		
		##
		# edit section	
		##
		elif request.args["method"][0] == "edit":
			# edit movies
			if request.args["what"][0] == "isMovie":
				key_value_dict = {}
				for key in request.args.keys():
					key_value_dict[key] = request.args[key][0]
				
				primary_key = {}
				primary_key["imdbid"] = request.args["ImdbId"][0]
				
				manager = Manager()
				manager.replaceByUsingPrimaryKey(Manager.MOVIES, primary_key, key_value_dict)
				return WebHelper().redirectMeTo("/mediainfo?mode=done&target=movies")
			
			# edit tvshows
			elif request.args["what"][0] == "isTvShow":
				key_value_dict = {}
				for key in request.args.keys():
					key_value_dict[key] = request.args[key][0]
				
				primary_key = {}
				primary_key["thetvdbid"] = request.args["TheTvDbId"][0]
				
				manager = Manager()
				manager.replaceByUsingPrimaryKey(Manager.TVSHOWS, primary_key, key_value_dict)
				return WebHelper().redirectMeTo("/mediainfo?mode=done&target=tvshows")
			
			# edit tvshowepisodes
			elif request.args["what"][0] == "isEpisode":
				key_value_dict = {}
				for key in request.args.keys():
					key_value_dict[key] = request.args[key][0]
				
				primary_key = {}
				primary_key["thetvdbid"] = request.args["TheTvDbId"][0]
				primary_key["season"] = request.args["Season"][0]
				primary_key["episode"] = request.args["Episode"][0]
				
				manager = Manager()
				manager.replaceByUsingPrimaryKey(Manager.TVSHOWSEPISODES, primary_key, key_value_dict)
				return WebHelper().redirectMeTo("/mediainfo?mode=done&target=episodes&TheTvDbId=" + request.args["TheTvDbId"][0])
		
		##
		# delete section
		##
		elif request.args["method"][0] == "delete":
			if request.args["what"][0] == "isMovie":
				primary_key = {}
				primary_key["imdbid"] = request.args["ImdbId"][0]
				
				manager = Manager()
				manager.removeByUsingPrimaryKey(Manager.MOVIES, primary_key)
				return WebHelper().redirectMeTo("/mediainfo?mode=done&target=movies")
		
		# delete tvshowepisodes
			elif request.args["what"][0] == "isEpisode":
				key_value_dict = {}
				for key in request.args.keys():
					key_value_dict[key] = request.args[key][0]
				
				primary_key = {}
				primary_key["thetvdbid"] = request.args["TheTvDbId"][0]
				primary_key["season"] = request.args["Season"][0]
				primary_key["episode"] = request.args["Episode"][0]
				
				manager = Manager()
				manager.removeByUsingPrimaryKey(Manager.TVSHOWSEPISODES, primary_key)
				return WebHelper().redirectMeTo("/mediainfo?mode=done&target=episodes&TheTvDbId=" + request.args["TheTvDbId"][0])
		
		##
		# save to db
		##	
		elif request.args["method"][0] == "save_changes_to_db":
			manager = Manager()
			manager.finish()
			
			if request.args["return_to"][0] == "movies":
				return WebHelper().redirectMeTo("/movies")
			elif request.args["return_to"][0] == "tvshows":
				return WebHelper().redirectMeTo("/tvshows")
			elif request.args["return_to"][0] == "episodes":
				return WebHelper().redirectMeTo("/episodes")
		