#####################################################################################
#  All Files of this Software are licensed under the Creative Commons               #
#  Attribution-NonCommercial-ShareAlike 3.0 Unported                                #
#  License if not stated otherwise in a Files Head. To view a copy of this license, #
#  visit http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to      #
#  Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.        #
#                                                                                   #
#  Alternatively, this plugin may be distributed and executed on hardware which    #
#  is licensed by Dream Multimedia GmbH.                                           #
#                                                                                  #
#  This plugin is NOT free software. It is open source, you are allowed to         #
#  modify it (if you keep the license), but it may not be commercially             #
#  distributed other than under the conditions noted above.                        #
#                                                                                  #
#  PlanerFS von shadowrider, Python3-Version von Mr.Servo (openA.TV)               #
####################################################################################

# PYTHON IMPORTS
from configparser import ConfigParser
from datetime import datetime, timedelta, date
from os import listdir
from os.path import exists, isfile, getsize, join
from re import compile
from time import localtime, strftime, strptime

# ENIGMA IMPORTS
from enigma import eTimer
from Components.ActionMap import NumberActionMap, HelpableActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from skin import parseColor

try:
	from Plugins.Extensions.Fritzcall.plugin import FritzCallFBF
	fbf = FritzCallFBF
except ImportError:
	fbf = None

# PLUGIN IMPORTS
from . import CONFIGPATH, CONFIGFILE, PLUGINPATH, ICSNAME, ICSNAME2, ICSFILE, VCFFILE, ERRORLOG, DWIDE, _  # for localized messages
from .PFSconfig import PlanerFSConfiguration
from .PFScateg import PFS_categorie_conf7, schicht_conf
from .PFSCards import PFS_show_card7, PFS_show_card_List7
from .PFSEdit import PFS_edit_Termin
from .PFSfiles import PFS_filemenu7
from .PFSimport import online_import
from .PFSonl import PlanerFSonline_files
from .routines import Feiertage, Rules, Next_Termin, Farben, schicht

msp_liste = ()
try:
	from Plugins.Extensions.mspFS.exporter import exporter
	msp = True
except Exception:
	msp = False

conf = {
		"dat_dir": CONFIGPATH,
		"altloesch": 365,
		"cals_dir": "/tmp/",
		"altloesch_on": "No",
		"extern_color": "On",
		"kalender_art": "Gregorian",
		"ansicht": 1,
		"version": "",
		"cards_on": None,
		"dat_dir": CONFIGPATH,
		"schicht_art": 0,
		"ferien": 0,
		"l_ferien": 0,
		"schicht_col": {"F": "#008B45", "S": "#FFD700", "N": "#3A5FCD", "fr": "#858585"},
		"bgr_skin": 1
		}
categories1 = []
color_list = []
z_liste = ("0", "1", "1", "0", "1", "1", "0", "0", "0", "0")
configparser = ConfigParser()
if exists(CONFIGFILE):
	configparser.read(CONFIGFILE)
	if configparser.has_section("settings"):
		l1 = configparser.items("settings")
		for k, v in l1:
			if len(str(v)):
				if k == "categories":
					cat_categories = v
					categories1 = list(cat_categories.split(","))
				elif k == "schicht_col":
					conf["schicht_col"] = v
				elif k == "cat_color_list":
					cat_color_list = v
					color_list = list(cat_color_list.split(","))
				elif k == "z_liste":
					z_liste = list(v.split(","))
				else:
					conf[k] = v
allcolor_list = ["#00008B", "#D2691E", "#006400", "#696969", "#FFD700", "#000000", "#B22222", "#8B8878", "#CD0000", "#00868B", "#f0f8ff", "#ff4500", "#20343c4f", "#deb887", "#228B22", "#5F9EA0", "#DC143C", "#F0F8FF", "#EEC900", "#20343c4f", "#f0f8ff"]
if len(color_list) < 21:
	color_list.extend(allcolor_list[len(color_list):])
if len(categories1) < 10:
	categories1 = (_("None"), _("Birthday"), _("Holiday"), _("Anniversary"), _("Wedding day"), _("None"), _("None"), _("None"), _("None"), _("None"))
cal_bg = Farben().farb_re(color_list[12])
color_inactiv = Farben().farb_re(color_list[15])
rot = Farben().farb_re(color_list[16])
weiss = Farben().farb_re(color_list[17])
ansicht = 1
lt = localtime()


class PlanerFS7(Screen, HelpableScreen):
	def __init__(self, session):
		global ansicht
		global conf
		global color_list
		global categories1
		global cal_bg, color_inactiv, rot, weiss
		skindatei = join(PLUGINPATH, "skin/%s/PlanerFS.xml" % ("fHD" if DWIDE > 1300 else "HD"))
		with open(skindatei) as tmpskin:
			self.skin = tmpskin.read()
		configparser = ConfigParser()
		configparser.read(CONFIGFILE)
		if configparser.has_section("settings"):
			l1 = configparser.items("settings")
			for k, v in l1:
				if k.strip() == "ansicht":
					ansicht = int(v)
				elif k == "schicht_col":
					conf["schicht_col"] = v
				elif k.strip() == "kalender_art":
					conf["kalender_art"] = v
				if k == "categories":
					cat_categories = v
					categories1 = list(cat_categories.split(","))
				elif k == "cat_color_list":
					cat_color_list = v
					color_list = list(cat_color_list.split(","))
				elif k == "z_liste":
					z_liste = list(v.split(","))  # not used
				else:
					conf[k] = v
		self.schichtnamen = None
		self.kalnum = 1
		schicht = str(conf["schicht_art"]).split(",")
		if len(schicht) < 4:
			schicht.extend(("0", "0", "0", "Schicht")[len(schicht):])
		conf["schicht_art"] = int(schicht[0])
		if conf["schicht_art"]:  # or conf["schicht_ics"] != _("None"):
			if not isinstance(conf["schicht_col"], dict):
				conf["schicht_col"] = eval(conf["schicht_col"])
			self.schichtnamen = []
			if isinstance(conf["schicht_col"], dict):
				for key in conf["schicht_col"].items():
					self.schichtnamen.append(key)
			self.schicht_bez = schicht[3]
		if len(color_list) < 21:
			color_list.extend(allcolor_list[len(color_list):])
		cal_bg = Farben().farb_re(color_list[12])
		color_inactiv = Farben().farb_re(color_list[15])
		rot = Farben().farb_re(color_list[16])
		weiss = Farben().farb_re(color_list[17])
		ansicht = 1
		self.session = session
		self.cards_on = conf["cards_on"]
		self.version = conf["version"]
		self.extern_color = conf["extern_color"]
		self.kalender_art = conf["kalender_art"]
		self.bgr_skin = conf["bgr_skin"]
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = "PlanerFS7"
		self.menutitle = ""
		wt = [(_("WN"), _("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Su"))]
		self["weekdays"] = List([])
		self["weekdays"].setList(wt)
		self["event_list"] = List([])
		self["calendar"] = List([])
		self["kwlist"] = List([])
		self["greena_1"] = Pixmap()
		self["greena_2"] = Pixmap()
		self["greena_2"].hide()
		self["errs"] = Pixmap()
		self["errs"].hide()
		self["help"] = ScrollLabel("")
		self["help"].hide()
		self.hlp = None
		self.ed_list = ["New event", ()]
		self.sel_dat = 0
		self.min_dat = 0
		self.list_site = 0
		self.eigen_events = []
		self.schichtlist = []
		self.color_holiday = color_list[11]
		self.color_days = color_list[10]
		self.cal_background = color_list[12]
		self.color_event = color_list[13]
		self.color_today = color_list[14]
		self.categories = categories1
		self.TitelTimer = eTimer()
		self.msp_liste = None
		self.TitelTimer.callback.append(self.setDatum)
		self.edit_index = None
		self["event_list"].onSelectionChanged.append(self.changed)
		self["event_list"].style = "notselected"
		self["description"] = Label("")
		self["titel"] = Label("PlanerFS - %s" % self.version)
		self.setTitle("PlanerFS - %s" % self.version)
		self["datum"] = Label('%0.2d.%0.2d.%0.4d %0.2d:%0.2d%s' % (lt[2], lt[1], lt[0], lt[3], lt[4], " " * 2))
		self["kal_num"] = Label(_("cal.1"))
		self["ueberschrift"] = Label("")
		self["key_yellow"] = Label(_("Timer"))
		self["key_green"] = Label(_("Update data"))
		self["key_red"] = Label(_("Terminlist"))  # (_("Import"))
		self["key_blue"] = Label(_("Today"))
		self["list_titel"] = Label(_("Terminlist"))
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
				"cancel": (self.exit, _("Close PlanerFS")),
				"ok": (self.edit_termin, _("Edit selected Termin")),
				}, -2)
		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
				"yellow": (self.yellow, _("Show timer")),
				"red": (self.red, _("Toggle Calender/Terminlist")),
				"green": (self.green, _("Update data")),  # internet import
				"blue": (self.blue, _("Show current month")),  #zum aktuellen Monat
				}, -2)
		self["DirectionActions"] = HelpableActionMap(self, "DirectionActions",
		{
				"left": self.left,
				"right": self.right,
				"down": self.down,
				"up": self.up,
				}, -2)
		self["EPGSelectActions"] = HelpableActionMap(self, "EPGSelectActions",
		{
				"prevBouquet": (self.Bouquet, _("Change calendar file")),
				"nextBouquet": (self.Bouquet, _("Change calendar file")),
				"info": (self.vcards, _("Show buisness card of selected name")),
				"input_date_time": (self.showMainMenu, _("Show more Options in Menu")),
				}, -2)

		self["MenuActions"] = HelpableActionMap(self, "MenuActions",
				{
						"menu": (self.showMainMenu, _("PlanerFSMenu"))
				}
		)
		self["MediaPlayerActions"] = HelpableActionMap(self, "MediaPlayerActions",
				{
						"previous": (self.rueck, _("previous month")),
						"next": (self.vor, _("next Month")),
						"subtitles": (self.vcards_list, _("Open adress book")),
				}, -1)
		self["MediaPlayerSeekActions"] = HelpableActionMap(self, "MediaPlayerSeekActions",
				{
				"seekFwd": (self.vor, _("next Month")),
				"seekBack": (self.rueck, _("previous month")),
				}, -1)
		self.today = date.today()
		altdat = datetime.today() - timedelta(conf["altloesch"])
		self.altdat = datetime(altdat.year, altdat.month, altdat.day, 23, 59, 59)
		self.monat = lt[1]
		self.jahr = lt[0]
		self.terminfile = ICSFILE
		if self.monat == 12:
			sdt1 = date(self.jahr + 1, 1, 1) - timedelta(1)
		else:
			sdt1 = date(self.jahr, self.monat + 1, 1) - timedelta(1)
		self.monatstage = int(sdt1.day)
		self.onLayoutFinish.append(self.start_set)

	def setDatum(self):
		lt = localtime()
		self["datum"].setText('%0.2d.%0.2d.%0.4d %0.2d:%0.2d%s' % (lt[2], lt[1], lt[0], lt[3], lt[4], " " * 2))
		self.TitelTimer.startLongTimer(60)

	def start_set(self):
		self.TitelTimer.startLongTimer(60)
		if self.bgr_skin:
			self.instance.setBackgroundColor(parseColor(self.cal_background))
			self["description"].instance.setBackgroundColor(parseColor(self.cal_background))
			self["ueberschrift"].instance.setBackgroundColor(parseColor(self.cal_background))
		if str(conf["ferien"]) != "0":
			online_import().run(str(conf["dat_dir"]), (conf["ferien"], conf["l_ferien"]), False)   #dat_dir
		self.einlesen()

	def info_ical(self):
		text = _("no icalendar import from system possible\nplease ask in the forum of your image how it can be installed")
		self.session.open(MessageBox, text, MessageBox.TYPE_INFO, close_on_any_key=True, timeout=15)

	def vcards(self):
		if not exists(VCFFILE):
			open(VCFFILE, "wb").close()
		if self["event_list"].getCurrent() is not None:
			name_x = self["event_list"].getCurrent()[3][1]
			geb = self["event_list"].getCurrent()[3][3]
			geb2 = "%s-%s-%s" % (geb.year, geb.month, geb.day)
			self.session.open(PFS_show_card7, name_x, geb2)

	def vcards_list(self):
		if not exists(VCFFILE):
			open(VCFFILE, "wb").close()
		if exists(VCFFILE):
			if self.cards_on:
				self.close(None)
			else:
				self.session.open(PFS_show_card_List7, "cal_on")

	def showMainMenu(self):
		if self.hlp:
			self.hlp = None
			self["help"].hide()
		if self.list_site == 1:
			if self["event_list"].getCurrent():
				if self["event_list"].getCurrent()[3]:
					extern = self["event_list"].getCurrent()[3][11]
					self.session.openWithCallback(self.menuCallback, PanerFS_menu7, extern)
			else:
				self.session.openWithCallback(self.menuCallback, PanerFS_menu7, 1)
		else:
			self.session.openWithCallback(self.menuCallback, PanerFS_menu7, 9)

	def menuCallback(self, menu_nr):
		if menu_nr is not None and menu_nr != "nix":
			if menu_nr == "fileHandling":
				self.fileHandling()
			elif menu_nr == "edit_termin":
				self.edit_termin()
			elif menu_nr == "delete_termin":
				self.delete_termin()
			elif menu_nr == "new_termin":
				self.new_termin()
			elif menu_nr == "config_start":
				self.config_start()
			elif menu_nr == "config_colors":
				self.config_colors()
			elif menu_nr == "import_termin":
				self.edit_termin()
			elif menu_nr == "Online_cal":
				self.online_cals()
			elif menu_nr == "Adress_cards":
				self.vcards_list()
			elif menu_nr == "about":
				self.showAbout()
			elif menu_nr == "info_ical":
				self.info_ical()
			elif menu_nr == "Setting_shifts":
				self.session.open(schicht_conf)
			elif menu_nr == "show_errors":
				text = ""
		if exists(ERRORLOG):
			if getsize(ERRORLOG) > 60:
				with open(ERRORLOG) as fp:
					text = fp.read()
			else:
				text = "Congratulation! no errors found"
		else:
			text = "File problem in /tmp!\nERRORLOG does not exist"
			with open(ERRORLOG, "w") as fp:
				fp.write("[PlanerFS] ERROR: %s\n" % text)
		self["help"].setText(text)
		self["help"].show()
		self.hlp = 1

	def showAbout(self, args=None):
		self.session.open(MessageBox, "planerFS", MessageBox.TYPE_INFO, close_on_any_key=True, timeout=3)

	def online_cals(self):
		self.session.openWithCallback(self.einlesen, PlanerFSonline_files)

	def fileHandling(self):
		self.session.openWithCallback(self.einlesen, PFS_filemenu7)

	def Bouquet(self):     #copy extern -> intern
		if self.kalnum == 1:
			self.kalnum = 2
			self["kal_num"].setText(_("cal.2"))
		else:
			self.kalnum = 1
			self["kal_num"].setText(_("cal.1"))
		self["description"].setText("")
		self.einlesen()

	def red(self):     #copy extern -> intern
		lt = self["list_titel"].getText().replace(_(" (active)"), "")
		if self.list_site == 0:
			self.list_site = 1
			self["event_list"].style = "default"
			self.changed()
			self["key_red"].setText(_("Calendar"))
			self["list_titel"].setText(lt + _(" (active)"))
			self["greena_1"].hide()
			self["greena_2"].show()
		else:
			self["ueberschrift"].setText("<<   %s %s   >>" % (self.monatsname, self.jahr))
			self["description"].setText("")
			self["list_titel"].setText(lt)
			self["event_list"].style = "notselected"
			self.list_site = 0
			self.showActiveDat()
			self["key_red"].setText(_("Terminlist"))
			self["greena_2"].hide()
			self["greena_1"].show()
			self["list_titel"].show()

	def green(self):  # liste alle dat-Termine bilden und senden
		erg = online_import().run("%sPlanerFS_online.txt" % conf["dat_dir"], (conf["ferien"], 9), True)
		if erg == 0:
			text = "%s\n/tmp/PlanerFS_Errors.txt" % _("Error: at least one external file could not be loaded!")
			self.session.open(MessageBox, text, MessageBox.TYPE_ERROR, close_on_any_key=True, timeout=3)
		elif erg == 2:
			self.session.open(MessageBox, _("Successfully loaded data"), MessageBox.TYPE_INFO, close_on_any_key=True, timeout=3)
		self.schichtfile = None
		self.einlesen()

	def cal_filesList(self):
		cal_files = []
		self.schichtfile = None
		if exists(CONFIGPATH):
			for cal_file in listdir(CONFIGPATH):
				if cal_file.endswith(".ics"):  # and cal_file != ICSNAME2 and cal_file != ICSNAME:
					cal_files.append("%s/%s" % (CONFIGPATH, cal_file))
		for cal_file in listdir(conf["cals_dir"]):
			if cal_file.endswith(".ics"):
				cal_files.append(conf["cals_dir"] + cal_file)
		if conf["dat_dir"] != CONFIGPATH:
			if exists(conf["dat_dir"]):
				for cal_file in listdir(conf["dat_dir"]):
					if cal_file.endswith(".ics"):
						cal_files.append(conf["dat_dir"] + cal_file)
		return cal_files

	def einlesen(self):  # planerFS-iCal Datei einlesen
		self.testdat = ''
		dataLines = []
		ica = None
		self.events = []
		self.eigen_events = []
		self.schichtlist = []
		self.events2 = []
		modu2 = True
		fileList = self.cal_filesList()
		if len(fileList) > 0:
			ica = []
			ica2 = []
			for file in fileList:
				if isfile(file):
					parse1 = Rules().parseEvent_b(file, self.schichtnamen)
					if parse1:
						tx_tsr = "%s2" % conf["cals_dir"]
						modu2 = False
						if ICSNAME2 in file or tx_tsr in file:
							ica2.extend(parse1)
						else:
							ica.extend(parse1)
					else:
						modu2 = True
				if modu2:
					with open(file, 'r') as tempFile:
						dataLines.append("filename: %s" % file)
						dataLines.extend(tempFile.readlines())
			if ica:
				self.readEvents1(ica, 1)
				if len(ica2):
					self.readEvents1(ica2, 2)
			if len(dataLines):
				self.readEvents(dataLines)
		else:
			self.liste_anzeigen()

	def readEvents1(self, ica, num=1):
		check = []
		for x in ica:
			ch2 = str((x[0], x[2]))
			if ch2 not in check:
				check.append(ch2)
				if conf["schicht_art"] and x[14]:
					in1 = None
					if ICSNAME in str(x[9]) or ICSNAME2 in str(x[9]):
						in1 = x
						self.eigen_events.append(x)
					self.schichtlist.append((x[0], x[2], x[3], x[5], x[6], in1, x[17]))
				else:
					if ICSNAME in str(x[9]) or ICSNAME2 in str(x[9]):
						self.eigen_events.append(x)
					if num == 2:
						self.events2.append(x)
					else:
						self.events.append(x)
		self.bew_feiert()
		self.liste_anzeigen()

	def readEvents(self, lines):
		mask = {}
		mask['BEGIN'] = compile(r"^BEGIN:VEVENT")
		mask['END'] = compile(r"^END:VEVENT")
		inEvent = False
		index = 0
		rname = ""
		fname = None
		fname2 = ""
		eventLines = []
		for line in lines:
			if 'filename' in line:
				fname = line.replace("filename:/etc/ConfFS/", "")
				rname = fname
			if "X-WR-CALNAME" in line:
				fname2 = line.replace("X-WR-CALNAME:", "")
			if mask['BEGIN'].match(line):
				eventLines = []
				inEvent = True
			elif mask['END'].match(line) and inEvent:
				if not fname:
					fname = fname2
				parse1 = Rules().parseEvent(eventLines, index, fname, self.schichtnamen).decode()
				if parse1:
					in1 = None
					if ICSNAME in rname or ICSNAME2 in rname:
						self.eigen_events.append(parse1)
					if conf["schicht_art"] and parse1[14]:
						in1 = None
						if ICSNAME in rname or ICSNAME2 in rname:
							in1 = parse1
						self.schichtlist.append((parse1[0], parse1[2], parse1[3], parse1[5], parse1[6], in1, parse1[17]))
					else:
						if ICSNAME2 in rname or "%s2" % conf["cals_dir"] in rname:
							self.events2.append(parse1)
						else:
							self.events.append(parse1)
						index += 1
				inEvent = False
			elif inEvent:
				eventLines.append(line)
		self.bew_feiert()
		self.liste_anzeigen()

	def liste_anzeigen(self):
		global msp_liste
		eventliste3 = []
		self.feiertagsliste = []
		self.term_liste = []
		self.term_liste5 = []
		self.termcol_liste = []
		self.cat_term_liste = []
		self.timerliste = []
		index = -1
		self.timer = 0
		jetzt = (self.jahr, self.monat)
		alist = self.events if self.kalnum == 1 else self.events2
		for x in alist:
#			x = [t.decode() if type(t) == bytes else t for t in x] Holger
			zaehler = 0
			if x[1] == "TIMER":
				continue
			next_datet = None
			next_datet = Next_Termin().next_termin(x[5], x[2], x[3], jetzt, 1, "planer", x[17])
			zeit = (x[2].hour, x[2].minute)
			zeit2 = (x[3].hour, x[3].minute)
			zeitges = 1
			if zeit[0] + zeit[1] + zeit2[0] + zeit2[1] == 0:
				zeit = None
				zeit2 = None
				zeitges = None
			elif zeit == zeit2:
				zeit2 = None
			repeat = 0
			for next_date in next_datet:
				if len(str(next_datet)) > 2:
					if x[5] == None:
						repeat = repeat + 1
						if zeitges and x[3].date() > x[2].date():
							zeit = None
							zeit2 = None
							if next_date == x[2]:
								zeit = (x[2].hour, x[2].minute)
							elif next_date.date() == x[3].date():
								zeit2 = (x[3].hour, x[3].minute)
					color = None
					eigen_num = 2
					if x[9] == ICSNAME or x[9] == ICSNAME2:
						eigen_num = 0
					if len(x) > 16:
						y = (next_date, x[0], x[1], x[2], x[3], x[4], x[5], self.jahr, x[6], x[7], x[8], eigen_num, x[9], x[10], zeit, index, zaehler, x[12], zeit2, x[13], repeat, x[11], x[15], x[16], x)
					else:
						y = (next_date, x[0], x[1], x[2], x[3], x[4], x[5], self.jahr, x[6], x[7], x[8], eigen_num, x[9], x[10], zeit, index, zaehler, x[12], zeit2, x[13], repeat, x[11], None, None, x)
					index += 1
					eventliste3.append(y)
					categories = str(x[1])
					if self.extern_color == "On" or eigen_num == 0:
						if x[1] == "HOLIDAY":
							self.feiertagsliste.append(next_date.day)
						cat_ind = 0
						for tmp in categories1:
							if categories and categories.find(tmp.strip()) != -1:
								color = color_list[cat_ind]
								break
							cat_ind += 1
						if not color:
							testtext = str(x[0]) + str(x[6])
							for c in categories1:
								if c.strip() in testtext:
									color = color_list[categories1.index(c)]
									break
						self.term_liste.append(date(next_date.year, next_date.month, next_date.day))
						self.term_liste5.append((date(next_date.year, next_date.month, next_date.day), x[0]))
						self.termcol_liste.append(color)
						zaehler += 1
			index += 1
		if self.kalender_art != "Off":
			self.bew_feiert()
			for x in self.bewegl_feiertage:
				next_date = None
				next_datet = Next_Termin().next_termin(x[5], x[2], x[3], jetzt, 1, "planer2")
				next_date = next_datet
				for next_date in next_datet:
					y = (next_date, x[0], x[1], x[2], x[3], None, None, self.jahr, x[6], 0, None, 1, "br", None, None, None, None, None, None, None, None, None, None, None)
					eventliste3.append(y)
					self.feiertagsliste.append(next_date.day)
		eventliste3.sort()
		monatsnamen = (_("January"), _("February"), _("March"), _("April"), _("May"), _("June"), _("July"), _("August"), _("September"), _("October"), _("November"), _("December"))
		self.monatsname = monatsnamen[self.monat - 1]
		self.timer = 0
		l_1 = []
		for x in eventliste3:
			if len(x) > 16:
				if x[16] == 0:
					l_1.append(x)
			else:
				l_1.append(x)
		self.eventliste3 = eventliste3
		l_2 = []
		for x in eventliste3:
			if x[20] is not None and x[2] != "TIMER" and (len(x) > 20 and x[20] < 2):
				color1 = weiss  # 0xFFFFFF #Farbe bei Nichtauswahl
				color2 = weiss
				text = x[1]
				alter1 = ""
				dat1 = '%0.2d.' % int(x[0].day)
				dat2 = ""
				rd = None
				if x[4].date() > x[3].date():
					rd = 1
					dat2 = ' (- %0.2d.%0.2d.)' % (int(x[4].day), int(x[4].month)) if int(x[4].month) != int(x[0].month) else ' - %0.2d.' % int(x[4].day)
				if rd:
					dat1 = dat1 + dat2
				else:
					if len(x) > 14:
						zeit = ""
						zeit2 = ""
						if x[14]:
							zeit = ' %0.2d:%0.2d ' % (x[14][0], x[14][1])
						if x[18]:
							zeit2 = '- %0.2d:%0.2d ' % (x[18][0], x[18][1])
						if len(zeit + zeit2):
							dat1 = dat1 + " " + zeit + zeit2
				dat1 = dat1 + " " * 2
				# fuer Geburts- und Jahrestage, Farbe festlegen und alter bestimmen
				categories = str(x[2]) + str(x[8])  # .upper()
				if _('Holiday').lower() in categories.lower():  # != -1 or categories.find('Holiday') != -1:
					text = text + ' (' + (_('Holiday')) + ')'
				else:
					tmp_al = 0
					cat_ind = 0
					for tmp in categories1:
						if categories and categories.find(tmp.strip()) != -1:
							if z_liste[cat_ind] == "1":
								tmp_al = 1
							break
						cat_ind += 1
					if tmp_al == 1:
						alter = x[7] - int(x[3].year)

						alter1 = ' (' + str(alter) + ')'
						if "dogage" in x[8].lower() and alter > 0:
							ha = 0
							if alter == 1:
								ha = 14
							elif alter == 2:
								ha = 22
							elif alter > 2:
								ha = 22 + (alter - 2) * 5
							alter1 = ' (' + str(alter) + " **" + str(ha) + ')'
						if alter % 10 == 0:
							color1 = rot
							color2 = rot
						elif alter % 5 == 0:
							color1 = 0x87CEEB
							color2 = 0x87CEEB
						else:
							color1 = weiss
							color2 = weiss
						text = text + alter1
				if x[9] > 0:
					text = text + ' (' + (_('Date Error')) + ')'
 				# ENDE: fuer Geburts- und Jahrestage, Farbe festlegen und alter bestimmen
				text = "* %s %s" % (dat1, text) if x[11] != 0 and x[11] != 3 else "  %s %s" % (dat1, text)
				l_2.append((text, color1, color2, x))
		self["event_list"].setList(l_2)
		self.setTitle("%s %s" % (self.monatsname, self.jahr))
		self["ueberschrift"].setText("<<   %s %s   >>" % (self.monatsname, self.jahr))
		msp_liste = []
		if (conf["schicht_art"] == 1 and self.kalnum == 1) or (conf["schicht_art"] == 2 and self.kalnum == 2):
			if len(self.schichtlist):
				msp_liste = schicht().parseSchicht(self.schichtlist, jetzt, "s1")
			elif msp:
				msp_liste = exporter((self.jahr, self.monat)).w_list
			if len(msp_liste) and len(msp_liste[0]) > 3:
				msp_liste.sort(key=lambda x: x[3])
		i = 1
		ir = 0
		kwliste = []
		d1 = date(self.jahr, self.monat, 1)
		d2 = d1.weekday()
		dt_list = [[], [], [], [], [], [], []]
		sel = 0
		self.min_dat = None  # -1
		for x in range(42):
			terms = []
			if (x + 7) % 7 == 0:
				ir += 1
			b_col = ""
			if self.cal_background:
				b_col = self.cal_background
			f_col = self.color_days
			if x >= d2 and i <= self.monatstage:
				sel += 1
				if not self.min_dat:
					self.min_dat = x - 1
				r = datetime(self.jahr, self.monat, i)
				wn1 = r.isocalendar()[1]
				if wn1 and not wn1 in kwliste:
					kwliste.append(wn1)
				if date(self.jahr, self.monat, i).weekday() == 6:
					f_col = self.color_holiday
				if i in self.feiertagsliste:
					f_col = self.color_holiday
				if date(self.jahr, self.monat, i) in self.term_liste:
					for term in self.term_liste5:
						if term[0] == date(self.jahr, self.monat, i):
							terms.append(term[1])
					b_col = self.color_event
					if self.termcol_liste[self.term_liste.index(date(self.jahr, self.monat, i))]:
						b_col = self.termcol_liste[self.term_liste.index(date(self.jahr, self.monat, i))]
				if date(self.jahr, self.monat, i) == date.today():
					b_col = self.color_today
				dt_list[ir].append((str(i), f_col, b_col, terms))
				i = i + 1
			else:
				dt_list[ir].append(("", f_col, self.cal_background, terms))
		if self.sel_dat == 0:
			self.sel_dat = date.today().day
		self.d_list = dt_list
		self.d2list = []
		msp_list = []
		for dat in dt_list:
			d_test = 0
			self.d3list = []
			msp_t_list = []
			if len(dat):
				for x in dat:
					if len(x):
						txt = str(x[0])
						if txt == '':
							txt = " "
						else:
							d_test = d_test + int(x[0])
						if conf["schicht_art"] and len(msp_liste):
							tp = msp_liste[0]
							if len(x[0]):
								tp = msp_liste[int(x[0]) - 1]
								msp_t_list.append(" ", Farben().farb_re(tp[2]), tp[1])  # int(tp[2].lstrip('#'), 16)
							else:
								msp_t_list.append(" ", Farben().farb_re(self.cal_background), tp[1])  # int(self.cal_background.lstrip('#'), 16))
						self.d3list.append(txt)
						self.d3list.append(Farben().farb_re(x[2]))  # (int(x[2].lstrip('#'), 16))
						self.d3list.append(Farben().farb_re(x[1]))  # (int(x[1].lstrip('#'), 16))
						if txt == " ":
							self.d3list.append(Farben().farb_re(self.cal_background))  # (int(self.cal_background.lstrip('#'), 16))
						elif int(self.sel_dat) == int(x[0]):
							self.d3list.append(0xffffff)
						else:
							self.d3list.append(0x000000)
				if d_test > 0:
					self.d2list.append(tuple(self.d3list))
					if conf["schicht_art"] and len(msp_t_list):
						msp_list.append(tuple(msp_t_list))
		self["calendar"].style = "default"
		self["calendar"].setList(self.d2list)
		if not exists(ERRORLOG):
			with open(ERRORLOG, "w") as fx:
				fx.write("errors-text wurde vor dem Start durch Fremdeinwirkung geloescht!\n\nDadurch sind Fehler in den Routinen nicht erkennbar")
		elif getsize(ERRORLOG) > 60:
			self["errs"].show()
		self["help"].hide()
		self.setKW(kwliste)
		self.showActiveDat()

	def setKW(self, kwliste):
		list1 = []
		for wn in kwliste:
			text = '%0.2d' % wn
			list1.append((text, 0))
		self["kwlist"].setList(list1)

	def termin_liste_anzeigen(self):
		timerliste2 = []
		index = 0
		stunde = 0
		minute = 0
		for x in self.events:
			if x[1] and x[1].upper() == "TIMER":
				if x[3]:
					stunde = x[2].hour
					minute = x[2].minute
				eigen = 1
				minu = (stunde * 60) + minute
				if x[9] == ICSNAME or x[9] == ICSNAME2:
					eigen = 0
				y = (minu, x[0], x[1], x[2], x[3], x[4], x[5], self.jahr, x[6], x[7], x[8], eigen, x[9], x[10], None, index, None, x[12], None, x[13], None, x[11], x[15], x)
				timerliste2.append(y)
			index += 1
		timerliste2.sort()
		l_2 = []
		for x in timerliste2:
			text = x[1].replace('\\n', ', ')
			color1 = weiss
			color2 = weiss
			if x[13] and x[13] == "no_activ":
				color1 = color_inactiv
				color2 = color_inactiv
			time = '%0.2d:%0.2d' % (x[3].hour, x[3].minute)
			text = " %s %s" % (time, text)
			if x[11] != 0 and x[11] != 3:
				text = "* %s" % text
			l_2.append((text, color1, color2, x))
		self.timer = 1
		self["event_list"].setList(l_2)
		self.setTitle("Timer-Liste")

	def bew_feiert(self):  # abarbeitung ob termin angezeigt wird
		self.bewegl_feiertage = ()
		if self.kalender_art == "Gregorian":
			self.bewegl_feiertage = Feiertage().ostern_greg(self.jahr)
		elif self.kalender_art == "Julian":
			self.bewegl_feiertage = Feiertage().ostern_jul(self.jahr)

	def vor(self):   # Termine heute
		if self.monat == 12:
			self.monat = 1
			self.jahr = self.jahr + 1
		else:
			self.monat = self.monat + 1
		if self.monat == 12:
			sdt1 = date(self.jahr + 1, 1, 1) - timedelta(1)
		else:
			sdt1 = date(self.jahr, self.monat + 1, 1) - timedelta(1)
		self.monatstage = int(sdt1.day)
		if self.monat == 1:
			self.bew_feiert()
		self["description"].setText("")
		self.sel_dat = 1
		self.liste_anzeigen()

	def rueck(self):   # Termine heute
		sdt1 = date(self.jahr, self.monat, 1) - timedelta(1)
		self.monatstage = int(sdt1.day)
		if self.monat == 1:
			self.monat = 12
			self.jahr = self.jahr - 1
		else:
			self.monat = self.monat - 1
			self.jahr = self.jahr
		if self.monat == 12:
			self.bew_feiert()
		self["description"].setText("")
		self.sel_dat = self.monatstage
		self.liste_anzeigen()

	def blue(self):
		self.today = date.today()
		self.monat = lt[1]
		self.jahr = lt[0]
		if self.monat == 12:
			sdt1 = date(self.jahr + 1, 1, 1) - timedelta(1)
		else:
			sdt1 = date(self.jahr, self.monat + 1, 1) - timedelta(1)
		self.monatstage = int(sdt1.day)
		self.bew_feiert()
		self["description"].setText("")
		self.sel_dat = date.today().day
		self.liste_anzeigen()

	def changed(self):
		kat = ""
		index = []
		if self["event_list"].getCurrent() is not None:
			index = self["event_list"].getCurrent()[3]
		if self["event_list"].getCurrent():
			description = ""  # None
			datum = ""
			zeit = ""
			location = ""
			kat = ""
			description = str(self["event_list"].getCurrent()[3][8]).replace("dogage", "")
			if description is None or not len(description):
				description = self["event_list"].getCurrent()[3][1]
			elif self["event_list"].getCurrent()[3][1] not in description:
				description = self["event_list"].getCurrent()[3][1] + ", " + description
			description = description.replace('\\n', ', ')
			kat1 = self["event_list"].getCurrent()[3][2]
			if self["event_list"].getCurrent()[3][2]:
				kat1 = self["event_list"].getCurrent()[3][2]
			if not kat1 or kat1 == "" or kat1 == "None":
				for tmp in categories1:
					if tmp.strip() in description != -1:
						kat1 = tmp.strip()
						description = description.replace(tmp.strip(), "")
			alter = ""
			if kat1 and len(kat1) and kat1 != "None" and kat1 != _("None"):
				cat_ind = 0
				for tmp in categories1:
					if kat1 and kat1.find(tmp.strip()) != -1 and z_liste[cat_ind] == "1":
						alter = " " + str(index[7] - int(index[3].year))
						break
					cat_ind += 1
				kat = " (" + _(kat1) + alter + ")"
			date = self["event_list"].getCurrent()[3][0]
			if self.timer == 0:
				kompl = self["event_list"].getCurrent()[3]
				days = (_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"), _("Friday"), _("Saturday"), _("Sunday"))
				day = date.weekday()
				day_name = days[day]
				datum = day_name + ", " '%0.2d' % int(date.day) + ". " + self.monatsname
				if len(kompl) > 19 and kompl[19] and len(str(kompl[19])):
					location = ", %s" % kompl[19]
				description = "%s%s: %s%s%s" % (datum, zeit, description, location, kat)
			self["description"].setText(description)

	def yellow(self,):   # Termine heute
		if self.list_site == 0:
			self.list_site = 1
			self["event_list"].style = "default"
			self["greena_1"].hide()
			self["greena_2"].show()
			self["key_red"].setText(_("Calendar"))
		if self.timer == 0:
			self.termin_liste_anzeigen()
			self["key_yellow"].setText(_("Events"))
			self["list_titel"].setText(_("Timer") + " (active)")
			self["ueberschrift"].setText("%s %s" % (self.monatsname, self.jahr))  # +" - "+_("Events"))
		else:
			self.liste_anzeigen()
			self["ueberschrift"].setText("%s %s" % (self.monatsname, self.jahr))  # +" - "+_("Event-List"))
			self["key_yellow"].setText(_("Timer"))
			self["list_titel"].setText(_("Terminlist") + " (active)")

	def left(self, num=None):
		if self.list_site == 1:
			self["event_list"].pageUp()
		else:
			if self.sel_dat == 1:
				self.rueck()
			else:
				self.sel_dat -= 1
				self.showActiveDat()

	def right(self, num=None):
		if self.list_site == 1:
			self["event_list"].pageDown()
		else:
			if self.sel_dat >= self.monatstage:
				self.vor()
			else:
				self.sel_dat += 1
				self.showActiveDat()

	def up(self, num=None):
		if self.list_site == 1:
			self["event_list"].selectPrevious()  # .up()
		else:
			if self.sel_dat == 1:
				self.rueck()
			else:
				self.sel_dat -= 7
				if self.sel_dat < 1:
					self.sel_dat = 1
			self.showActiveDat()

	def down(self, num=None):
		if self.list_site == 1:
			self["event_list"].selectNext()
		else:
			if self.sel_dat == self.monatstage:
				self.vor()
			else:
				self.sel_dat += 7
				if self.sel_dat > self.monatstage:  # self.max_dat:
					self.sel_dat = self.monatstage  # self.sel_dat-(7 * int(self.sel_dat/7))
			self.showActiveDat()

	def showActiveDat(self):
		self.d2list = []
		self.d3list = []
		msp_liste = []
		msp_color = None
		tp_txt = ""
		text = ""
		for dat in self.d_list:
			d_test = 0
			self.d3list = []
			if len(dat):
				for x in dat:
					if len(x):
						txt = x[0]
						if txt == '':
							txt = " "
						else:
							d_test = d_test + int(x[0])
						msp_color = None
						if conf["schicht_art"] and len(msp_liste):
							if txt != " ":
								tp = msp_liste[int(x[0]) - 1]
								msp_color = Farben().farb_re(tp[2])  # int(tp[2].lstrip('#'), 16)
							else:
								msp_color = Farben().farb_re(self.cal_background)  # int(self.cal_background.lstrip('#'), 16)
						self.d3list.append(txt)
						self.d3list.append(Farben().farb_re(x[2]))
						self.d3list.append(Farben().farb_re(x[1]))
						if txt == " ":
							self.d3list.append(Farben().farb_re(self.cal_background))
						elif int(self.sel_dat) == int(x[0]):
							self.d3list.append(0xffffff)
						else:
							self.d3list.append(0x000000)
						if conf["schicht_art"] and msp_color:
							self.d3list.append(msp_color)
				if d_test > 0:
					self.d2list.append(tuple(self.d3list))
		self["calendar"].style = "default"
		if msp_color:
			self["calendar"].style = "with_schicht"
		self["calendar"].setList(self.d2list)
		self.ed_list = [(_("Add new event"), (1, (self.sel_dat, self.monat, self.jahr), None, None))]
		if conf["schicht_art"] and len(msp_liste):
			le = msp_liste[int(self.sel_dat) - 1]
			tp_txt = str(le[1]).strip()
			tplus = ""
			if len(le) > 4 and le[4]:  # self.ed_list.append((tp_txt,le)) #and le[4] in self.eigen_events
				edt = le[4]
				zeit = (edt[2].hour, edt[2].minute)
				zeit2 = (edt[3].hour, edt[3].minute)
				ed2 = tuple(le[3], edt[0], edt[1], edt[2], edt[3], edt[4], edt[5], self.jahr, edt[6], edt[7], edt[8], 0, edt[9], edt[10], zeit, -1, edt[11], edt[12], zeit2, edt[13], 0)
				self.ed_list.append((tp_txt, ed2))
				if zeit != (0, 0) or zeit2 != (0, 0):
					tplus = " " + str(zeit[0]) + ":" + str(zeit[1]) + " - " + str(zeit2[0]) + ":" + str(zeit2[1])
				if edt[6] and edt[0] != edt[6]:
					tplus += " (" + str(edt[6]) + ")"
			if len(str(tp_txt)):
				tp_txt = self.schicht_bez + ": " + str(tp_txt) + tplus
		currdate = date(self.jahr, self.monat, self.sel_dat)
		for x in self.eventliste3:
			if self.sel_dat > 0 and date(x[0].year, x[0].month, x[0].day) == date(self.jahr, self.monat, self.sel_dat):
				kat = ""
				datum = ""
				zusatz = ""
				zeit = ""
				location = ""
				if len(x) > 19 and len(str(x[19])):
					location = ", %s" % x[19]
				if len(x) > 17 and x[17] != "ganztag":
					zeit2 = ""
					zeit1 = ""
					zeit1 = '%0.2d:%0.2d ' % (x[3].hour, x[3].minute)
					zeit2 = '%0.2d:%0.2d ' % (x[4].hour, x[4].minute)
					if x[4].date() > x[3].date():
						if date == x[3].date():
							zeit2 = " ..."
						elif date == x[4].date():
							zeit1 = "bis "
						else:
							zeit1 = "..."
							zeit2 = ""
					else:
						if zeit1 == zeit2:
							zeit2 = ""
						else:
							zeit1 = zeit1 + "- "
					zeit = " " + zeit1 + zeit2
				anz_text = x[8]
				if anz_text is None or anz_text == 0:
					anz_text = x[1]
				elif x[1] != anz_text:
					anz_text = "%s, %s" % (x[1], anz_text)
				kat1 = x[2].strip() if x[2] else None
				if not kat1 or kat1 == "" or kat1 == "None":
					for tmp in categories1:
						if tmp.strip() in anz_text != -1:
							kat1 = tmp.strip()
							anz_text = anz_text.replace(tmp.strip(), "")
				alter = ""
				if kat1 and kat1 != "" and kat1 != "None":
					cat_ind = 0
					for tmp in categories1:
						if kat1 and kat1.find(tmp.strip()) != -1 and z_liste[cat_ind] == "1":
							alter = " " + str(x[7] - int(x[3].year))
							break
						cat_ind += 1
					kat = " (%s%s)" % (_(kat1), alter)
				text = "%s%s%s%s%s\n" % (zeit, zusatz, anz_text, location, kat)
				self.ed_list.append((zusatz + x[1], x))
		days = (_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"), _("Friday"), _("Saturday"), _("Sunday"))
		day = currdate.weekday()
		day_name = days[day]
		datum = "%s, %0.2d. %s" % (day_name, currdate.day, self.monatsname)
		text = "%s: %s\n%s" % (datum, tp_txt, text.replace("dogage", ""))
		self["description"].setText(text)

	def config_start(self):
		self.session.openWithCallback(self.config_back, PlanerFSConfiguration)

	def config_back(self, a=None, b=None, c=None):
		if c == "restart":
			self.close(self.session, True)

	def config_colors(self):
		self.session.openWithCallback(self.config_back, PFS_categorie_conf7)

	def new_termin(self, datum=None):
		self.edit_index = None
		eigen_num = 0 if self.kalnum == 1 else 3
		self.session.openWithCallback(self.editliste, PFS_edit_Termin, None, eigen_num, datum)

	def edit_termin(self):
		if self.list_site == 1:
			if self["event_list"].getCurrent() is not None:
				index = self["event_list"].getCurrent()  # [3]
				if index and len(index) > 3:
					index = index[3]
					if len(index) > 11 and str(index[12]) == "br":
						text = _("Internal calculated holiday, import not possible") + "\n"
						self.session.open(MessageBox, text, type=MessageBox.TYPE_INFO, close_on_any_key=True, timeout=3)
					elif index[11] == 0 or index[11] == 3:
						self.edit_index = self.eigen_events.index(index[24]) + 1
						self.session.openWithCallback(self.editliste, PFS_edit_Termin, index)
					else:
						self.import_termin = index
						text = "\n%s\n%s\n%s" % (_("Termin from downloaded file"), index[12], _("external file can not be edited, Import this event?"))  # +self["event_list"].l.getCurrentSelection()[0][12]+"\n"
						self.session.openWithCallback(self.edit_antwort, MessageBox, text, MessageBox.TYPE_YESNO)
		else:
			self.session.openWithCallback(self.t_listCallback, ChoiceBox, title=_("Select for edit or new"), list=self.ed_list)

	def t_listCallback(self, choice):
		if choice is not None:
			if choice[1][0] == 1:
				self.new_termin(choice[1][1])
			elif choice[1][11] == 0 or choice[1][11] == 3:
				self.edit_index = self.eigen_events.index(choice[1][24]) + 1
				self.session.openWithCallback(self.editliste, PFS_edit_Termin, choice[1])
			else:
				self.import_termin = choice[1]
				text = "%s\n%s" % (_("Termin from downloaded file"), _("external file can not be edited, Import this event?"))  # +choice[1][12]
				self.session.openWithCallback(self.edit_antwort, MessageBox, text, MessageBox.TYPE_YESNO)

	def edit_antwort(self, answer=None):
		if answer and self.import_termin:
			g = self.import_termin
			if len(g) > 20:
				if g[11] == 0:
					text = "%s\n%s\n%s" % (_("Termin from downloaded file"), self.import_termin[12], _("Entry can only be copied from external to internal (*...)"))  # +self.import_termin[12]
					self.session.open(MessageBox, text, type=MessageBox.TYPE_INFO, close_on_any_key=True, timeout=3)
				else:
					self.edit_index = None
					neulist = (g[1], g[2], g[3], g[4], g[5], g[6], g[8], None, None, None, None, g[18], g[17], g[19])
					self.editliste(neulist, None)
		self.import_termin = None

	def editliste(self, neueintrag, loesch=None):
		if loesch and str(loesch) == "aktloesch":
			self.delete_termin()
		elif neueintrag:
			eventliste = self.eigen_events  # TerminList(0,self.terminfile).events
			if self.edit_index:  # and neueintrag[7] >=0:
				del eventliste[self.edit_index - 1]
			if loesch is None:
				eventliste.append(neueintrag)
			events = []
			ev_start = "BEGIN:VCALENDAR\nMETHOD:PUBLISH\nPRODID: -Enigma2-Plugin / PlanerFS " + self.version + "\nVERSION:2.0"
			events.append(ev_start)
			fname = ICSNAME if self.kalnum == 1 else ICSNAME2
			for x in eventliste:
				if x[9] is None or fname in str(x[9]):
					anzeige = ""
					comment = ""
					location = ""
					on = "\nBEGIN:VEVENT\n"
					off = "END:VEVENT"
					if x[12] != "Yes" and x[12] != "ganztag":
						start_dat = strftime("DTSTART;TZID=Europe/Berlin:%Y%m%dT%H%M%S\n", strptime(str(x[2]), "%Y-%m-%d %H:%M:%S"))
						end_dat = strftime("DTEND;TZID=Europe/Berlin:%Y%m%dT%H%M%S\n", strptime(str(x[3]), "%Y-%m-%d %H:%M:%S"))
					else:
						start_dat = strftime("DTSTART;VALUE=DATE:%Y%m%d\n", strptime(str(x[2]), "%Y-%m-%d %H:%M:%S"))
						end_dat = strftime("DTEND;VALUE=DATE:%Y%m%d\n", strptime(str(x[3]), "%Y-%m-%d %H:%M:%S"))
					self.altdatum = x[3]
					summary = "SUMMARY:" + x[0] + "\n"
					desc = x[6]
					if x[6] is None or x[6] == "":
						desc = x[0]
					desc = "%s:%s\n" % (_("Description-text"), desc)
					if len(x[13].strip() if x[13] is not None else ""):  # and x[13]!="ganztag":
						location = "LOCATION: %s\n" % x[13].strip()
					if str(x[4]) == "no_startscreen":
						location = location + "ACTION: %s\n" % x[4]
					if x[1] == "TIMER":
						anzeige = "BEGIN:VALARM\nACTION: %s\n\nTRIGGER;VALUE=DURATION:-PT1M\n%sEND:VALARM\n" % (x[4], desc)
					elif x[4] == "DISPLAY":
						anzeige = "BEGIN:VALARM\nACTION:DISPLAY\nTRIGGER;VALUE=DURATION:-P1D\n%sEND:VALARM\n" % desc
					cat = ""
					if x[1]:
						cat = "CATEGORIES:%s\n" % x[1].strip()
					# (freq, interval, byMonth, byMonthday, untilDate, byMinute, byHoure,byDay, byYearday, byWeekno, byWeekst)
					rule = ""
					if x[5] and x[5][0] is not None:
						self.altdatum = datetime.today() + timedelta(1)
						rule = "RRULE:FREQ=" + x[5][0]
						if x[5][1] is not None:
							rule = rule + ";INTERVAL=" + str(x[5][1])
						if x[5][2] is not None:
							rule = rule + ";BYMONTH=" + ', '.join([str(t) for t in x[5][2]])
						if x[5][7] is not None:
							rule = rule + ";BYDAY=" + ', '.join([str(t) for t in x[5][7]])
						if x[5][3] is not None:
							rule = rule + ";BYMONTHDAY=" + ', '.join([str(t) for t in x[5][3]])
						if x[5][4] is not None:
							self.altdatum = x[5][4]
							untile = strftime(";UNTIL=%Y%m%dT%H%M%S", strptime(str(x[5][4]), "%Y-%m-%d %H:%M:%S"))
							rule = rule + untile  # ";UNTIL="+str(x[5][4])
						if x[5][6] is not None:
							rule = rule + ";BYHOUR=" + str(x[5][6])
						if x[5][5] is not None:
							rule = rule + ";BYMINUTE=" + str(x[5][5])
						if x[5][8] is not None:
							rule = rule + ";BYYEARDAY=" + str(x[5][8])
						if x[5][9] is not None:
							rule = rule + ";BYWEEKNO=" + str(x[5][9])
						if x[5][10] is not None:
							rule = rule + ";BYWEEKST=" + str(x[5][10])
						if x[5][11] is not None:
							rule = rule + ";COUNT=" + str(x[5][11])
						rule = rule + "\n"
						comment = "COMMENT:%s\n" % (x[10] if x[10] else "")
					trigger = ""
					if len(x) > 14 and x[14]:
						trigger = "BEGIN:VALARM\nACTION:DISPLAY\n" + x[14] + "\nEND:VALARM\n"
					detailliste = on + start_dat + end_dat + summary + cat + rule + desc + anzeige + comment + location + trigger + off
					if conf["altloesch_on"] == "No":
						events.append(str(detailliste))
					else:
						if self.altdatum >= self.altdat:
							events.append(str(detailliste))
						else:
							continue
			events.append("\nEND:VCALENDAR")
			self.edit_index = None
			with open(conf["dat_dir"] + fname, "w") as f2:
				f2.writelines(events)
			self.einlesen()
		else:
			self.liste_anzeigen()

	def delete_termin(self):
		t = ""
		rule = None
		if self.edit_index is None:
			self.edit_index = self.eigen_events.index(self["event_list"].getCurrent()[3][24]) + 1
		dat = self.eigen_events[self.edit_index - 1]
		t = dat[0]
		rule = dat[5]
		text1 = "\n%s\n\n" % t
		if rule:
			self.session.openWithCallback(self.delete_termin_ok, MessageBox, _(text1 + _("Caution, this is a recurring appointment! Delete recurring appointment?")), MessageBox.TYPE_YESNO)
		else:
			self.session.openWithCallback(self.delete_termin_ok, MessageBox, _(text1 + _("Do you really want to delete this entry?")), MessageBox.TYPE_YESNO)

	def delete_termin_ok(self, answer=None):
		if answer:
			self.editliste(1, 1)

	def exit(self):
		if self.hlp:
			self.hlp = None
			self["help"].hide()
		else:
			self.close(None)

	def func_update_check(self, ans=None):
		pass


class PanerFS_menu7(Screen):
	skindatei = join(PLUGINPATH, "skin/%s/PFSmenulist.xml" % ("fHD" if DWIDE > 1300 else "HD"))
	with open(skindatei) as tmpskin:
		skin = tmpskin.read()

	def __init__(self, session, extern):
		Screen.__init__(self, session)
		self.skinName = "menulist7"
		self.session = session
		lista = []
		self["menulist"] = List([])
		nr = 0
		lista.append((str(nr + 1), " " + _("Insert new event / timer"), "new_termin"))
		if extern == 0 or extern == 3:
			lista.append(('1', " " + _("edit selected  entry"), "edit_termin"))
			lista.append(('2', " " + _("Delete selected  entry"), "delete_termin"))
			nr = 2
			lista.append((" ", "", "nix"))
		elif extern == 2:
			lista.append(('1', " " + _("Import selected  entry"), "import_termin"))
			nr = 1
			lista.append((" ", "", "nix"))
		lista.append((str(nr + 2), " " + "PlanerFS: " + _("parameters setting"), "config_start"))
		lista.append((str(nr + 3), " " + "PlanerFS: " + _("Color an category setting"), "config_colors"))
		lista.append((str(nr + 4), " " + _("Files Handling"), "fileHandling"))
		lista.append((str(nr + 5), " " + _("Edit online calendar list"), "Online_cal"))
		lista.append((str(nr + 6), " " + _("Open adress book"), "Adress_cards"))
		if conf["schicht_art"]:
			nr = nr + 1
			lista.append((str(nr + 6), " " + _("Setting shifts"), "Setting_shifts"))
		nr = nr + 1
		lista.append((str(nr + 7), " " + _("Show errors"), "show_errors"))
		lista.append((str(nr + 7), " " + _("About"), "about"))
		self.setTitle("PlanerFS: " + _("Menu"))
		self["menulist"].setList(lista)
		self["actions"] = NumberActionMap(["OkCancelActions", "ColorActions", "InputActions", "DirectionActions"],
		{
				"ok": self.run,
				"cancel": self.exit,
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				"5": self.keyNumberGlobal,
				"6": self.keyNumberGlobal,
				"7": self.keyNumberGlobal,
				"8": self.keyNumberGlobal,
				"9": self.keyNumberGlobal,
				#"0": self.keyNumberGlobal,
				#"red": self.autostart,
				#"green": self.setMainMenu,
				#"yellow": self.restore,
				#"blue": self.backup
		}, -1)

	def keyNumberGlobal(self, number):
		self["menulist"].setIndex(number - 1)
		self.run()

	def run(self):
		returnValue = self["menulist"].getCurrent()[2]
		if returnValue != "nix":
			self.close(returnValue)

	def exit(self):
		returnValue = None
		self.close(returnValue)
