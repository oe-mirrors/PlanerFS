# PYTHON IMPORTS
from gettext import bindtextdomain, dgettext, gettext
from os.path import join

# ENIGMA IMPORTS
from enigma import getDesktop
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SYSETC

# PLUGIN-GLOBALS
VERSION = "10.0b"
DWIDE = getDesktop(0).size().width()
CONFIGPATH = resolveFilename(SCOPE_SYSETC, "ConfFS/")
CONFIGFILE = join(CONFIGPATH, "PlanerFS.conf")
PLUGINPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/PlanerFS/")
ICSNAME = "PlanerFS.ics"
ICSNAME2 = "PlanerFS2.ics"
VCFNAME = "PlanerFS.vcf"
ICSFILE = "%s/%s" % (CONFIGPATH, ICSNAME)
VCFFILE = "%s/%s" % (CONFIGPATH, VCFNAME)
ERRORLOG = "/tmp/PlanerFS-Errors.txt"
ONLINETEXT = join(CONFIGPATH, "PlanerFS_online.txt")
CONF = {
		"ext_menu": "True",
		"startscreen_plus": "True",
		"version": "",
		"plfs_list": "",
		"timer_on": "On",
		"akt_intv": "24",
		"startanzeige2": "systemstart",
		"timestartstandby": "No",
		"kalender_art": "Gregorian",
		"vorschaum": "3",
		"starttime": "None",
		"autosync": "No",
		"sec_file": "none",
		"cal_menu": "1",
		"adr_menu": "1",
		"l4l_on": "Yes",
		"l4l_lcd": "1",
		"l4l_screen": "1",
		"l4l_font": "40",
		"l_ferien": "0",
		"ferien": "0",
		"schicht_send_url": "None",
		"dat_dir": CONFIGPATH,
		"cals_dir": "/tmp/",
		"categories": "Keine,Geburtstag,Feiertag,Jahrestag,Hochzeitstag,Keine,Keine,Keine,Keine,Keine",
		"cat_color_list": "#00008B,#D2691E,#006400,#696969,#FFD700,#000000,#B22222,#8B8878,#CD0000,#00868B,#f0f8ff,#ff4500,#20343c4f,#deb887,#228B22,#5F9EA0,#DC143C,#F0F8FF,#EEC900",
		"z_liste": "0,1,0,1,1,0,0,0,0,0",
		}


def localeInit():
    bindtextdomain("PlanerFS", join(PLUGINPATH, "locale"))


def _(txt):
    t = dgettext("PlanerFS", txt)
    if t == txt:
        print("[PlanerFS] fallback to default translation for %s" % txt)
        t = gettext(txt)
    return t


localeInit()
language.addCallback(localeInit)
