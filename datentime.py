import datetime

tod = '06/03/17 08:00'
today = datetime.datetime.strptime(tod, "%d/%m/%y %H:%M")
workingweek = [9,9,9,9,8,0,0]
timeframe = sum(workingweek)*2 #2 weeks working hours
OKtoprintweeks = 2
proceduralbuffer = 0.25
jobbuffer = 0.0
#todaytoprint = today+datetime.timedelta(days=OKtoprintweeks*7)

def HourstoDate(v):
	t = today
	while v >= workingweek[t.weekday()]:
		v -= workingweek[t.weekday()]
		t += datetime.timedelta(days=1)
	t += datetime.timedelta(hours=round(v,2))
	if t.hour>=12:
		t += datetime.timedelta(hours=1)
	return t

def DatetoHours(date):
	t = today
	v = 0.0
	while not (t.year==date.year and t.month==date.month and t.day==date.day):
	# while not str(t)[:10]==str(date)[:10]:
		v += workingweek[t.weekday()]
		t += datetime.timedelta(days=1)
	v += (date-t).total_seconds()/60.0/60.0
	if date.hour>12:
		v -= 1
	return v

def DateAbbr(date):
	return str(date)[11:13]+str(date)[14:16]+'+'+str((date-today).days)

def AbbrtoDate(abbr):
	hh = int(abbr[:2])
	mm = int(abbr[2:4])
	d = int(abbr[5:])
	t = today+datetime.timedelta(days=d)
	return datetime.datetime(t.year, t.month, t.day, hh, mm)

def NextWorkingDate(origt):
	def inWorkingHour():
		if t.weekday()<4 and ((t.hour>=8 and t.hour<12) or (t.hour==12 and t.minute==0) or (t.hour>=13 and t.hour<=17) or (t.hour==18 and t.minute==0)):
			return True
		elif t.weekday()==4 and ((t.hour>=8 and t.hour<12) or (t.hour==12 and t.minute==0) or (t.hour>=13 and t.hour<=16) or (t.hour==17 and t.minute==0)):
			return True
		else:
			return False

	t = origt
	while not inWorkingHour():
		t+=datetime.timedelta(days=1)
	if t==origt:
		return origt
	else:
		return datetime.datetime(t.year, t.month, t.day, 8, 0, 0)
			
	