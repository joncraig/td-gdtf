import traceback

import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, project.folder+'/modules')

import pygdtf
import re

from CallbacksExt import CallbacksExt
from TDStoreTools import StorageManager
TDF = op.TDModules.mod.TDFunctions

from pprint import pprint

class GDTFFixture(CallbacksExt):
	"""
	GDTFFixture description
	"""
	def __init__(self, ownerComp):
		# the component to which this extension is attached
		self.ownerComp = ownerComp
		# the component to which data is stored
		self.dataComp = ownerComp.op('data')

		# init callbacks
		self.callbackDat = self.ownerComp.par.Callbackdat.eval()
		try:
			CallbacksExt.__init__(self, ownerComp)
		except:
			self.ownerComp.addScriptError(traceback.format_exc() + \
					"Error in CallbacksExt __init__. See textport.")
			print()
			print("Error initializing callbacks - " + self.ownerComp.path)
			print(traceback.format_exc())
		# run onInit callback
		try:
			self.DoCallback('onInit', {'exampleExt':self})
		except:
			self.ownerComp.addScriptError(traceback.format_exc() + \
					"Error in custom onInit callback. See textport.")
			print(traceback.format_exc())

		# properties
		# TDF.createProperty(self, 'MyProperty', value=0, dependable=True,
		# 				   readOnly=False)

		# stored items (persistent across saves and re-initialization):
		storedItems = [
			# Only 'name' is required...
			{'name': 'Channels', 'default': [], 'readOnly': False,
			 						'property': True, 'dependable': True},
			{'name': 'ChannelSets', 'default': {}, 'readOnly': False,
			 						'property': True, 'dependable': False},
		]
		self.fixture = None
		self.stored = StorageManager(self, self.dataComp, storedItems)

	# do something in the future
	def _future(self, attrib, args=(), group_name=None, delayMilliSeconds=0, delayFrames=0):
		if group_name == None:
			group_name = self.ownerComp.name
		self.ownerComp.op('future').run(attrib, args, group=group_name, delayFrames=delayFrames, delayMilliSeconds=delayMilliSeconds)

	# kill all runs with group name
	def _killRuns(self, group_name):
		for r in runs:
			if r.group == group_name:
				r.kill()

	def destroyChans(self):
		self.stored['Channels'] = []
		pages = [p.name for p in self.ownerComp.customPages]
		dmx_page = self.ownerComp.customPages[pages.index('DMX')]
		for p in dmx_page.pars:
			#print(p.name)
			p.destroy()

	def updateMode(self, mode):
		#print(type(dmx_page))

		self.destroyChans()

		pages = [p.name for p in self.ownerComp.customPages]
		dmx_page = self.ownerComp.customPages[pages.index('DMX')]

		channels = []
		order = 0
		if self.fixture == None:
			self.Load()
			return
		m = self.fixture.dmx_modes[mode]

		#pprint([dir(c) for c in m.dmx_channels])

		for c in m.dmx_channels:
			chan_sets = {}
			order += 1
			#print(dir(c))
			#print(len(c.logical_channels))

			if len(c.logical_channels) > 0:
				logical_chan = c.logical_channels[0]
				offset = c.offset
				name = logical_chan.attribute.str_link
				p_name = name.lower().capitalize()
				p_name = re.sub("[^A-Za-z0-9]", "", p_name)
				# print(f"{p_name=}")

				#pprint(logical_chan.channel_functions[0].__dict__)


				channel_function = logical_chan.channel_functions[0]

				byte_count = channel_function.dmx_from.byte_count

				#print(byte_count)
				default = channel_function.default.value
				physical_from = 0
				physical_to = 255**byte_count

				# if len(logical_chan.channel_functions) < 2:
				# 	physical_from = channel_function.physical_from
				# 	physical_to = channel_function.physical_to
				# else:
				# 	physical_from = 0
				# 	physical_to = 255**byte_count

				# default = tdu.remap(default, 0, 256**byte_count,physical_from, physical_to)	
				

				#pprint(channel_function.mode_to.__dict__)
				# print(f"{name=}, {default=},{p_name=}")

				p = dmx_page.appendInt(
					p_name,
					label = name
				)[0]

				p.min = 0
				p.normMin = 0
				p.default = default
				p.val = default
				p.max = physical_to
				p.normMax = physical_to
				p.order = order #offset[0]
				p.startSection = True

				# order += 1
				# p2 = dmx_page.appendStr(
				# 	p_name+'fn',
				# 	label = name + " Fn"
				# )[0]
				# p2.readOnly = True
				# p2.order = order

				# order += 1
				# p2 = dmx_page.appendStr(
				# 	p_name+'set',
				# 	label = name + " Set"
				# )[0]
				# p2.readOnly = True
				# p2.order = order

				# order += 1
				# p2 = dmx_page.appendFloat(
				# 	p_name+'phys',
				# 	label = name + " Phys"
				# )[0]
				# p2.order = order


				for cf in logical_chan.channel_functions:
					for cs in cf.channel_sets:
						if cs.name != '':
							order += 1
							#print(cs.name)

							n = cs.name.lower()
							n = re.sub('[^a-z0-9]+', '', n)

							#print(p_name + n)

							cs_par_name = p_name+n
							set_p = dmx_page.appendPulse(
								cs_par_name,
								label = cs.name
							)[0]
							set_p.order = order

							# pprint(dir(cs))
							dmx_from = cs.dmx_from
							#print(dir(dmx_from))
							chan_sets[cs_par_name] = {
								'chan_par_name': p_name,
								'value': dmx_from.value
							}


							

				# p.setattr('test', {'foo': 'bar'})

				channels.append(
					{
						'offset': offset,
						'name': name,
						'p_name': p_name,
						'byte_count': byte_count,
						'default': default,
						'physical_from': physical_from,
						'physical_to': physical_to,
						'chan_sets': chan_sets
					}
				)



			
		self.stored['ChannelSets'] = chan_sets
		self.stored['Channels'] = channels
		# for m in self.fixture.dmx_modes[0]:
			
		# 	print(m.name)

		# 	self.ownerComp.par.Mode

		#print(dmx_page)
		pass

	def Load(self, file=None):
		if file is None:
			file = self.ownerComp.par.Gdtffile.eval()
		self.fixture = pygdtf.FixtureType(file)

		# print(len(self.fixture.dmx_modes))

		self.ownerComp.par.Mode.menuNames = [str(i) for i in range(len(self.fixture.dmx_modes))]
		self.ownerComp.par.Mode.menuLabels = [m.name for m in self.fixture.dmx_modes]
		mode = 0
		self.ownerComp.par.Mode = mode
		# self.ownerComp.par.Mode.cook()

		#print(dir(self.fixture.dmx_modes[0]))

		self.updateMode( mode )
		

	# example method with callback
	def Start(self):
		self.DoCallback('onStart', {'data': 'start'})
		self._future('done', delayFrames=1)

	# example method with callback
	def done(self):
		self.DoCallback('onDone', {'data': 'start'})

	# example pulse parameter handler
	def pulse_Editextension(self):
		self.ownerComp.op('GDTFFixture').par.edit.pulse()

	def pulse_Start(self):
		self.Start()

	def pulse_Load(self):
		self.Load()

	def pulse_Destroychans(self):
		self.destroyChans()