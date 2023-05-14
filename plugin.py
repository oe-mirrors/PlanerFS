######################################
# PlanerFS (beginn 24.10.2010)       #
#                                    #
#   Enigma2 Plugin                   #
#                                    #
#  Author: shadowrider (fs-plugins)  #
#  Py3-Version: Mr.Servo (openA.TV)  #
######################################

# PYTHON IMPORTS
from configparser import ConfigParser
from datetime import datetime, timedelta
from os import listdir, system
from os.path import exists
from pickle import dump
from time import localtime, time, strftime

# ENIGMA IMPORTS
from enigma import eTimer
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Standby import inStandby
from Screens import Standby
from Tools import Notifications
from Tools.Directories import copyfile, fileExists

# PLUGIN IMPORTS
from . import _ # for localized messages
from .timer import Timer_dats
from .routines import schicht
from .termin import TerminList
from .PFSanzeige import startscreen8
from .PFSCards import PFS_show_card_List7
from .PFSimport import online_import
from .PFSpaint import mspFS_paint
from .PFSwe import PFS_show_we
from .PlanerFS import PlanerFS7

version = "10.0beta"
txt = "Version: %s\n" % version
CONFIGFILE = "/etc/ConfFS/PlanerFS.conf"
ONLINETEXT = "/etc/ConfFS/PlanerFS_online.txt"
cal_files_path = "/etc/ConfFS"
icsdatei = "PlanerFS.ics"
termindatei = "%s/%s" % (cal_files_path, icsdatei)
try:
	from Plugins.Extensions.LCD4linux.module import L4Lelement
	L4L = True
except Exception:
	L4L = None
	txt += "No L4L\n"

try:
	if not fileExists(termindatei):
		copyfile("/usr/lib/enigma2/python/Plugins/Extensions/sample_PlanerFS/sample.ics", termindatei)
	if not fileExists("/etc/ConfFS/PlanerFS.vcf"):
		copyfile("/usr/lib/enigma2/python/Plugins/Extensions/PlanerFS/sample.vcf", "/etc/ConfFS/PlanerFS.vcf")
except Exception:
	pass

#DPKG = False
conf = {
		"ext_menu": "True",
		"startscreen_plus": "True",
		"version": "",
		"plfs_list": "",
		"timer_on": "On",
		"akt_intv": 24,
		"startanzeige2": "systemstart",
		"timestartstandby": "No",
		"kalender_art": "Gregorian",
		"vorschaum": 3,
		"starttime": "None",
		"autosync": "No",
		"sec_file": "none",
		"cal_menu": 1,
		"adr_menu": 1,
		"l4l_on": "Yes",
		"l4l_lcd": 1,
		"l4l_screen": 1,
		"l4l_font": 40,
		"l_ferien": 0,
		"ferien": 0,
		"schicht_send_url": None,
		"dat_dir": '/etc/ConfFS/',
		"cals_dir": "/tmp/",
		"categories": "Keine,Geburtstag,Feiertag,Jahrestag,Hochzeitstag,Keine,Keine,Keine,Keine,Keine",
		"cat_color_list": "#00008B,#D2691E,#006400,#696969,#FFD700,#000000,#B22222,#8B8878,#CD0000,#00868B,#f0f8ff,#ff4500,#20343c4f,#deb887,#228B22,#5F9EA0,#DC143C,#F0F8FF,#EEC900",
		"z_liste": "0,1,0,1,1,0,0,0,0,0",
		}
systemstart = 0
display_size = None
l4l_sets = [1, 1, 40]
plfstimer_list = []
plfs_list = []
configparser = ConfigParser()
if exists(CONFIGFILE):
	configparser.read(CONFIGFILE)
	if configparser.has_section("settings"):
		l1 = configparser.items("settings")
		for k, v in l1:
			if k == "l4l_lcd":
				l4l_sets[0] = int(v)
			elif k == "l4l_screen":
				l4l_sets[1] = int(v)
			elif k == "l4l_font":
				l4l_sets[2] = int(v)
			elif k == "date_dir":
				if v.endswith("/"):
					conf["dat_dir"] = v
				else:
					conf["dat_dir"] = v + "/"
			else:
				try:
					conf[k] = int(v)
				except Exception:
					conf[k] = v
		if str(conf["version"]) != version:
			configparser.read(CONFIGFILE)
			configparser.set("settings", "version", version)
			conf["version"] = version
			file1 = open(CONFIGFILE, "w")
			configparser.write(file1)
			file1.close()
else:
	datei = open(CONFIGFILE, "w")
	configparser.add_section("settings")
	for k, v in conf.items():
		configparser.set("settings", k, v)
	configparser.write(datei)
	datei.close()
onl_lines = []
if exists(ONLINETEXT):
	fp = open(ONLINETEXT, 'r')
	onl_lines = fp.readlines()
	fp.close()
else:
	fp = open("/etc/ConfFS/PlanerFS_online.txt", "w")
	fp.write("##internetadressen fuer online-Kalender\n# Aufbau:\n##    name = url = calendarNr\n##sample (delete # / entferne #) :\n")
	fp.write("\n#Feiertage_Germany = https://calendar.google.com/calendar/ical/de.german%23holiday%40group.v.calendar.google.com/public/basic.ics\n")
	fp.close()
time_timer = Timer_dats(None, None, None)
global akt_intv
if int(conf["akt_intv"]):
	akt_intv = int(conf["akt_intv"])
	if akt_intv > 1440:
		akt_intv = 1440
	akt_intv = akt_intv * 60
else:
	akt_intv = 0
cal_menu = conf["cal_menu"]
adr_menu = conf["adr_menu"]
startscreen_plus = conf["startscreen_plus"]

class einlesen():
	def __init__(self, r=False):
		if r:
			global plfstimer_list
			global plfs_list
			fer = None
			if str(conf["l_ferien"]) != "0":
				fer = (conf["ferien"], conf["l_ferien"])
			termine = []
			timer = []
			schichten = []
			erg = 1
			if conf["autosync"] == "Yes":
				path = ONLINETEXT
				if conf["dat_dir"] != '/etc/ConfFS/' and exists(conf["dat_dir"] + 'PlanerFS_online.txt'):
					path = conf["dat_dir"] + 'PlanerFS_online.txt'
				erg = online_import().run(path, fer, True)
				if erg == 0 and not inStandby:
					Notifications.AddNotification(MessageBox, "PlanerFS\n" + _("Error: at least one external file could not be loaded!"), type=MessageBox.TYPE_ERROR, timeout=30)
			files = []
			if conf["kalender_art"] != "Off":
				files.append("kalender")
			if conf["sec_file"] != "" and conf["sec_file"] != _("none") and exists(conf["sec_file"]):
				files.append(conf["sec_file"])
			if exists(conf["dat_dir"]):
				for cal_file in listdir(conf["dat_dir"]):
					n1 = conf["dat_dir"] + cal_file
					if cal_file.endswith(".ics") and not n1 in files:
						files.append(n1)
			if conf["cals_dir"] != conf["dat_dir"] and exists(conf["cals_dir"]):
				for cal_file in listdir(conf["cals_dir"]):
					if cal_file.endswith(".ics"):
						if (not cal_file.startswith("1ferien") or not cal_file.startswith("2ferien")) or conf["l_ferien"]:
							files.append(conf["cals_dir"] + cal_file)
			fileliste = []
			if len(files):
				for file1 in files:
					if file1 not in fileliste and exists(file1):
						fileliste.append(file1)
						TL = TerminList()
						l2 = TL.getlists(file1, 0)
						termine.extend(l2[0])
						timer.extend(l2[1])
						if len(l2) == 4:
							schichten.extend(l2[3])
			if erg and str(conf["schicht_send_url"]) and len(schichten):
				schicht1 = schicht().parseSchicht(schichten, "export1")
				nl2 = ""
				if schicht1 and len(schicht1):
					anz = len(schicht1)
					for i2 in range(anz):
						sh1 = schicht1[i2]
						nt = sh1[1].replace(" ", "%20")
						if nt == None or nt == "":
							nt = "frei"
						nl2 += sh1[3].strftime('%d.%m.%Y') + "," + nt + ";"
				opt = ' -O /dev/null'
				ur = str(conf["schicht_send_url"]) + nl2
				com = 'wget "' + ur + '"' + opt
				f = open("/tmp/schicht", "w")
				f.write(strftime("%d.%m.%y %H:%M:%S", localtime()) + " send schichtdaten\n")
				f.close()
				system(com)
			if L4L is not None and len(schichten):
				mspFS_paint(schichten)
			if len(termine):
				termine.sort(key=lambda x: x[9])
			plfstimer_list = timer
			plfs_list = termine


class Termin_Timer():
	def __init__(self):
		self.session = None
		self.erstmal = 0
		self.aktual_timer = eTimer()
		self.startzeit_timer = None
		self.display_timer = None
		self.MyElements = None
		self.pfsstandby = False

	def saveSession(self, session):
		self.session = session

	def standby_on(self):
		if inStandby:
			self.pfsstandby = False
			Standby.inStandby.onHide.append(self.Days)
		else:
			if not self.pfsstandby:
				self.pfsstandby = True
				config.misc.standbyCounter.addNotifier(self.standby_start, initial_call=False)

	def standby_start(self, configElement):
		self.pfsstandby = False
		if self.standby_check_timer1:
			self.standby_check_timer1.startLongTimer(60)

	def Starter(self):
		if time() < 1383701983:
			self.sttimer = eTimer()
			self.sttimer.timeout.get().append(self.datecheck)
			self.sttimer.startLongTimer(2)
		else:
			self.Starter2()

	def datecheck(self):
		if time() < 1383701983:
			self.sttimer = eTimer()
			self.sttimer.timeout.get().append(self.datecheck)
			self.sttimer.startLongTimer(2)
		else:
			self.Starter2()

	def Starter2(self):
		start_s = conf["startanzeige2"].replace("(idle)", "")
		global systemstart
		self.standby_check_timer1 = None
		if self.startzeit_timer:
			self.startzeit_timer.stop()
			self.startzeit_timer = None
		self.run_timer = None
		if not exists(termindatei):
			with open(termindatei, "w") as f:
				f.write("BEGIN:VCALENDAR\nMETHOD:PUBLISH\nPRODID: -EnigmaII-Plugin / PlanerFS " + conf["version"] + "\nVERSION:2.0")
				f.write("\nEND:VCALENDAR")
		einlesen(True)
		if akt_intv > 0:
			self.aktual_timer.timeout.get().append(self.aktual)
			self.aktual_timer.startLongTimer(akt_intv)
		if conf["timer_on"] == "On":
			if len(plfstimer_list):
				global time_timer
				time_timer = Timer_dats(None, None, None)
				time_timer.startTimer(self.session, plfstimer_list, None)
		if start_s != "None" and "time" in start_s:
			st = conf["starttime"].strip().split(':')
			sek = ((int(st[0]) * 60) + int(st[1]))  # stunde
			now = [x for x in localtime()]
			sek2 = ((now[3] * 60) + now[4])
			start = (sek - sek2) * 60
			self.startzeit_timer = eTimer()
			self.startzeit_timer.timeout.get().append(self.Days1)
			if start < 0:
				start = start + 86400
			elif start < 20:
				start = 86400 - start
			self.startzeit_timer.startLongTimer(start)
		if "systemstart" in start_s:
			if systemstart == 0:
				self.Days()
				systemstart = 1
		if "standby" in start_s:
			self.standby_check_timer1 = eTimer()
			self.standby_check_timer1.timeout.get().append(self.standby_on)
			self.standby_check_timer1.startLongTimer(60)
			self.standby_on()
		else:
			pass
		if L4L is not None and conf["l4l_on"] == "Yes":
			self.l4l()

	def Days1(self):
		if inStandby:
			if conf["timestartstandby"] == "Yes" and conf["startanzeige2"] != "standby and time":
				Standby.inStandby.onHide.append(self.Days)
		else:
			self.Days()

	def Days(self):
		if self.standby_check_timer1:
			self.standby_check_timer1.startLongTimer(60)
		if len(plfs_list):
			Notifications.AddNotificationWithCallback(check_re, startscreen8, plfs_list, conf["version"])

	def aktual(self):
		einlesen(True)
		if str(conf["timer_on"]) == "On":
			time_timer.restart(self.session, plfstimer_list, None)
		if L4L and conf["l4l_on"] == "Yes":
			self.l4l()
		z = datetime.today()
		end = datetime(z.year, z.month, z.day, 0, 0, 2) + timedelta(1)
		diff = end - z
		next2 = diff.seconds
		if next2 > akt_intv and akt_intv > 0:
			next2 = akt_intv
		self.aktual_timer.startLongTimer(next2)

	def l4l(self):
		global L4L
		global display_size
		if self.MyElements is None and L4L is not None:
			self.display_timer = eTimer()
			self.display_timer.timeout.get().append(self.l4l)
			if self.MyElements is None:
				from Plugins.Extensions.LCD4linux.module import L4Lelement
				self.MyElements = L4Lelement()
			if display_size is not None and display_size > 0:
				if self.display_timer:
					self.display_timer.stop()
					self.display_timer = None
				if len(plfs_list) > 0:
					from .PFSl4l import PFS_l4l
					PFS_l4l(plfs_list, l4l_sets, conf["vorschaum"], display_size)
			else:
				display_size = self.MyElements.getResolution(l4l_sets[0])[1]
				self.display_timer.startLongTimer(2)
if len(txt):
	with open("/tmp/PlanerFS-Errors.txt", "w") as f:
		f.write(txt)
	txt = ""
t_timer = Termin_Timer()

def uebersicht(session, **kwargs):
	einlesen(True)
	session.openWithCallback(check_re, startscreen8, plfs_list, version)

def main(session, **kwargs):
	session.openWithCallback(check_re, PlanerFS7)

def check_re(session=None, *args):
	if session and args:
		main(session)

def adress(session, **kwargs):
	session.open(PFS_show_card_List7, None, version)

def adress_menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("PlanerFS address book"), adress, "PlanerFS address book", 58)]
	return []

def pfs_wecker(session, **kwargs):
	session.open(PFS_show_we)

def pfs_wecker2(**kwargs):
	begin = -1
	if len(plfstimer_list):
		if exists(termindatei):
			TL = TerminList()
			l2 = TL.getlists(termindatei, 1)
			tim_list = l2[1]
			tim_list.sort(key=lambda x: x[10])
			for x in tim_list:
				if x[10] + (config.recording.margin_before.value * 60) > time():
					dump(x, open("/media/hdd/plfs_dstart", 'wb'), 1)
					begin = x[10] + (config.recording.margin_before.value * 60) + (x[11] * 60)
					break
	return begin

def calen_menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("PlanerFS"), main, "PlanerFS", 57)]
	return []

def autostart(**kwargs):
	if "session" in kwargs:
		session = kwargs["session"]
		t_timer.saveSession(session)
	t_timer.Starter()

def Plugins(**kwargs):
	pfc_list = [PluginDescriptor.WHERE_PLUGINMENU]
	pfa_list = [PluginDescriptor.WHERE_PLUGINMENU]
	if cal_menu == 2 or cal_menu == 4:
		pfc_list.append(PluginDescriptor.WHERE_EXTENSIONSMENU)
	if adr_menu == 2 or adr_menu == 4:
		pfa_list.append(PluginDescriptor.WHERE_EXTENSIONSMENU)
	liste = [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart, wakeupfnc=pfs_wecker2),
		  PluginDescriptor(name="PlanerFS", where=pfc_list, icon="PlanerFS.png", description=_("Schedule appointments, view events"), fnc=main),
		  PluginDescriptor(name=_("PlanerFS address book"), description=_("addresses and phone numbers search, find, manage, and more"), where=pfa_list, icon="PlanerFS_adr.png", fnc=adress), ]
	if startscreen_plus == "True":
		liste.append(PluginDescriptor(name=_("PlanerFS overview"), where=pfc_list, icon="PlanerFS.png", description=_("Show start screen with overview"), fnc=uebersicht))
	if cal_menu == 3 or cal_menu == 4:
		liste.append(PluginDescriptor(name="PlanerFS", where=PluginDescriptor.WHERE_MENU, fnc=calen_menu))
	if adr_menu == 3 or adr_menu == 4:
		liste.append(PluginDescriptor(name="PlanerFS address book", where=PluginDescriptor.WHERE_MENU, fnc=adress_menu))
	liste.append(PluginDescriptor(name="PlanerFS alarm clock", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=pfs_wecker))
	return liste
