from .ConductingEquipment import ConductingEquipment

#newly defined as per TC57CIM Profile part 452, CoreEquipment profile CutsAndJumpers
class Clamp(ConductingEquipment):
	'''
	Combination of conducting material with consistent electrical characteristics, building a single electrical system, used to carry current between points in the power system.

	:length: Segment length for calculating line section capabilities Default: 0.0
		'''

	cgmesProfile = ConductingEquipment.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.EQ.value, ],
						'lengthFromTerminal1': [cgmesProfile.EQ.value, ],
						'ACLineSegment': [cgmesProfile.EQ.value, ], 
						 }

	serializationProfile = {}

	__doc__ += '\n Documentation of parent class ConductingEquipment: \n' + ConductingEquipment.__doc__ 

	def __init__(self, lengthFromTerminal1 = 0.0, ACLineSegment= '',  *args, **kw_args):
		super().__init__(*args, **kw_args)
	#TBC datatype  for aclinesegment
		self.lengthFromTerminal1 = lengthFromTerminal1
		self.ACLineSegment = ACLineSegment
		
	def __str__(self):
		str = 'class=Clamp\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
