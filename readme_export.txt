

Programmcode:

	from Plugins.Extensions.PlanerFS.PFShmexp import hm_exp
	PlanerFS_files=hm_exp().get_calfiles()
        PlanerFS=hm_exp().get_caldates() 
	termine=hmt[0]
	timer=hmt[1]
	
Ende Programmcode

Hinweise
Varianten:
	get_caldates() -> by the end of next month, all files
	get_caldates(3) -> 3 months, all files
	get_caldates(2."/mypath/my_file")  -> 2 months, ical-file with path


Ausgaben:

PlanerFS_files
	(Name,ical-file with path)

termine liefert:
	((2018, 7, 5), 'test', datetime.datetime(2018, 7, 5, 15, 30), datetime.datetime(2018, 7, 5, 15, 30), 'test', datetime.datetime(2018, 7, 5, 15, 30))
	akt dat als tuple, Summary,ical-start,ical-ende,Description, akt termin-dat 


timer liefert (zwei Tage, wenn Kategorie 'timer' oder VALARM DISPLAY):
	('Ztest2', 'timer', datetime.datetime(2018, 6, 28, 9, 40), (9, 40), datetime.datetime(2018, 6, 12, 9, 40), datetime.datetime(2018, 6, 14, 9, 50))
	('Ztest', 'DISPLAY', datetime.datetime(2018, 7, 15, 11, 0), (11, 0), datetime.datetime(2018, 7, 15, 12, 0), datetime.datetime(2018, 7, 15, 14, 0))
	Summary, art (Display von ical, Timer wenn Kategorie timer), Alarm-dat, Alarm als Uhrzeit-tuple, ical-start, ical-ende