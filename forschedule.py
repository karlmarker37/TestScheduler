import copy
from datentime import *
from machine import *
from orderm import PrintInformation
import time

def DecisionTree(dep, proc, fororders):
	def NextFinishtAllso(t):
		return min([so.EE[proc] for o in fororders for so in o.suborders if so.EE[proc]>t])

	def NextFinishtEldersib(t):
		return min([so.EE[proc] for so in fororders[oindex].suborders if so.EE[proc]>t])

	def Check(startt):
		if startt>timeframe:
			return startt,[]

		freem = [i for i in range(nummachine)]
		busyso = [so for o in fororders for so in o.suborders if (startt>=so.ES[proc] and startt<so.EE[proc])]
		for so in busyso:
			for m in so.machineused[proc]:
				try:
					freem.remove(m)
				except:
					pass
		# print 'entry\t',nextso.jo, proc, DateAbbr(HourstoDate(startt)), 'freem', freem
		if freem:
			if haveeldersib:
				if omused:
					if set(omused) & set(freem):
						mused = list(set(omused) & set(freem))
						if len(mused)<maxmachine:
							for m in freem:
								if len(mused)==maxmachine:
									break
								mused.append(m)
								mused = list(set(mused))
							# print 'exit 1\t',nextso.jo, proc, startt, 'maxm', maxmachine, mused	
							return startt, mused
						else: #len(omused)>=maxmachine
							# print 'exit 2\t', nextso.jo, proc, 'maxm', maxmachine, startt, mused
							return startt, mused
					else: #omused & freem = empty set
						if len(omused)<maxmachine:
							startt = NextFinishtAllso(startt)
							return Check(startt)
						else:
							try:
								startt = NextFinishtEldersib(startt)
							except ValueError:
								startt = NextFinishtAllso(startt)
							return Check(startt)
				else: #omused = empty set
					mused = []
					for i in range(maxmachine):
						if i<len(freem):
							mused.append(freem[i])
					return startt, mused

			else: #no eldersib
				if len(freem)<=maxmachine:
					mused = freem
					# print 'exit 3\t', nextso.jo, proc, 'maxm', maxmachine, startt, mused
					return startt, freem
				else:
					mused = freem
					for i in range(len(mused)-maxmachine):
						mused.pop(-1)
					# print 'exit 4\t', nextso.jo, proc, 'maxm', maxmachine, startt, mused
					return startt, freem
		else: #no freem
			if haveeldersib:
				if len(omused)<maxmachine:
					startt = NextFinishtAllso(startt)
					return Check(startt)
				else:
					try:
						startt = NextFinishtEldersib(startt)
					except ValueError:
						startt = NextFinishtAllso(startt)
					return Check(startt)
			else:
				startt = NextFinishtAllso(startt)
				return Check(startt)

	############################## Decision Tree starts ##############################

	if proc=='print':
		# wait for the completion of all sheeting
		prevproc = dep[0]
		nextts = [max([so.EE[prevproc] if so.ES[proc]<0 else -2 for so in o.suborders]) for o in fororders]
		#print [o.jo for o in fororders], [DateAbbr(HourstoDate(t)) for t in nextts]
		nextt, oindex = min((t,j) for j,t in enumerate(nextts) if t>=0)
		nextso, sindex = [(so,i) for i,so in enumerate(fororders[oindex].suborders) if so.ES[proc]<0][0]
		haveeldersib = 	int(nextso.jo[-2:])>0
		startt = nextt + proceduralbuffer

	elif proc=='fold':
		# 1 section dried -> start folding
		prevproc = dep[0]
		nextt,sindex,oindex = min([(so.EE[prevproc],i,j) for j,o in enumerate(fororders) for i,so in enumerate(o.suborders) if so.ES[proc]<0])
		nextso = fororders[oindex].suborders[sindex]
		startt = nextt + proceduralbuffer
		haveeldersib = 	int(nextso.jo[-2:])>0

	elif proc=='foldnip':
		prevproc = dep[0]
		try:
			startt,oindex = [(o.suborders[0].EE[proc],j) for j,o in enumerate(fororders) if o.sections>1 and o.suborders[0].EE[proc]>0 and o.suborders[1].EE[proc]<0][0]
			sindex = 1
			nextso = fororders[oindex].suborders[sindex]
		except IndexError:
			nextt,oindex,sindex = min([(o.suborders[i].EE[prevproc],j,i) for j,o in enumerate(fororders) for i in range(min(o.sections,2)) if o.suborders[i].ES[proc]<0])
			nextso = fororders[oindex].suborders[sindex]
			startt = DatetoHours(today)
		# startt = nextt + proceduralbuffer
		haveeldersib = 	int(nextso.jo[-2:])>0

	elif proc=='nip':
		# 1st or last section folded -> start nipping
		try:
			startt,oindex = [(o.suborders[0].EE[proc],j) for j,o in enumerate(fororders) if o.sections>1 and o.suborders[0].EE[proc]>0 and o.suborders[1].EE[proc]<0][0]
			sindex = 1
			nextso = fororders[oindex].suborders[sindex]
		except IndexError:
			nextt,oindex,sindex = min([(max([o.suborders[i].EE[prevproc] for prevproc in dep]), j, i) for j,o in enumerate(fororders) for i in range(min(2,o.sections)) if o.suborders[i].ES[proc]<0])
			nextso = fororders[oindex].suborders[sindex]
			startt = nextt + proceduralbuffer
		haveeldersib = 	int(nextso.jo[-2:])>0

	elif proc=='collate' or proc=='sew' or proc=='casein':
		# wait for the completion of all suborders
		nextt, oindex = min([(max([so.EE[dep[1]] if len(dep)>1 and so.EE[dep[1]]>0 else so.EE[dep[0]] for so in o.suborders]), j) for j, o in enumerate(fororders) if o.ES[proc]<0])
		startt = nextt + proceduralbuffer
		nextso = fororders[oindex]
		haveeldersib = 	False

	if haveeldersib:
		if proc=='foldnip':
			startt = fororders[oindex].suborders[sindex-1].EE[proc]
		else:
			startt = max([fororders[oindex].suborders[sindex-1].EE[proc]] + [nextso.EE[prevproc]+proceduralbuffer for prevproc in dep])

	omused = list(set([m for so in fororders[oindex].suborders for m in so.machineused[proc]]))
	nummachine	=	len(machines[proc])
	maxmachine = nextso.maxmachine[proc]
	startt, mused = Check(startt)

	return nextso, startt, mused

def ForSchedule(fororders, *args):
	def Trimtimeframe(proc):
		return
		for o in fororders:
			for so in o.suborders:
				if so.ES[proc]>timeframe:
					so.ES[proc] = timeframe
				if so.EE[proc]>timeframe:
					so.EE[proc] = timeframe
	
	################################ ForSchedule starts ################################
	if args:
		# Check if exactly the same
		oldfororders = args[0]
		if [o.jo for o in fororders] == [o.jo for o in oldfororders]:
			return oldfororders

	t0 = time.time()
	# SHEETING
	v = max(max(so.EE['sheet'] for o in fororders for so in o.suborders),0.0)
	for o in fororders:
		v += jobbuffer
		for i,so in enumerate(o.suborders):
			if so.ES['sheet']>=0:
				continue
			so.ES['sheet'] = v
			v = v+machines['sheet'][0].mr if i==0 else v
			v += so.sheets/machines['sheet'][0].c
			so.EE['sheet'] = v
			so.processtime['sheet'] = so.EE['sheet'] - so.ES['sheet']
			so.machineused['sheet'] = [0]
		o.machineused['sheet'] = [0]
	Trimtimeframe('sheet')

	t1 = time.time()
	# PRINTING
	allprinted = -1
	while allprinted<0:
		nextso, starttime, mused = DecisionTree(['sheet'], 'print', fororders)
		if mused:
			nextso.machineused['print'] = mused
			nextso.ES['print'] = starttime
			nextso.processtime['print'] = max(machines['print'][i].mr for i in mused) + nextso.sheets/sum(machines['print'][i].c for i in mused)
			nextso.EE['print'] = starttime + nextso.processtime['print']
		else:
			nextso.ES['print'] = timeframe+sum(workingweek)
			nextso.EE['print'] = timeframe+sum(workingweek)
			nextso.processtime['print'] = 0.0
		allprinted = min([so.ES['print'] for o in fororders for so in o.suborders])
	Trimtimeframe('print')

	t2 = time.time()
	# DRYING
	for o in fororders:
		for so in o.suborders:
			if so.EE['print']>timeframe:
				so.ES['dry'] = timeframe+sum(workingweek)
				so.EE['dry'] = timeframe+sum(workingweek)
				so.processtime['dry'] = 0.0
			elif so.ES['dry']<0:
				so.ES['dry'] = so.EE['print'] + proceduralbuffer
				dryenddate = HourstoDate(so.ES['dry'])
				dryenddate += datetime.timedelta(days=2)
				so.EE['dry'] = DatetoHours(NextWorkingDate(dryenddate))
				# so.processtime['dry'] = so.EE['dry'] - so.ES['dry']
	Trimtimeframe('dry')

	t3 = time.time()
	# FOLDING
	allfolded = -1
	while allfolded==-1:
		nextso, starttime, mused = DecisionTree(['dry'], 'fold', fororders)
		if mused:
			nextso.machineused['fold'] = mused
			nextso.ES['fold'] = starttime
			if nextso.jo[-2:]=='00':
				nextso.processtime['fold'] += max(machines['fold'][i].mr for i in mused)
			elif not nextso.ES['fold'] == [o.suborders[i-1] for o in fororders for i,so in enumerate(o.suborders) if so==nextso][0].EE['fold']: #if not nextso.ES[fold] == eldersib.EE[fold]
				nextso.processtime['fold'] += max(machines['fold'][i].mr for i in mused)
			nextso.processtime['fold'] += nextso.sheets/sum(machines['fold'][i].c for i in mused)
			nextso.EE['fold'] = starttime + nextso.processtime['fold']
		else:
			nextso.ES['fold'] = timeframe+sum(workingweek)
			nextso.EE['fold'] = timeframe+sum(workingweek)
			nextso.processtime['fold'] = 0.0
		allfolded = min(so.ES['fold'] for o in fororders for so in o.suborders)
	Trimtimeframe('fold')
	
	t4 = time.time()
	# FOLDNIP
	allfoldnipped = -1
	while allfoldnipped==-1:
		nextso, starttime, mused = DecisionTree(['fold'], 'foldnip', fororders)
		if mused:
			nextso.machineused['foldnip'] = mused
			nextso.ES['foldnip'] = starttime
			if nextso.jo[-2:]=='00':
				nextso.processtime['foldnip'] = max(machines['foldnip'][i].mr for i in mused)
			elif not nextso.ES['foldnip'] == [o.suborders[i-1] for o in fororders for i,so in enumerate(o.suborders) if so==nextso][0].EE['foldnip']: #if not nextso.ES[foldnip] == eldersib.EE[foldnip]
				nextso.processtime['foldnip'] = max(machines['foldnip'][i].mr for i in mused)
			nextso.processtime['foldnip'] += nextso.sheets/sum(machines['foldnip'][i].c for i in mused)
			nextso.EE['foldnip'] = starttime + nextso.processtime['foldnip']
		else:
			nextso.ES['foldnip'] = timeframe+sum(workingweek)
			nextso.EE['foldnip'] = timeframe+sum(workingweek)
			nextso.processtime['foldnip'] = 0.0
		allfoldnipped = min(o.suborders[i].ES['foldnip'] for o in fororders for i in range(min(o.sections,2)))
	Trimtimeframe('foldnip')

	t5 = time.time()
	# NIPPING
	allnipped = -1
	count = 0
	while allnipped==-1:
		nextso, starttime, mused = DecisionTree(['foldnip','fold'], 'nip', fororders)
		if mused:
			nextso.machineused['nip'] = mused
			nextso.ES['nip'] = starttime
			nextso.processtime['nip'] = nextso.sheets/machines['nip'][0].c if nextso.parent.sections>1 else nextso.sheets/machines['nip'][0].c*2
			nextso.processtime['nip'] += machines['nip'][0].mr
			nextso.EE['nip'] = starttime + nextso.processtime['nip']
		else:
			nextso.ES['nip'] = timeframe+sum(workingweek)
			nextso.EE['nip'] = timeframe+sum(workingweek)
			nextso.processtime['nip'] = 0.0
		allnipped = min(o.suborders[i].ES['nip'] for o in fororders for i in range(min(2,o.sections)))
	Trimtimeframe('nip')

	t6 = time.time()
	# COLLATING
	allcollated = -1
	while allcollated==-1:
		nexto, starttime, mused = DecisionTree(['fold','nip'], 'collate', fororders)
		if mused:
			nexto.machineused['collate'] = mused
			nexto.ES['collate'] = starttime
			if nexto.sections > 20:
				nexto.processtime['collate'] += 120/60.0
				nexto.processtime['collate'] += nexto.qty/1000
			elif nexto.sections > 10:
				nexto.processtime['collate'] += 90/60.0
				nexto.processtime['collate'] += nexto.qty/1500
			else:
				nexto.processtime['collate'] += 60/60.0
				nexto.processtime['collate'] += nexto.qty/2000
			nexto.EE['collate'] = starttime + nexto.processtime['collate']
		else:
			nexto.ES['collate'] = timeframe+sum(workingweek)
			nexto.EE['collate'] = timeframe+sum(workingweek)
			nexto.processtime['collate'] = 0.0
		nexto.CopytoSuborders('collate')
		allcollated = min(so.ES['collate'] for o in fororders for so in o.suborders)
	Trimtimeframe('collate')

	t7 = time.time()
	# SEWING
	allsewed = -1
	while allsewed==-1:
		nexto, starttime, mused = DecisionTree(['collate'], 'sew', fororders)
		if mused:
			nexto.machineused['sew'] = mused
			nexto.ES['sew'] = starttime
			nexto.processtime['sew'] += max(m.mr for m in machines['sew'])
			nexto.processtime['sew'] += nexto.sheets/sum(machines['sew'][i].c for i in range(len(nexto.machineused['sew'])))
			nexto.EE['sew'] = starttime + nexto.processtime['sew']
		else:
			nexto.ES['sew'] = timeframe+sum(workingweek)
			nexto.EE['sew'] = timeframe+sum(workingweek)
			nexto.processtime['sew'] = 0.0
		nexto.CopytoSuborders('sew')
		allsewed = min(so.ES['sew'] for o in fororders for so in o.suborders)
	Trimtimeframe('sew')

	t8 = time.time()
	# CASE-IN
	allcasein = -1
	while allcasein==-1:
		nexto, starttime, mused = DecisionTree(['sew'], 'casein', fororders)
		if mused:
			nexto.machineused['casein'] = mused
			nexto.ES['casein'] = starttime
			nexto.processtime['casein'] += max(m.mr for m in machines['casein'])
			nexto.processtime['casein'] += nexto.qty/sum(machines['casein'][i].c for i in range(len(nexto.machineused['casein'])))
			nexto.EE['casein'] = starttime + nexto.processtime['casein']
		else:
			nexto.ES['casein'] = timeframe+sum(workingweek)
			nexto.EE['casein'] = timeframe+sum(workingweek)
			nexto.processtime['casein'] = 0.0
		nexto.CopytoSuborders('casein')
		allcasein = min(so.ES['casein'] for o in fororders for so in o.suborders)
	Trimtimeframe('casein')

	t9 = time.time()
	# total time for each procedure
	for o in fororders:
		for i,proc in enumerate(machines):
			try:
				o.ES[proc] = min(so.ES[proc] for so in o.suborders if so.ES[proc]>=0)
			except:
				pass
			try:
				o.EE[proc] = max(so.EE[proc] for so in o.suborders if so.EE[proc]>=0)
			except:
				pass
			o.processtime[proc] = o.EE[proc] - o.ES[proc]
			o.machineused[proc] = list(set([m for so in o.suborders for m in so.machineused[proc]]))

	# print 'SH\t',t1-t0,'\t',
	# print 'PR\t',t2-t1,'\t',
	# print 'FO\t',t3-t2,'\t',
	# print 'DR\t',t4-t3,'\t',
	# print 'FN\t',t5-t4,'\t',
	# print 'NI\t',t6-t5,'\t',
	# print 'CO\t',t7-t6,'\t',
	# print 'SE\t',t8-t7,'\t',
	# print 'CA\t',t9-t8
	# PrintInformation(fororders)
	return fororders

def CalUT(orders):
	for o in orders:
		for so in o.suborders:
			for i,(k,m) in enumerate(machines.items()):
				if k=='collate' or k=='sew' or k=='casein':
					if so.ES[k] < timeframe:
						for mindex in so.machineused[k]:
							o.ut[k][mindex] = min(so.processtime[k], timeframe-so.ES[k])
				else:
					if so.ES[k] < timeframe:
						for mindex in so.machineused[k]:
							o.ut[k][mindex] += min(so.processtime[k], timeframe-so.ES[k])
	for o in orders:
		for i,(k,ms) in enumerate(o.ut.items()):
			o.ut[k] = [m/timeframe for m in ms]
	return sum(ut for o in orders for proc in o.ut.values() for ut in proc)/sum(len(m) for m in machines.values())