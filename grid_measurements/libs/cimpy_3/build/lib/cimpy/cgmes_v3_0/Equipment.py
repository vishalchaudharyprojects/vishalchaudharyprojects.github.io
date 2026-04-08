from .PowerSystemResource import PowerSystemResource

#updated as per TC57CIM Profile part 452, CoreEquipment profile Main
class Equipment(PowerSystemResource):
	'''
	The parts of a power system that are physical devices, electronic or mechanical.

	:aggregate: The single instance of equipment represents multiple pieces of equipment that have been modeled together as an aggregate.  Examples would be power transformers or synchronous machines operating in parallel modeled as a single aggregate power transformer or aggregate synchronous machine.  This is not to be used to indicate equipment that is part of a group of interdependent equipment produced by a network production program. Default: False
	:EquipmentContainer: Container of this equipment. Default: None
	:OperationalLimitSet: The operational limit sets associated with this equipment. Default: "list", can be optional, (page 19)
		'''

	cgmesProfile = PowerSystemResource.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.EQ.value, cgmesProfile.SSH.value, cgmesProfile.DY.value, cgmesProfile.EQ_BD.value,cgmesProfile.SC.value, ],
						'aggregate': [cgmesProfile.EQ.value, ],
						'normallyInService': [cgmesProfile.EQ.value, ],
						'EquipmentContainer': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						#'OperationalLimitSet': [cgmesProfile.EQ.value, ], # For instance, OperationalLimitSet can be used to constraint any conducting equipment. It is up to the business process to define if any equipment is mandatory to have operational limits
						 }

	serializationProfile = {}

	__doc__ += '\n Documentation of parent class PowerSystemResource: \n' + PowerSystemResource.__doc__ 

	def __init__(self, aggregate = False, normallyInService = False ,EquipmentContainer = None,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	#not sure for inital value of normallyInService
		self.aggregate = aggregate
		self.normallyInService = normallyInService
		self.EquipmentContainer = EquipmentContainer
		#self.OperationalLimitSet = OperationalLimitSet
		
	def __str__(self):
		str = 'class=Equipment\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
