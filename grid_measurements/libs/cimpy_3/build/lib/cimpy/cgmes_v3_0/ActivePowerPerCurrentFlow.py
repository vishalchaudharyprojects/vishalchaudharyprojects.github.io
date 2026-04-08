from .Base import Base

#updated as per TC57CIM Profile part 452, and sec 5.172
class ActivePowerPerCurrentFlow(Base):
	'''
	

	:denominatorMultiplier:  Default: None
	:denominatorUnit:  Default: None
	:multiplier:  Default: None
	:unit:  Default: None
	:value:  Default: 0.0
		'''

	cgmesProfile = Base.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.EQ.value, ],
						#'denominatorMultiplier': [cgmesProfile.EQ.value, ],
						#'denominatorUnit': [cgmesProfile.EQ.value, ],
						'multiplier': [cgmesProfile.EQ.value, ],
						'unit': [cgmesProfile.EQ.value, ],
						'value': [cgmesProfile.EQ.value, ],
						 }

	serializationProfile = {}

	

	def __init__(self, multiplier = None, unit = None, value = 0.0,  ):
	
		#self.denominatorMultiplier = denominatorMultiplier
		#self.denominatorUnit = denominatorUnit
		self.multiplier = multiplier
		self.unit = unit
		self.value = value
		
	def __str__(self):
		str = 'class=ActivePowerPerCurrentFlow\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
