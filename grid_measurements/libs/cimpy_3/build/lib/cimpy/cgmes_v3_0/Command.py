from .Control import Control

#updated as per TC57CIM Profile part 452, and sec 6.14
class Command(Control):
	'''
	A Command is a discrete control used for supervisory control.

	:normalValue: Normal value for Control.value e.g. used for percentage scaling. Default: 0
	:value: The value representing the actuator output. Default: 0
	:DiscreteValue: The Control variable associated with the MeasurementValue. Default: None
	:ValueAliasSet: The ValueAliasSet used for translation of a Control value to a name. Default: None
		'''

	cgmesProfile = Control.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.OP.value, ],
						'normalValue': [cgmesProfile.OP.value, ],
						'value': [cgmesProfile.OP.value, ],
						'DiscreteValue': [cgmesProfile.OP.value, ],
						'ValueAliasSet': [cgmesProfile.OP.value, ],
						 }

	serializationProfile = {}

	__doc__ += '\n Documentation of parent class Control: \n' + Control.__doc__ 

	def __init__(self, normalValue = 0, value = 0, DiscreteValue = None, ValueAliasSet = None,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.normalValue = normalValue
		self.value = value
		self.DiscreteValue = DiscreteValue
		self.ValueAliasSet = ValueAliasSet
		
	def __str__(self):
		str = 'class=Command\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
