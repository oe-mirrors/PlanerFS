# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from gettext import bindtextdomain, dgettext, gettext

def localeInit():
    bindtextdomain("PlanerFS", resolveFilename(SCOPE_PLUGINS, "Extensions/PlanerFS/locale"))

def _(txt):
    t = dgettext("PlanerFS", txt)
    if t == txt:
        print("[PlanerFS] fallback to default translation for %s" % txt)
        t = gettext(txt)
    return t

localeInit()
language.addCallback(localeInit)
