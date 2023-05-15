# PYTHON IMPORTS
from configparser import ConfigParser
from datetime import datetime, timedelta
from os.path import exists, isfile
from re import compile
from requests import get
from time import localtime, strftime, strptime

# PLUGIN IMPORTS
from . import _ # for localized messages
from .routines import Rules

version = ""
altloesch = 365
altloesch_on = "No"
CONFIGFILE = "'/etc/ConfFS/PlanerFS.conf'"
termindatei = "/etc/ConfFS/PlanerFS.ics"
cardfile = "/etc/ConfFS/PlanerFS.vcf"
cals_dir = "/tmp/"
if exists(CONFIGFILE):
	configparser = ConfigParser()
	configparser.read("/etc/ConfFS/PlanerFS.conf")
	if configparser.has_section("settings"):
		if configparser.has_option("settings", "version"):
			version = configparser.get("settings", "version")
		if configparser.has_option("settings", "altloesch_on"):
			altloesch_on = configparser.get("settings", "altloesch_on")
		if configparser.has_option("settings", "altloesch"):
			altloesch = configparser.get("settings", "altloesch")
		if configparser.has_option("settings", "cals_dir"):
			cals_dir = configparser.get("settings", "cals_dir")


class all_import():
	def run(self, imp_datei=None):
		self.ok = 0
		if imp_datei != None:
			list1 = []
			list2 = []
			if exists(CONFIGFILE):
				list1 = self.einles(termindatei)
			list2 = self.einles(imp_datei)
			if len(list2) > 0:
				list1.extend(list2)
				self.write_liste(list1)
		return self.ok

	def write_liste(self, liste):
		eventliste = liste
		events = []
		ev_start = "BEGIN:VCALENDAR\nMETHOD:PUBLISH\nPRODID: -EnigmaII-Plugin / PlanerFS " + version + "\nVERSION:2.0"
		events.append(ev_start)
		for x in eventliste:
			anzeige = ""
			comment = ""
			on = "\nBEGIN:VEVENT\n"
			off = "END:VEVENT"
			start_dat = strftime("DTSTART;TZID=Europe/Berlin:%Y%m%dT%H%M%S\n", strptime(str(x[2]), "%Y-%m-%d %H:%M:%S"))
			end_dat = strftime("DTEND;TZID=Europe/Berlin:%Y%m%dT%H%M%S\n", strptime(str(x[3]), "%Y-%m-%d %H:%M:%S"))
			self.altdatum = x[3]
			summary = "SUMMARY:" + x[0] + "\n"
			desc = x[6]
			if x[6] is None or x[6] == "":
				desc = x[0]
			desc = "DESCRIPTION:" + desc + "\n"
			if x[1] == "TIMER":
				anzeige = "BEGIN:VALARM\nACTION:" + str(x[4]) + "\nTRIGGER;VALUE=DURATION:-PT5M\n" + desc + "END:VALARM\n"
			elif x[4] == "DISPLAY":
				anzeige = "BEGIN:VALARM\nACTION:DISPLAY\nTRIGGER;VALUE=DURATION:-P1D\n" + desc + "END:VALARM\n"
			cat = "CATEGORIES:" + str(x[1]) + "\n"
#			(freq, interval, byMonth, byMonthday, untilDate, byMinute, byHoure,byDay, byYearday, byWeekno, byWeekst)
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
				rule = rule + "\n"
			if x[10] and x[10] != None:
				comment = "COMMENT:" + x[10] + "\n"
			detailliste = on + start_dat + end_dat + summary + cat + rule + desc + anzeige + comment + off
			if altloesch_on == "No":
				events.append(str(detailliste))
			else:
				if self.altdatum >= self.altdat:  # siehe PlanerFS.self.altdat = datetime(altdat.year, altdat.month, altdat.day, 23, 59, 59)
					events.append(str(detailliste))
				else:
					continue
		events.append("\nEND:VCALENDAR")
		with open(termindatei, "w") as f2:
			f2.writelines(events)
		self.ok = 1

	def einles(self, cal_datei):
		dataLines = []
		events = []
		if isfile(cal_datei):
			parse1 = Rules().parseEvent_b(cal_datei)
			for x in parse1:
				if x[5] or x[3].date() >= datetime.today():
					events.append(x)
		self.events = []
		mask = {}
		mask['BEGIN'] = compile(r"^BEGIN:VEVENT")
		mask['END'] = compile(r"^END:VEVENT")
		inEvent = False
		eventLines = []
		index = 0
		for line in dataLines:
			line = line.replace("\r", "")
			if mask['BEGIN'].match(line):
				eventLines = []
				inEvent = True
			elif mask['END'].match(line) and inEvent:
				parse1 = Rules().parseEvent(eventLines, index, "")
				events.append(parse1)
				inEvent = False
				index += 1
			elif inEvent:
				eventLines.append(line)
		return events


class vcf_import():
	def run(self, imp_datei=None):
		self.ok = 0
		if imp_datei != None:
			list1 = []
			list2 = []
			if exists(cardfile):
				list1 = self.einles(cardfile)
			list2 = self.einles(imp_datei)
			if len(list2) > 0:
				list1.extend(list2)
				with open(cardfile, "w") as f2:
					for x in list1:
						for x2 in x:
							f2.write(x2 + "\n")
				self.ok = 1
		return self.ok

	def einles(self, vcf_datei):
		dataLines = []
		if isfile(vcf_datei):
			with open(vcf_datei, 'rb') as tempFile:
				dataLines.extend(tempFile.readlines())
		cards1 = []
		if dataLines:
			mask = {}
			mask['umlaute'] = compile(r"(.*).*�������(.*).*")
			mask['BEGIN'] = compile(r"^BEGIN:VCARD")
			mask['END'] = compile(r"^END:VCARD")
			inCard = False
			cardLines = ["BEGIN:VCARD"]
			for line in dataLines:
				line = line.strip('\r\n')  # .replace("\r","")
				if mask['BEGIN'].match(line):
					cardLines = ["BEGIN:VCARD"]
					inCard = True
				elif mask['END'].match(line) and inCard:
					cardLines.append("END:VCARD")
					cards1.append(cardLines)
					inCard = False
				elif inCard:
					cardLines.append(line)
		return cards1


class online_import():
	def run(self, datei=None, fer=None, nofer=True):
		opath = '/etc/ConfFS/PlanerFS_online.txt'
		if datei and exists(datei):
			opath = datei
		onl_lines = []
		errmeld = None
		if nofer is True and exists(opath):
			with open(opath, 'r') as fp:
				onl_lines = fp.readlines()
		ferien = fer
		if ferien is None and nofer is False and exists(CONFIGFILE):
			configparser = ConfigParser()
			configparser.read("/etc/ConfFS/PlanerFS.conf")
			if configparser.has_option("settings", "ferien"):
				f1 = 0
				f2 = "0"
				f1 = int(configparser.get("settings", "ferien"))
				if configparser.has_option("settings", "l_ferien"):
					f2 = configparser.get("settings", "l_ferien")
				ferien = (f1, f2)
		if ferien and ferien[0]:
			jahr = localtime()[0]
			if int(ferien[1]) or (int(ferien[1]) == 0 and nofer is False):
				onl_lines.append("ferien" + " = https://www.schulferien.eu/downloads/ical4.php?land=" + str(ferien[0]) + "&type=1&year=" + str(jahr))
			if int(ferien[1]) == 9 or nofer is False:
				onl_lines.append("ferien2" + " = https://www.schulferien.eu/downloads/ical4.php?land=" + str(ferien[0]) + "&type=1&year=" + str(jahr + 1))
		self.ok = 0
		erg = 1
		if len(onl_lines):
			for x in onl_lines:
				x = x.strip()
				url = None
				datei2 = None
				kalnum = "1"
				if len(x) and not x.startswith("#"):
					spl = x.partition('=')
					if len(spl) == 3:
						kt = spl[2].rpartition("=")
						kn = int(kt[2].strip()) if kt[2].strip().isdigit() else kt[2].strip()
						if kn == 1 or kn == 2:
							kalnum = kn
							url = kt[0].strip()
						else:
							url = spl[2].strip()
						datei2 = "%s%s%s.ics" % (cals_dir, kalnum, spl[0].strip())
					if url:
						headers = {
								 'Accept': u"text/html,application/xhtml+xml,application/xml",
								 'User-Agent': u"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36",
								 'Accept-Encoding': u"gzip,deflate",
								 'Accept-Language': u"en-US,en;q=0.8"
								}
						resp = get(url, headers=headers, timeout=15, verify=False)
						status = resp.status_code
						if datei2 and status == 200:
							res = resp.content.decode("utf-8")
							with open(datei2, "w") as f:
								f.write(res)
							erg = 2
						else:
							errmeld = str(status) + "\n"
							erg = 0
						if errmeld:
							with open("/tmp/PlanerFS-Errors.txt", "a") as fx:
								fx.write("import1 read-error for: " + str(spl[0]) + "\n" + " " * 5 + str(url) + "\n" + " " * 5)
								fx.write(errmeld)
		return erg
