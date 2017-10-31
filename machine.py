from collections import OrderedDict

class Machine():
	def __init__(self, c, mr):
		self.broken = 0
		self.c = c
		self.mr = mr
		self.status = 'idle'

machines = OrderedDict()
machines['sheet'] = 	[Machine(c=16580.0,mr=10/60.0)]
machines['print'] = 	[Machine(c=5646.0, mr=42/60.0),	Machine(c=5530.0, mr=36/60.0)]
machines['dry'] = 		[]
machines['fold'] = 		[Machine(c=4200.0, mr=30/60.0),	Machine(c=4200.0, mr=30/60.0), Machine(c=4200.0, mr=30/60.0)]
machines['foldnip'] = 	[Machine(c=4200.0, mr=30/60.0)]
machines['nip'] = 		[Machine(c=2114.0, mr=60/60.0)]
machines['collate'] = 	[Machine(c=None,   mr=None)]
machines['sew'] = 		[Machine(c=5500.0, mr=40/60.0), Machine(c=5500.0, mr=40/60.0)]
machines['casein'] = 	[Machine(c=848.0,  mr=90/60.0)]