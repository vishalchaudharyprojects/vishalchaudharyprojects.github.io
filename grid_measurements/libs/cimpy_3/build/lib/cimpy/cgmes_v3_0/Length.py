from .Base import Base

#updated as per TC57CIM Profile part from standard book
class Length(Base):
	'''
	Unit of length. Never negative.

	:value:  Default: 0.0
	:unit:  Default: None
	:multiplier:  Default: None
		'''

	cgmesProfile = Base.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.EQ.value, cgmesProfile.DY.value,cgmesProfile.SC.value,  ],
						'value': [cgmesProfile.EQ.value, cgmesProfile.DY.value, cgmesProfile.SC.value, ],
						'unit': [cgmesProfile.EQ.value, cgmesProfile.DY.value,cgmesProfile.SC.value,  ],
						'multiplier': [cgmesProfile.EQ.value, cgmesProfile.DY.value,cgmesProfile.SC.value,  ],
						 }

	serializationProfile = {}

	

	def __init__(self, value = 0.0, unit = None, multiplier = None,  ):
	
		self.value = value
		self.unit = unit
		self.multiplier = multiplier
		
	def __str__(self):
		str = 'class=Length\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
