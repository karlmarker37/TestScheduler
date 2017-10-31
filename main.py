import sys, time, copy, datetime, threading, random, multiprocessing
from operator import attrgetter
from functools import partial
from collections import OrderedDict, defaultdict
from itertools import permutations, product, combinations
from os.path import sep, expanduser, isdir, dirname

import kivy
kivy.require('1.9.0')
from kivy.app import App
from kivy.lang import Builder
from kivy.utils import platform
from kivy.logger import Logger

from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import *

# from kivy.garden.filebrowser import FileBrowser
from filebrowser import FileBrowser

from kivy.properties import StringProperty,BooleanProperty,ListProperty,ObjectProperty,NumericProperty

from kivy.clock import Clock, mainthread
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp

from kivy.config import Config
Config.set('kivy','log_level', 'warning')
Config.write()

from machine import *
from datentime import *
from exporter import Exporter
from floatinput import FloatInput
from orderm import PrintInformation, OrderInfoPanel
from db import ReadOrders
from forschedule import ForSchedule, CalUT

transparent =	[  0,  0,  0,  0]
elite = 		[ .5,  0,  0, .8]
gold = 			[ .5, .4, .2, .8]
silver = 		[.25,.25,.25, .8]
lightblue = 	[  0, .4, .6, .8]
purple = 		[ .6, .2, .6, .8]
blue = 			[  0,  0,.75, .8]

###################################################################### MINOR LAYOUTS ######################################################################

class TopbarButton(Button):
	def __init__(self, **kwargs):
		super(TopbarButton, self).__init__(**kwargs)

	def on_release(self):
		for btn in self.parent.children:
			if type(btn).__name__ == 'TopbarButton':
				btn.background_color = [1, 1, 1, 1]
		self.background_color = elite
		
class TitleButton(Button):
	def __init__(self, **kwargs):
		super(TitleButton, self).__init__(**kwargs)
		self.background_color = lightblue

	def on_touch_down(self, touch):
		if self.collide_point(*touch.pos):
			touch.grab(self)

	def on_touch_up(self, touch):
		if touch.grab_current is self:
			touch.ungrab(self)

class ContentButton(Button):
	def __init__(self, **kwargs):
		super(ContentButton, self).__init__(**kwargs)
		self.background_color = transparent

	def on_touch_down(self, touch):
		if self.collide_point(*touch.pos):
			touch.grab(self)
			try:
				callback = partial(app.OrderInfo, self, touch)
				Clock.schedule_once(callback, 1)
				touch.ud['event'] = callback

				#CHANGE COLOR
				index = self.parent.children.index(self)
				index = index-index%(self.parent.cols)+self.parent.cols-1
				for btn in self.parent.children:
					btn.background_color = transparent
				for x in range(index, index-self.parent.cols, -1):
					self.parent.children[x].background_color = gold if self.parent.children[x].background_color==transparent else transparent
			except:
				pass

	def on_touch_up(self, touch):
		if touch.grab_current is self:
			if self.text=='..':
				app.OrderStatus(self)
			touch.ungrab(self)
			try:
				Clock.unschedule(touch.ud['event'])
				app.orderinfopopup.dismiss()
			except:
				pass

class Slide0Header(BoxLayout):
	def __init__(self, **kwargs):
		super(Slide0Header, self).__init__(**kwargs)

class Slide1Header(BoxLayout):
	def __init__(self, **kwargs):
		super(Slide1Header, self).__init__(**kwargs)

class SettingsContents(BoxLayout):
	jbuffer = StringProperty()
	pbuffer = StringProperty()
	permsreport = StringProperty()
	qoffset = StringProperty()
	soffset = StringProperty()
	roffset = StringProperty()
	LNSmax = StringProperty()
	timelimit = StringProperty()
	def __init__(self, **kwargs):
		super(SettingsContents, self).__init__(**kwargs)
		self.jbuffer = str(jobbuffer)
		self.pbuffer = str(proceduralbuffer)
		self.permsreport = app.permsreport
		self.qoffset = str(app.qtyoffset)
		self.soffset = str(app.sectionsoffset)
		self.roffset = str(app.rapdateoffset)
		self.LNSmax = str(app.LNSmax)
		self.timelimit = str(app.timelimit)

	def ApplySettings(self):
		jobbuffer 			= float(self.ids.setjbuffer.text)
		proceduralbuffer 	= float(self.ids.setpbuffer.text)
		app.permsreport 	= self.ids.setpermsreport.text
		app.qtyoffset		= int(self.ids.setqoffset.text)
		app.sectionsoffset	= int(self.ids.setsoffset.text)
		app.rapdateoffset	= int(self.ids.setroffset.text)
		app.LNSmax			= int(self.ids.setlnsmax.text)
		app.timelimit 		= float(self.ids.settimelimit.text)
		app.settingspopup.dismiss()

class AddPanel(BoxLayout):
	def Submit(self):
		app.addpopup.dismiss()
		app.UpdateSlide0()
		app.UpdateSlide1()
	def __init__(self, **kwargs):
		super(AddPanel, self).__init__(**kwargs)

class Navigator(BoxLayout):
	def __init__(self, **kwargs):
		super(Navigator, self).__init__(**kwargs)

###################################################################### MP EVAL ######################################################################
def Evaluate(*args):
	candidate = args[0]
	fororders = ForSchedule(copy.deepcopy(candidate))
	avgut = CalUT(fororders)
	return (avgut, candidate)

def MP(i):
	print '-'*35,app.neighbourhoods[i][0],'-'*35

	# MP.PROCESS
	# perms = app.neighbourhoods[i][1]()
	# head,tail = 0,0
	# jobs = []
	# cpus = multiprocessing.cpu_count()
	# for process in range(cpus-1):
	# 	tail+=int(len(perms)/cpus)
	# 	jobs.append(multiprocessing.Process(target=Evaluate, args=(perms[head:tail],)))
	# 	head=tail
	# jobs.append(multiprocessing.Process(target=Evaluate, args=(perms[head:],)))
	# for j in jobs:
	# 	j.start()
	# for j in jobs:
	# 	j.join()

	# MP.POOL
	avgut = 0.0
	bestperm = []
	workers = multiprocessing.Pool(multiprocessing.cpu_count())
	try:
		(avgut,bestperm) = max(workers.map(Evaluate,app.neighbourhoods[i][1]()))
		workers.close()
		workers.join()
	except:
		return

	if avgut>app.bestut:
		app.selectedorders = [bestperm]
		app.bestut=avgut
		print [o.jo if len(o.jo)<5 else o.jo[-4:] for o in bestperm], round(app.bestut*100,4),'%'
	elif avgut==bestut:
		app.selectedorders.append(bestperm)
		for perm in app.selectedorders:
			print [o.jo if len(o.jo)<5 else o.jo[-4:] for o in bestperm], round(app.bestut*100,4),'%'
	app.orders = app.selectedorders[0]



###################################################################### MAIN INIT ######################################################################
class TestScheduler(App):
	def build(self):
		self.PreBuildInit()
		self.sm.add_widget(self.AddSlide0())
		self.sm.add_widget(self.AddSlide1())
		self.sm.add_widget(self.AddSlide2())

		self.navboard = Navigator()
		self.navboard.ids.nd.add_widget(self.NavPanel())
		self.navboard.ids.nd.add_widget(self.sm)

		board = BoxLayout(orientation='vertical')
		board.add_widget(self.Topbar())
		board.add_widget(self.navboard)	
		self.PostBuildInit()	
		return board

	def PreBuildInit(self):
		self.sm = ScreenManager(transition=SwapTransition())
		# CALCULATIONS PARA
		self.drydays = 2
		self.LNSmax = 500
		self.qtyoffset = 2000
		self.sectionsoffset = 2
		self.rapdateoffset = 7
		self.permsreport = 'None'
		self.orderpath = './ORDERS_10.txt'
		self.orders = ReadOrders(self.orderpath)
		# CALCULATIONS VAR
		self.signal = 'run'
		self.neighbourhoods = [
		(' Random ',	partial(self.neighbours_random, num=100)),
		('Swapping', 	self.neighbours_swap),
		('LNS (3) ', 	partial(self.neighbours_LNS, size=3)),
		('LNS (4) ', 	partial(self.neighbours_LNS, size=4)),
		('Idle (4)', 	partial(self.neighbours_idle, size=4)),
		('Idle (5)', 	partial(self.neighbours_idle, size=5))
		]
		self.strategytime = [0.0 for i in range(len(self.neighbourhoods))]
		self.strategyimpr = [0.0 for i in range(len(self.neighbourhoods))]
		self.pausetime = 0.0
		self.bestut = 0.0
		self.selectedorders = []

	def PostBuildInit(self):
		l = len(self.orders)
		if l<=5:
			self.timelimit = 0.1
		elif l<=10:
			self.timelimit = 5
		elif l<=15:
			self.timelimit = 15
		elif l<=20:
			self.timelimit = 45
		elif l<=40:
			self.timelimit = 90
		else:
			self.timelimit = 120
	###################################################################### MAIN LAYOUTS ######################################################################
	def Topbar(self):
		topbar = BoxLayout(size_hint_y=.15)
		topbarmain = TopbarButton(text='Main', on_release=partial(self.ChangeScreen,0), background_color=elite)
		topbarfor = TopbarButton(text='Forward Schedule', on_release=partial(self.ChangeScreen,1))
		topbarback = TopbarButton(text='Backward Schedule', on_release=partial(self.ChangeScreen,2))

		topbar.add_widget(Button(text='=', on_press=lambda i: self.navboard.ids.nd.toggle_state(), size_hint_x=.3))
		topbar.add_widget(topbarmain)
		topbar.add_widget(topbarfor)
		topbar.add_widget(topbarback)
		topbar.add_widget(Button(text='|>', on_release=self.StartTH, size_hint_x=.3))
		return topbar

	def AddSlide0(self):
		slide0container = BoxLayout(orientation='vertical')
		self.slide0 = GridLayout(cols=8, row_default_height=50,size_hint_y=None)
		self.slide0.bind(minimum_height=self.slide0.setter('height'))
		slide0scroll = ScrollView()
		slide0scroll.add_widget(self.slide0)
		slide0container.add_widget(Slide0Header())
		slide0container.add_widget(slide0scroll)
		self.UpdateSlide0()
		
		slide0sm = Screen(name='slide0')
		slide0sm.add_widget(slide0container)
		
		return slide0sm

	def UpdateSlide0(self):
		self.slide0.clear_widgets()
		for o in self.orders:
			self.slide0.add_widget(ContentButton(text=o.jo))
			self.slide0.add_widget(ContentButton(text=str(o.qty)))
			self.slide0.add_widget(ContentButton(text=str(o.sections)))
			self.slide0.add_widget(ContentButton(text=str(o.sheets)))
			self.slide0.add_widget(ContentButton(text=str(o.rapdate)[:10]))
			self.slide0.add_widget(ContentButton(text=str(round(o.timetodue,2))))
			self.slide0.add_widget(ContentButton(text=''))
			self.slide0.add_widget(ContentButton(text='..'))

	def AddSlide1(self):
		slide1container = BoxLayout(orientation='vertical')
		self.slide1 = GridLayout(cols=9, row_default_height=50,size_hint_y=None)
		self.slide1.bind(minimum_height=self.slide1.setter('height'))
		slide1scroll = ScrollView()
		slide1scroll.add_widget(self.slide1)
		slide1container.add_widget(Slide1Header())
		slide1container.add_widget(slide1scroll)
		self.UpdateSlide1()

		slide1sm = Screen(name='slide1')
		slide1sm.add_widget(slide1container)
		return slide1sm

	def UpdateSlide1(self):
		self.slide1.clear_widgets()
		for o in self.orders:
			self.slide1.add_widget(ContentButton(text=o.jo))
			for i,(key,value) in enumerate(o.ES.items()):
				if key=='dry' or key=='foldnip':
					continue
				self.slide1.add_widget(ContentButton(text=DateAbbr(HourstoDate(value)) if value>=0 else '-'))
			self.slide1.add_widget(ContentButton(text=DateAbbr(HourstoDate(o.EE[key])) if o.EE[key]>=0 else '-'))

	def AddSlide2(self):
		slide2 = Screen(name='slide2', size_hint=(.5,.5))
		return slide2

	def ChangeScreen(self, i, btn):
		self.sm.current = 'slide'+str(i)

	def NavPanel(self):
		navpanel = BoxLayout(orientation='vertical')
		navpanel.add_widget(Button(text='Add'))#, on_release=self.AddPopup))
		navpanel.add_widget(Button(text='Delete'))#, on_release=self.DeleteJob))
		navpanel.add_widget(Button(text='Export', on_release=partial(ex.Export, self.orders)))
		navpanel.add_widget(Button(text='Select a File', on_release=self.SelectFile))
		navpanel.add_widget(Button(text='Settings', on_release=self.Settings))
		return navpanel

	def SelectFile(self, instance):
		def _fbrowser_canceled(instance):
			print 'Selection canceled'
		def _fbrowser_success(instance):
			try:
				self.orders = ReadOrders(instance.selection[0])
				self.UpdateSlide0()
				self.UpdateSlide1()
				self.orderpath = instance.selection[0]
				self.PostBuildInit()
				popup.dismiss()
				self.navboard.ids.nd.toggle_state()
				print instance.selection
			except:
				pass

		if platform == 'win':
			user_path = dirname(expanduser('~')) + sep + 'Documents'
		else:
			user_path = expanduser('~') + sep + 'Documents'
		browser = FileBrowser(select_string='Select',
							favorites=[(user_path, 'Documents')])
		browser.bind(on_success=_fbrowser_success,
        			on_canceled=_fbrowser_canceled)
		popup = Popup(title='Select a file',
						size_hint=(.75,.75),
						content=browser)
		popup.open()

	def Settings(self, instance):
		settingscontents = SettingsContents()
		self.settingspopup = Popup(title='Settings',
								size_hint=(.5,.8),
								content=settingscontents,
								title_size=sp(20))
		self.settingspopup.open()

	def OrderInfo(self, btn, touch, touchtime):
		index = btn.parent.children.index(btn)
		for i in range(0, len(btn.parent.children)+1, btn.parent.cols):
			if i > index:	
				break
		jo = btn.parent.children[i-1].text
		o = [o for o in self.orders if o.jo==jo][0]
		sizehint = (.8,min(o.sections/15.0+.25,1))
		self.orderinfopanel = OrderInfoPanel(o)
		self.orderinfopopup = Popup(title='Order Information JO# '+jo,
									title_size=sp(20),
									content=self.orderinfopanel,
									size_hint=sizehint)
		self.orderinfopopup.open()
	###################################################################### THREADING ######################################################################
	def StartTH(self, btn):
		def pauseTH(instance):
			if self.THpanelpause.text == 'Pause':
				self.signal = 'pause'
				self.THpanelpause.text = 'Continue'
			else:
				self.signal = 'run'
				self.THpanelpause.text = 'Pause'

		def killTH(instance):
			if not self.signal=='stop':
				print '*'*80
				print '*'*34,'Forced End','*'*34
				print '*'*80
			self.signal = 'stop'
			time.sleep(1)
			self.THpopup.dismiss()

		def isProcessing(instance):
			if self.th.isAlive():
				return True
			else:
				self.UpdateSlide1()

		self.th = threading.Thread(target=self.RunTH)
		self.th.start()

		self.THpanel = BoxLayout(orientation='vertical')
		self.THpanelpb = ProgressBar(size_hint_y=5, max=self.timelimit*60.0)
		self.THpanelpause = Button(text='Pause', on_release=pauseTH)
		self.THpanelkill = Button(text='Cancel', on_release=killTH)
		self.THpanel.add_widget(self.THpanelpb)
		self.THpanel.add_widget(self.THpanelpause)
		self.THpanel.add_widget(self.THpanelkill)
		self.THpopup = Popup(title='Initializing...',
							title_size=sp(20),
							size_hint=(.5,.5),
							content=self.THpanel,
							on_dismiss=isProcessing)
		self.THpopup.open()
 
	def RunTH(self):
		print '*'*80
		print '*'*35,' Start  ','*'*35
		print '*'*80
		print
		print 'orders\t:',len(self.orders)
		print 'process(es)\t:',multiprocessing.cpu_count()
		print 'est. time\t:', self.timelimit,'min(s)'
		print 
		self.signal = 'run'
		self.t0  = time.time()
		while time.time()-self.t0 < self.timelimit*60:
			t = time.time()
			self.pausetime = 0.0
			MP(random.randint(0,len(self.neighbourhoods)-1))
			if not self.signal=='stop':
				print 'time taken',round(time.time()-t-self.pausetime,4),'seconds'
				print
				self.t0+=self.pausetime
			else:
				return
		ex.Export(ForSchedule(copy.deepcopy(app.orders)))
		self.signal = 'stop'
		app.THpanel.remove_widget(app.THpanelpause)
		app.THpanelkill.size_hint_y*=2
		app.THpanelkill.text='OK'
		print '*'*80
		print '*'*35,' Ended  ','*'*35
		print '*'*80

	def SignalCheck(self):
		t = time.time()
		while self.signal=='pause':
			time.sleep(1)
			print '.',
			if self.signal=='stop':
				return False
		if self.signal=='stop':
			return False
		self.pausetime+=time.time()-t
		self.THpanelpb.max+=self.pausetime
		return True

	def UpdateTHpanel(self):
		self.THpanelpb.value = time.time()-self.t0
		self.THpopup.title = 'Processing Permutations... '+str(round(self.THpanelpb.value/self.THpanelpb.max*100,2))+'%'
	###################################################################### CALCULATIONS ######################################################################
	def neighbours_random(self, num):
		candidates = []
		for i in range(num):
			if not self.SignalCheck():
				return []
			self.UpdateTHpanel()
			candidate = copy.deepcopy(self.orders)
			random.shuffle(candidate)
			candidates.append(candidate)
		return candidates

	def neighbours_swap(self):
		candidates = []
		for i,j in combinations(range(len(self.orders)),2):
			self.UpdateTHpanel()
			candidate = copy.deepcopy(self.orders)
			if not self.SignalCheck():
				return []
			candidate[i],candidate[j] = candidate[j],candidate[i]
			candidates.append(candidate)
		return candidates

	def neighbours_LNS(self, size):
		approach = 'UT'
		candidates = []
		neighbourhoods = list(combinations(app.orders,size))
		random.shuffle(neighbourhoods)

		for subset in neighbourhoods[:self.LNSmax]:
			if not self.SignalCheck():
				return []
			self.UpdateTHpanel()

			bestsubperm = list(subset)
			bestsubut = CalUT(ForSchedule(copy.deepcopy(subset)))
			for perm in permutations(subset):
				# Method 1: SPT
				if approach=='SPT': 
					pass
				# Method 2: Highest Utilization
				elif approach=='UT':
					avgsubut = CalUT(ForSchedule(copy.deepcopy(perm)))
					if avgsubut > bestsubut:
						bestsubut = avgsubut
						bestsubperm = list(perm)
			# if another ordering or the subset has a better performance
			if not bestsubperm==list(subset):
				candidate = copy.deepcopy(app.orders)
				# copy back the bestsubperm to fullperm
				i=0
				for j,o in enumerate(candidate):
					if o.jo in [r.jo for r in bestsubperm]:
						candidate[j] = bestsubperm[i]
						i+=1
				candidates.append(candidate)
		return candidates

	def neighbours_idle(self, size):
		candidates = [self.orders]
		self.UpdateTHpanel()
		if not self.SignalCheck():
			return []
		return candidates


if __name__=='__main__':
	multiprocessing.freeze_support()
	bestut = multiprocessing.Array('d',[])
	selectedorders = multiprocessing.Array('b',[])
	ex = Exporter()
	app = TestScheduler()
	app.run()