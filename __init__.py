# -*- coding: utf-8 -*-
from gettext import bindtextdomain, dgettext, gettext
from os.path import join
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SYSETC

# PLUGIN-GLOBALS
CONFIGPATH = resolveFilename(SCOPE_SYSETC, "ConfFS/")
CONFIGFILE = join(CONFIGPATH, "PlanerFS.conf")
PLUGINPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/PlanerFS/")

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
