import datetime, random
from collections import OrderedDict

from datentime import HourstoDate, DateAbbr, today
from machine import machines

from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class Order():
	qty,sheets = 0,0
	#order['pldate'] = datetime.datetime.strptime(row[5], date_format)
	drytime = 2*24.0
	totaltime, timetofinish, timetodue = 0.0,0.0,0.0
	status = ''
	progress = 0.0

	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)
		self.color = ''.join('%02x' %random.randint(50, 0xEE) for i in range(3))
		self.processtime = 	{'sheet':0.0, 	'print':0.0, 	'dry':0.0,	'fold':0.0, 	'foldnip':0.0,	'nip':0.0,	'collate':0.0,	'sew':0.0,	'casein':0.0}
		self.machineused =	{'sheet':[],	'print':[],		'dry':[],	'fold':[], 		'foldnip':[],	'nip':[],	'collate':[],	'sew':[],	'casein':[]}
		self.maxmachine = 	{'sheet':1, 	'print':1, 		'dry':0,	'fold':3, 		'foldnip':1,	'nip':1, 	'collate':1, 	'sew':2, 	'casein':1}
		if self.qty < 50000:
			self.maxmachine['fold'] = 1
		elif self.qty < 100000:
			self.maxmachine['fold'] = 2

		self.ut = OrderedDict()
		for i,(k,m) in enumerate(machines.items()):
			self.ut[k] = [0.0 for i in range(len(m))]

		#SUBORDERS
		self.suborders = []
		for i in ([0,self.sections-1]+range(1,self.sections-1) if self.sections>1 else range(1)):
			kwargs = {'parent':	self,
					'jo':	self.jo+'.0'+str(i) if i<10 else self.jo+'.'+str(i),
					'sheets':	int(self.qty),
					'qty':		int(self.qty),
					'siblings': self.sections,
					'maxmachine': self.maxmachine}
			so = SubOrder(**kwargs)
			self.suborders.append(so)

		self.ES = OrderedDict()
		self.EE = OrderedDict()
		self.LS = OrderedDict()
		self.LE = OrderedDict()
		for d in [self.ES, self.EE, self.LS, self.LE]:
			d['sheet'] = -1.0 
			d['print'] = -1.0
			d['dry'] = -1.0
			d['fold'] = -1.0
			d['foldnip'] = -1.0
			d['nip'] = -1.0
			d['collate'] = -1.0
			d['sew'] = -1.0
			d['casein'] = -1.0

		#TIME TO DUE
		hours = -8 #Start the first day at 8am
		t = today
		while t < self.rapdate:
			t+= datetime.timedelta(1)
			if t.weekday() < 4:
				hours+= 10
			elif t.weekday() < 5:
				hours+= 9
		self.timetodue = hours

	def CopytoSuborders(self, proc):
		for so in self.suborders:
			so.ES[proc] = 			self.ES[proc]
			so.EE[proc] = 			self.EE[proc]
			so.machineused[proc] =	self.machineused[proc]
			so.processtime[proc] =	self.processtime[proc]


class SubOrder(Order):
	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)
		self.processtime = {'sheet':0.0, 	'print':0.0, 	'dry':0.0,	'fold':0.0, 	'foldnip':0.0,	'nip':0.0,	'collate':0.0,	'sew':0.0,	'casein':0.0}
		self.machineused = {'sheet':[],		'print':[],		'dry':[],	'fold':[], 		'foldnip':[],	'nip':[],	'collate':[],	'sew':[],	'casein':[]}
		self.ES = OrderedDict()
		self.EE = OrderedDict()
		self.LS = OrderedDict()
		self.LE = OrderedDict()
		for d in [self.ES, self.EE, self.LS, self.LE]:
			d['sheet'] = -1.0 
			d['print'] = -1.0
			d['dry'] = -1.0
			d['fold'] = -1.0
			d['foldnip'] = -1.0
			d['nip'] = -1.0
			d['collate'] = -1.0
			d['sew'] = -1.0
			d['casein'] = -1.0

class SmalltimeLabel(Label):
	#font_size=sp(12)
	def __init(self, **kwargs):
		super(SmalltimeLabel, self).__init__(**kwargs)


class OrderInfoPanel(BoxLayout):
	def __init__(self, o, **kwargs):
		super(OrderInfoPanel, self).__init__(**kwargs)
		for so in o.suborders:
			b = BoxLayout()
			b.add_widget(Label(text=so.jo[-3:]))
			for i, (k,v) in enumerate(so.ES.items()):
				if k=='dry':
					continue
				if so.ES[k]==-1:
					b.add_widget(SmalltimeLabel(text='-'))
				else:
					es = HourstoDate(so.ES[k])
					b.add_widget(SmalltimeLabel(text=str(es)[11:13]+str(es)[14:16]+'+'+str((es-today).days)))
				if so.EE[k]==-1:
					b.add_widget(SmalltimeLabel(text='-'))
				else:
					ee = HourstoDate(so.EE[k])
					b.add_widget(SmalltimeLabel(text=str(ee)[11:13]+str(ee)[14:16]+'+'+str((ee-today).days)))
			b.add_widget(Label(text=str(so.machineused['print'])))
			b.add_widget(Label(text=str(so.machineused['fold'])))
			self.add_widget(b)

def PrintInformation(orders):
	for o in orders:
		for so in o.suborders:
			print so.jo,'\t',
			for i,(key,value) in enumerate(so.ES.items()):
				print DateAbbr(HourstoDate(so.ES[key])) if so.ES[key]>=0 else '','\t',
				print DateAbbr(HourstoDate(so.EE[key])) if so.ES[key]>=0 else '','\t',
				print round(so.processtime[key],2),'\t',
			print 'print\t',so.machineused['print'], '\tfold\t', so.machineused['fold']