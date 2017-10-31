import codecs, datetime

from orderm import Order, PrintInformation
from machine import machines

def ReadOrders(path):
	date_format = "%d/%m/%Y"
	# date_format = '%d-%b-%y'
	orders = []
	txt = codecs.open(path, encoding='utf-8')
	for line in txt:
		if line.split('\t')[0][0] == 'J':
			continue
		else:
			row = line.split('\t')
			kwargs={'jo':			row[0],
					'qty':			int(row[1]),
					'sections':		int(row[2]),
					'sheets':		int(row[3]),
					'incomedate':	datetime.datetime.strptime(row[4], date_format),
					'rapdate':		datetime.datetime.strptime(row[5], date_format), 
					'pldate':		datetime.datetime.strptime(row[6], date_format)}
			o = Order(**kwargs)
			finishedprocess = row[7].replace('\r\n','').split(',')
			#for proc in machines:
			for proc in finishedprocess:
				if proc=='none':
					break
				o.ES[proc] = 0.0
				o.EE[proc] = 0.0
				o.CopytoSuborders(proc)
			orders.append(o)
	return orders