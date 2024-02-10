# PYTHON IMPORTS
from configparser import ConfigParser
from os import remove
from os.path import exists, join

# ENIGMA IMPORTS
from enigma import getDesktop
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import getConfigListEntry, ConfigText, NoSave, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

# PLUGIN IMPORTS
from . import CONFIGPATH, CONFIGFILE, PLUGINPATH, _  # for localized messages


class PlanerFSonline_files(Screen, ConfigListScreen):
	skindatei = join(PLUGINPATH, "skin/%s/PFSconf.xml" % ("fHD" if getDesktop(0).size().width() > 1300 else "HD"))
	with open(skindatei) as tmpskin:
		skin = tmpskin.read()

	def __init__(self, session):
		self.path = join(CONFIGPATH, "PlanerFS_online.txt")
		self.cals_dir = "/tmp/"
		configparser = ConfigParser()
		if exists(CONFIGFILE):
			configparser.read(CONFIGFILE)
			if configparser.has_section("settings"):
				if configparser.has_option("settings", "cals_dir"):
					self.cals_dir = str(configparser.get("settings", "cals_dir"))
				if configparser.has_option("settings", "dat_dir"):
					path2 = str(configparser.get("settings", "dat_dir")) + 'PlanerFS_online.txt'
					if exists(path2):
						self.path = path2
		self.error = None
		self.list = []
		check_list = []
		self.onl_list2 = []
		self.index = ("", 9)
		if exists(self.path):
			with open(self.path, 'r') as fp:
				conf_lines = fp.readlines()
			for x in conf_lines:
				x = x.strip()
				fail = 0
				if len(x):
					aktiv = ""
					if x[0] == "#":
						x = x[1:]
						aktiv = "#"
					split = x.partition('=')
					kalnum = 1
					if len(split) == 3:
						try:
							kt = split[2].rpartition("=")  # .strip())
							kalnum = int(kt[2].strip())
							if kalnum < 0 or kalnum > 2:
								kalnum = 1
							url = kt[0].strip()
						except Exception:
							kalnum = 1
							url = split[2].strip()
						if url and not "name = url" in x:
							name = split[0].strip()
							if name in check_list:
								fail = 1
							check_list.append(split[0].strip())
							self.onl_list2.append((name, url, aktiv, fail, kalnum))
		self.altliste = self.onl_list2
		Screen.__init__(self, session)
		self.skinName = "PFSconf"
		ConfigListScreen.__init__(self, [], session=session, on_change=self.err)
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["key_yellow"] = Label(_("delete"))
		self["key_blue"] = Label(_("new"))
		self["help"] = Label("")  # (_("OK for editing, key 1 for activating/deactivating"))
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions", "HelpActions"],
				{
					"cancel": self.keyCancel,
					"ok": self.press_ok,
					"yellow": self.delet,
					"blue": self.new,
					"green": self.keySave,
					"red": self.keyCancel,
					'left': self.kn,
					'right': self.kn,
				}, -2
		)
		self["numactions"] = NumberActionMap(["InputActions"], {"1": self.keyNumberGlobal, }, -1)
		if not self.err in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.err)
		self.reloadList()
		self.setTitle("PlanerFS: " + _("online-calendars"))

	def keyNumberGlobal(self, number):
		en = self["config"].getCurrent()[3]
		if en in self.onl_list2:
			index = self.onl_list2.index(en)
			if en[2] == "#":
				en = (en[0], en[1], "", en[3], en[4])
			else:
				en = (en[0], en[1], "#", en[3], en[4])
			self.onl_list2[index] = en
			self.reloadList()

	def kn(self):
		if self["config"].getCurrent()[2] == 3:
			en = self["config"].getCurrent()[3]
			if en in self.onl_list2:
				index = self.onl_list2.index(en)
				knt = "1"
				if en[4] == "1":
					knt = "2"
				self.onl_list2[index] = (en[0], en[1], en[2], en[3], knt)
				self.reloadList()

	def new(self):
		self.index = ("new", 1)
		self.press_ok()

	def delet(self):
		rt = self["config"].getCurrent()
		if rt and len(rt) > 2 and rt[3] in self.onl_list2:
			nam = str(rt[3][4]) + str(rt[3][0])
			self.onl_list2.remove(rt[3])
			remove(self.cals_dir + nam + ".ics")
			self.reloadList()

	def press_ok(self, ans=None):
		if self.index[0] == "new":
			text1 = "new name"
		else:
			self.cur = self["config"].getCurrent()
			self.cur = self.cur and self.cur[1]
			if self["config"].getCurrent()[3] in self.onl_list2:
				self.index = (self.onl_list2.index(self["config"].getCurrent()[3]), self["config"].getCurrent()[2])
			text1 = str(self.cur.value)
		self.session.openWithCallback(self.texteingabeFinished, VirtualKeyBoard, title=_("Enter Text"), text=text1)

	def texteingabeFinished(self, ret):
		if ret:
			self.error = None
			ret = ret.strip()
			if self.index[0] != "new":
				en = self["config"].getCurrent()[3]
				aktiv = en[2]
			else:
				en = (ret, "new url", "", 0, 1)
				aktiv = ""
			if ret[0] == "#":
				ret = ret[1:]
				aktiv = "#"
			if en in self.onl_list2 or self.index[0] == "new":
				namefail = 0
				if self.index[1] == 1:
					if not len(ret) or ret == "new name":
						namefail = 1
					else:
						for x in self.onl_list2:
							if x[0] == ret and x[1] != en[1]:
								namefail = 1
					if namefail:
						self.session.openWithCallback(
							self.press_ok,
						   MessageBox, _("Name already exists or not allowed"), MessageBox.TYPE_ERROR)
					else:
						en = (ret, en[1], aktiv, en[3])
				elif self.index[1] == 2:
					en = (en[0], ret, en[2], en[3], en[4])
				if namefail == 0:
					if self.index[0] == "new":
						self.onl_list2.append((ret, "new url", aktiv, 0, 1))
					else:
						self.onl_list2[int(self.index[0])] = en
					self.reloadList()

	def reloadList(self):
		liste = []
		for x in self.onl_list2:
			tl = "name (inactiv)" if x[2] == "#" else "name"
			liste.extend((
						getConfigListEntry(tl, NoSave(ConfigText(default=x[0], fixed_size=False)), 1, x),
						getConfigListEntry("", NoSave(ConfigText(default=x[1], fixed_size=False)), 2, x),
						getConfigListEntry("zeige in Kalender", NoSave(ConfigSelection(choices=[("1", 1), ("2", 2)], default=x[4])), 3, x),
						getConfigListEntry(""),
						))
		self.list = liste
		self["config"].setList(self.list)

	def err(self):
		txt = ""
		cur = self["config"].getCurrent()[2]
		if self.error:
			txt = self.error
		else:
			if cur == 2 and self["config"].getCurrent()[3][1] == "new url":
				txt = _("not a valid URL!")
			elif cur == 1 or cur == 2:
				txt = _("Press OK for Edit, Press 1 for aktivate/deaktivate")
		self["help"].setText(txt)

	def cancelConfirm(self, result):
		if result:
			self.close()

	def keyCancel(self):
		self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"), MessageBox.TYPE_YESNO)

	def keySave(self):
		save_list = ["#internetadressen fuer online-Kalender\n", "# Aufbau:\n", "#    name = url\n", "#sample (delete # / entferne #) :\n"]
		for x in self.onl_list2:
			save_list.append(x[2] + x[0] + " = " + str(x[1]) + " = " + str(x[4]) + "\n")
			if x[2] == "#":
				remove(self.cals_dir + str(x[0]) + ".ics")
		self.okSave(save_list)

	def okSave(self, liste):
		with open(self.path, "w") as f:
			f.writelines(liste)
		if self.altliste != self.onl_list2:
			from PFSimport import online_import
			online_import().run(self.path, None, True)
		self.close()
