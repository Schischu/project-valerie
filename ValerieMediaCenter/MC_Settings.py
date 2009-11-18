from enigma import eTimer
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.ServiceInfo import ServiceInfoList, ServiceInfoListEntry
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Pixmap import Pixmap, MovingPixmap
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.Console import Console
from Components.ScrollLabel import ScrollLabel
from Components.config import *

from Components.Button import Button

from Tools.Directories import resolveFilename, fileExists, pathExists, createDir, SCOPE_MEDIA
from Components.FileList import FileList
from Components.AVSwitch import AVSwitch
from Plugins.Plugin import PluginDescriptor

try:
	from twisted.web.client import getPage
except Exception, e:
	print "Media Center: Import twisted.web.client failed"

from os import path, walk

from enigma import eServiceReference
import os

#------------------------------------------------------------------------------------------
def getAspect():
	val = AVSwitch().getAspectRatioSetting()
	return val/2
	
class MC_Settings(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

		list = []
		#list.append(("Titel", "nothing", "entryID", "weight"))
		list.append(("Global Settings", "MCS_GlobalSettings", "menu_globalsettings", "50"))
		list.append(("Skin Selector", "MCS_SkinSelector", "menu_skinselector", "50"))
		list.append(("Screen Adjustment", "MCS_ScreenAdjustment", "menu_screenadjustment", "50"))
		list.append(("Update MediaCenter", "MCS_Update", "menu_update", "50"))
		list.append(("Exit", "MCS_Exit", "menu_exit", "50"))
		self["menu"] = List(list)
		self["title"] = StaticText("")
		
		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"cancel": self.Exit,
			"ok": self.okbuttonClick
		}, -1)

	def okbuttonClick(self):
		print "okbuttonClick"
		selection = self["menu"].getCurrent()
		if selection is not None:
			if selection[1] == "MCS_GlobalSettings":
				self.session.open(MCS_GlobalSettings)
			elif selection[1] == "MCS_SkinSelector":
				self.session.open(MCS_SkinSelector)
			elif selection[1] == "MCS_ScreenAdjustment":
				self.session.open(MCS_ScreenAdjustment)
			elif selection[1] == "MCS_Update":
				self.session.open(MCS_Update)
			elif selection[1] == "MCS_Exit":
				self.close(0)
			else:
				self.session.open(MessageBox,("Error: Could not find plugin %s\ncoming soon ... :)") % (selection[1]),  MessageBox.TYPE_INFO)
			
	def Ok(self):
		self.session.open(MPD_PictureViewer)
		
	def Exit(self):
		self.close(0)
		


#------------------------------------------------------------------------------------------

class MCS_GlobalSettings(Screen):
	skin = """
		<screen position="160,220" size="400,120" title="Media Center - Global Settings" >
			<widget name="configlist" position="10,10" size="380,100" />
		</screen>"""
	
	def __init__(self, session):
		self.skin = MCS_GlobalSettings.skin
		Screen.__init__(self, session)

		self["actions"] = NumberActionMap(["SetupActions","OkCancelActions"],
		{
			"ok": self.keyOK,
			"cancel": self.close,
			"left": self.keyLeft,
			"right": self.keyRight,
			"0": self.keyNumber,
			"1": self.keyNumber,
			"2": self.keyNumber,
			"3": self.keyNumber,
			"4": self.keyNumber,
			"5": self.keyNumber,
			"6": self.keyNumber,
			"7": self.keyNumber,
			"8": self.keyNumber,
			"9": self.keyNumber
		}, -1)
		
		self.list = []
		self["configlist"] = ConfigList(self.list)
		self.list.append(getConfigListEntry(_("Language"), config.plugins.mc_globalsettings.language))
		self.list.append(getConfigListEntry(_("Show MC in Main-Menu"), config.plugins.mc_globalsettings.showinmainmenu))
		self.list.append(getConfigListEntry(_("Show MC in Extension-Menu"), config.plugins.mc_globalsettings.showinextmenu))
		self.list.append(getConfigListEntry(_("Check for Updates on Startup"), config.plugins.mc_globalsettings.checkforupdate))
		
	def keyLeft(self):
		self["configlist"].handleKey(KEY_LEFT)

	def keyRight(self):
		self["configlist"].handleKey(KEY_RIGHT)
		
	def keyNumber(self, number):
		self["configlist"].handleKey(KEY_0 + number)

	def keyOK(self):
		config.plugins.mc_globalsettings.save()
		self.close()
		
			
#------------------------------------------------------------------------------------------
# (c) 2006 Stephan Reichholf
# B0rked by Homey :)

class MCS_SkinSelector(Screen):
	skin = """
		<screen position="75,138" size="600,320" title="Choose your Skin" >
			<widget name="SkinList" position="10,10" size="275,300" scrollbarMode="showOnDemand" />
			<widget name="Preview" position="305,45" size="280,210" alphatest="on"/>
		</screen>
		"""

	skinlist = []
	root = "/usr/lib/enigma2/python/Plugins/Extensions/MediaCenter/skins/"

	def __init__(self, session, args = None):

		self.skin = MCS_SkinSelector.skin
		Screen.__init__(self, session)

		self.skinlist = []
		self.previewPath = ""

		path.walk(self.root, self.find, "")

		self.skinlist.sort()
		self["SkinList"] = MenuList(self.skinlist)
		self["Preview"] = Pixmap()

		self["actions"] = NumberActionMap(["WizardActions", "InputActions", "EPGSelectActions"],
		{
			"ok": self.ok,
			"back": self.close,
			"up": self.up,
			"down": self.down,
			"left": self.left,
			"right": self.right
		}, -1)
		
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		tmp = config.plugins.mc_globalsettings.currentskin.path.value.find('/skin.xml')
		if tmp != -1:
			tmp = config.plugins.mc_globalsettings.currentskin.path.value[:tmp]
			idx = 0
			for skin in self.skinlist:
				if skin == tmp:
					break
				idx += 1
			if idx < len(self.skinlist):
				self["SkinList"].moveToIndex(idx)
		self.loadPreview()

	def up(self):
		self["SkinList"].up()
		self.loadPreview()

	def down(self):
		self["SkinList"].down()
		self.loadPreview()

	def left(self):
		self["SkinList"].pageUp()
		self.loadPreview()

	def right(self):
		self["SkinList"].pageDown()
		self.loadPreview()

	def find(self, arg, dirname, names):
		for x in names:
			if x == "skin.xml":
				if dirname <> self.root:
					foldername = dirname.split('/')
					subdir = foldername[-1]
					self.skinlist.append(subdir)
				else:
					subdir = "Default Skin"
					self.skinlist.append(subdir)

	def ok(self):
		if self["SkinList"].getCurrent() == "Default Skin":
			skinfile = "default/skin.xml"
		else:
			skinfile = self["SkinList"].getCurrent()+"/skin.xml"

		print "Skinselector: Selected Skin: "+self.root+skinfile
		config.plugins.mc_globalsettings.currentskin.path.value = skinfile
		config.plugins.mc_globalsettings.currentskin.path.save()
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply a new skin\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI now?"))

	def loadPreview(self):
		if self["SkinList"].getCurrent() == "Default Skin":
			pngpath = self.root+"/preview.png"
		else:
			pngpath = self.root+self["SkinList"].getCurrent()+"/preview.png"

		if not path.exists(pngpath):
			# FIXME: don't use hardcoded path
			pngpath = "/usr/lib/enigma2/python/Plugins/Extensions/MediaCenter/skins/noprev.png"

		if self.previewPath != pngpath:
			self.previewPath = pngpath

		self["Preview"].instance.setPixmapFromFile(self.previewPath)

	def restartGUI(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)

	
#------------------------------------------------------------------------------------------

DEFAULT_DST_TOP = 0
DEFAULT_DST_LEFT = 0
DEFAULT_DST_HEIGHT = 576
DEFAULT_DST_WIDTH = 720

class MCS_ScreenAdjustment(Screen):
	skin = """
		<screen position="40,40" size="180,190" title="Screen Adjustment" flags="wfNoBorder" >
			<widget name="posinfox" position="40,40" transparent="0" zPosition="2" size="150,25" font="Regular;14" />
			<widget name="posinfoy" position="40,55" zPosition="2" size="150,25" font="Regular;14" />
			<widget name="posinfow" position="40,70" zPosition="2" size="150,25" font="Regular;14" />
			<widget name="posinfoh" position="40,85" zPosition="3" size="150,25" font="Regular;14" />
			<widget name="infotext" position="40,130" zPosition="2" size="150,50" font="Regular;14" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.curposx = config.plugins.mc_globalsettings.dst_left.value
		self.curposy = config.plugins.mc_globalsettings.dst_top.value
		self.curposw = config.plugins.mc_globalsettings.dst_width.value
		self.curposh = config.plugins.mc_globalsettings.dst_height.value
		
		self["posinfox"] = Label("Position X: " + str(config.plugins.mc_globalsettings.dst_left.value))
		self["posinfoy"] = Label("Position Y: " + str(config.plugins.mc_globalsettings.dst_top.value))
		self["posinfow"] = Label("Width: " + str(config.plugins.mc_globalsettings.dst_width.value))
		self["posinfoh"] = Label("Height: " + str(config.plugins.mc_globalsettings.dst_height.value))

		self["infotext"] = Label("Vol +-: Height\nBouq +-: Width\nBlue: Reset")
		
		self["actions"] = NumberActionMap(["ChannelSelectBaseActions", "NumberActions", "GlobalActions", "WizardActions", "MenuActions", "ShortcutActions", "SetupActions", "ColorActions"], 
		{
			"ok": self.keySave,
			"cancel": self.Exit,
			"up": self.keyUp,
			"down": self.keyDown,
			"left": self.keyLeft,
			"right": self.keyRight,
			"nextBouquet": self.WidthUp,
			"prevBouquet": self.WidthDown,
			"volumeUp": self.HeightUp,
			"volumeDown": self.HeightDown,
			"blue": self.keyReset
		}, -1)

		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()

		os.system("/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/MediaCenter/icons/screenadjust.mvi &")

		os.system("echo " + hex(config.plugins.mc_globalsettings.dst_top.value)[2:] + " > /proc/stb/vmpeg/0/dst_top")
		os.system("echo " + hex(config.plugins.mc_globalsettings.dst_left.value)[2:] + " > /proc/stb/vmpeg/0/dst_left")
		os.system("echo " + hex(config.plugins.mc_globalsettings.dst_width.value)[2:] + " > /proc/stb/vmpeg/0/dst_width")
		os.system("echo " + hex(config.plugins.mc_globalsettings.dst_height.value)[2:] + " > /proc/stb/vmpeg/0/dst_height")
		
    # Workaround
		#os.system("echo  180 > /proc/stb/vmpeg/0/dst_height")
		#os.system("echo  240 > /proc/stb/vmpeg/0/dst_height")
		
	def keyUp(self):
		self.curposy -= 1
		
		if self.curposy < 0:
			self.curposy = 0

		self["posinfoy"].setText(("Position Y: %s (%s)\n") % (self.curposy,hex(self.curposy)[2:]))
		os.system("echo " + hex(self.curposy)[2:] + " > /proc/stb/vmpeg/0/dst_top")
		#self.session.open(MessageBox,("Position Y: %s\n") % (self.curposy),  MessageBox.TYPE_INFO)

	def keyDown(self):
		if self.curposy + self.curposh >= DEFAULT_DST_HEIGHT:
			return

		self.curposy += 1
		
		if self.curposy < 0:
			self.curposy = 0

		self["posinfoy"].setText(("Position Y: %s (%s)\n") % (self.curposy,hex(self.curposy)[2:]))
		os.system("echo " + hex(self.curposy)[2:] + " > /proc/stb/vmpeg/0/dst_top")
		#self.session.open(MessageBox,("Position Y: %s\n") % (hex(self.curposy)),  MessageBox.TYPE_INFO)
		
	def keyLeft(self):
		self.curposx -= 1
			
		if self.curposx < 0:
			self.curposx = 0
		
		self["posinfox"].setText(("Position X: %s (%s)\n") % (self.curposx,hex(self.curposx)[2:]))
		os.system("echo " + hex(self.curposx)[2:] + " > /proc/stb/vmpeg/0/dst_left")
		#self.session.open(MessageBox,("Position X: %s\n") % (self.curposx),  MessageBox.TYPE_INFO)

	def keyRight(self):
		if self.curposx + self.curposw >= DEFAULT_DST_WIDTH:
			return

		self.curposx += 1
		
		if self.curposx < 0:
			self.curposx = 0

		self["posinfox"].setText(("Position X: %s (%s)\n") % (self.curposx,hex(self.curposx)[2:]))
		os.system("echo " + hex(self.curposx)[2:] + " > /proc/stb/vmpeg/0/dst_left")
		#self.session.open(MessageBox,("Position X: %s\n") % (self.curposx),  MessageBox.TYPE_INFO)

	def WidthUp(self):
		if self.curposw + self.curposx >= DEFAULT_DST_WIDTH:
			return

		self.curposw += 1
					
		if self.curposw > DEFAULT_DST_WIDTH:
			self.curposw = DEFAULT_DST_WIDTH
		if self.curposw < 0:
			self.curposw = 0
			
		self["posinfow"].setText(("Width: %s (%s)\n") % (self.curposw,hex(self.curposw)[2:]))
		os.system("echo " + hex(self.curposw)[2:] + " > /proc/stb/vmpeg/0/dst_width")
		#self.session.open(MessageBox,("Width: %s\n") % (self.curposw),  MessageBox.TYPE_INFO)

	def WidthDown(self):
		self.curposw -= 1
			
		if self.curposw > DEFAULT_DST_WIDTH:
			self.curposw = DEFAULT_DST_WIDTH
		if self.curposw < 0:
			self.curposw = 0
		
		self["posinfow"].setText(("Width: %s (%s)\n") % (self.curposw,hex(self.curposw)[2:]))
		os.system("echo " + hex(self.curposw)[2:] + " > /proc/stb/vmpeg/0/dst_width")
		#self.session.open(MessageBox,("Width: %s\n") % (self.curposw),  MessageBox.TYPE_INFO)

	def HeightUp(self):
		if self.curposh + self.curposy >= DEFAULT_DST_HEIGHT:
			return

		self.curposh += 1
		
		if self.curposh > DEFAULT_DST_HEIGHT:
			self.curposh = DEFAULT_DST_HEIGHT
		if self.curposh < 0:
			self.curposh = 0
			
		self["posinfoh"].setText(("Height: %s (%s)\n") % (self.curposh,hex(self.curposh)[2:]))
		os.system("echo " + hex(self.curposh)[2:] + " > /proc/stb/vmpeg/0/dst_height")
		#self.session.open(MessageBox,("Height: %s\n") % (self.curposh),  MessageBox.TYPE_INFO)

	def HeightDown(self):
		self.curposh -= 1
			
		if self.curposh > DEFAULT_DST_HEIGHT:
			self.curposh = DEFAULT_DST_HEIGHT
		if self.curposh < 0:
			self.curposh = 0

		self["posinfoh"].setText(("Height: %s (%s)\n") % (self.curposh,hex(self.curposh)[2:]))
		os.system("echo " + hex(self.curposh)[2:] + " > /proc/stb/vmpeg/0/dst_height")
		#self.session.open(MessageBox,("Height: %s\n") % (self.curposh),  MessageBox.TYPE_INFO)

	def keyReset(self):
		os.system("echo " + hex(DEFAULT_DST_TOP)[2:] + " > /proc/stb/vmpeg/0/dst_top")
		os.system("echo " + hex(DEFAULT_DST_LEFT)[2:] + " > /proc/stb/vmpeg/0/dst_left")
		os.system("echo " + hex(DEFAULT_DST_WIDTH)[2:] + " > /proc/stb/vmpeg/0/dst_width")
		os.system("echo " + hex(DEFAULT_DST_HEIGHT)[2:] + " > /proc/stb/vmpeg/0/dst_height")
		self["posinfox"].setText(("Position X: %s (%s)\n") % (DEFAULT_DST_LEFT,hex(DEFAULT_DST_LEFT)[2:]))
		self["posinfoy"].setText(("Position Y: %s (%s)\n") % (DEFAULT_DST_TOP,hex(DEFAULT_DST_TOP)[2:]))
		self["posinfow"].setText(("Width: %s (%s)\n") % (DEFAULT_DST_WIDTH,hex(DEFAULT_DST_WIDTH)[2:]))
		self["posinfoh"].setText(("Height: %s (%s)\n") % (DEFAULT_DST_HEIGHT,hex(DEFAULT_DST_HEIGHT)[2:]))
		
	def keySave(self):
		config.plugins.mc_globalsettings.dst_top.value = self.curposy
		config.plugins.mc_globalsettings.dst_left.value = self.curposx
		config.plugins.mc_globalsettings.dst_width.value = self.curposw
		config.plugins.mc_globalsettings.dst_height.value = self.curposh
		config.plugins.mc_globalsettings.save()
		configfile.save()
		
		self.session.nav.stopService()
		self.session.nav.playService(self.oldService)
		self.close()
		
	def Exit(self):
		self.session.nav.stopService()
		self.session.nav.playService(self.oldService)
		os.system("echo " + hex(config.plugins.mc_globalsettings.dst_top.value)[2:] + " > /proc/stb/vmpeg/0/dst_top")
		os.system("echo " + hex(config.plugins.mc_globalsettings.dst_left.value)[2:] + " > /proc/stb/vmpeg/0/dst_left")
		os.system("echo " + hex(config.plugins.mc_globalsettings.dst_width.value)[2:] + " > /proc/stb/vmpeg/0/dst_width")
		os.system("echo " + hex(config.plugins.mc_globalsettings.dst_height.value)[2:] + " > /proc/stb/vmpeg/0/dst_height")
		self.close()



#------------------------------------------------------------------------------------------

class MCS_Update(Screen):
	skin = """
		<screen position="110,110" size="500,380" title="Media Center - Software Update" >
			<widget name="text" position="10,10" size="480,360" font="Regular;20" />
		</screen>"""
	
	def __init__(self, session):
		self.skin = MCS_Update.skin
		Screen.__init__(self, session)

		self.working = False
		self.Console = Console()
		self["text"] = ScrollLabel("Checking for updates ...")
		
		self["actions"] = NumberActionMap(["WizardActions", "InputActions", "EPGSelectActions"],
		{
			"ok": self.close,
			"back": self.close
		}, -1)
		
		self.url = "http://www.homeys-bunker.de/dm800/projects/MediaCenter/"
		
		self.onFirstExecBegin.append(self.CheckForMCUpdate)
		
	def CheckForMCUpdate(self):
		#Get Info from my webserver
		try:
			getPage(self.url + "currentversion.txt").addCallback(self.GotMCUpdateInfo).addErrback(self.error)
			self["text"].setText(_("Checking for updates ..."))
		except Exception, e:
			self["text"].setText(_("Error: Twisted-Web not installed"))

	def GotMCUpdateInfo(self, html):
		tmp_infolines = html.splitlines()
		
		remoteversion = tmp_infolines[0]
		
		if config.plugins.mc_globalsettings.currentplatform.value == "mipsel":
			self.installfilename = tmp_infolines[1]
		elif config.plugins.mc_globalsettings.currentplatform.value == "powerpc":
			self.installfilename = tmp_infolines[2]
		else:
			self.installfilename = ""
			return
		
		if config.plugins.mc_globalsettings.currentversion.value < remoteversion:
			self["text"].setText("A new version of MediaCenter is available :-)\n\nInstall: %s" % self.installfilename)
			self.initupdate()
		else:
			self["text"].setText("Your MediaCenter is up to date! No update required ...")
	
	def initupdate(self):
		self.working = True
		
		if self.installfilename != "":
			cmd = "ipkg install -force-overwrite " + str(self.url) + str(self.installfilename)
			
			self["text"].setText("Updating MediaCenter ...\n\n\nStay tuned :-)")
			self.Console.ePopen(cmd, self.startupdate)
		
	def startupdate(self, result, retval, extra_args):
		if retval == 0:
			self.working = True
			self["text"].setText(result)
			self.session.open(MessageBox,("Your MediaCenter was hopefully updated now ...\n\nYou have to restart Enigma now!"),  MessageBox.TYPE_INFO)
		else:
			self.working = False
