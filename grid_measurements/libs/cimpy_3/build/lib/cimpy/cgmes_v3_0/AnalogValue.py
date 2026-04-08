from .MeasurementValue import MeasurementValue

#updated as per TC57CIM Profile part 452, and sec 6.12
class AnalogValue(MeasurementValue):
	'''
	AnalogValue represents an analog MeasurementValue.

	:Analog: The values connected to this measurement. Default: None
	:AnalogControl: The MeasurementValue that is controlled. Default: None
	:value: The value to supervise. Default: 0.0
		'''

	cgmesProfile = MeasurementValue.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.OP.value, ],
						'Analog': [cgmesProfile.OP.value, ],
						'AnalogControl': [cgmesProfile.OP.value, ],
						#'value': [cgmesProfile.EQ.value, ],
						 }

	serializationProfile = {}

	__doc__ += '\n Documentation of parent class MeasurementValue: \n' + MeasurementValue.__doc__ 

	def __init__(self, Analog = None, AnalogControl = None,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.Analog = Analog
		self.AnalogControl = AnalogControl
		#self.value = value
		
	def __str__(self):
		str = 'class=AnalogValue\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
