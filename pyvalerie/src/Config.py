# -*- coding: utf-8 -*-

import os

from Plugins.Extensions.ProjectValerie.__common__ import printl2 as printl

#------------------------------------------------------------------------------------------

conf = {}

def load():
	# Check default config
	try:
		printl("Check "+"/hdd/valerie/valerie.conf", __name__)
		if os.path.isfile("/hdd/valerie/valerie.conf") is False:
			f = open("/hdd/valerie/valerie.conf", "w")
			f.write("local=en\n")
			f.write("delete=true\n")
			f.write("sqlite=false\n")
			f.close()
			printl("\t- Created", __name__)
		else:
			printl("\t- OK", __name__)
	except Exception, ex:
		printl("Exception: " + str(ex), __name__)
	
	f = open("/hdd/valerie/valerie.conf", "r")
	for line in f.readlines():
		key,value = line.split("=")
		conf[key] = value
	f.close()

def getKey(key):
	if key in conf:
		return conf[key].strip()
	else:
		return "false"

def getString(key):
	return getKey(key)

def getBoolean(key):
	if getKey(key) == "true":
		return True
	else:
		return False
