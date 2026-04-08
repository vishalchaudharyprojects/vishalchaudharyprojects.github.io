from .Measurement import Measurement

#updated as per TC57CIM Profile part 452, CoreEquipment profile
class Accumulator(Measurement):
	'''
	Accumulator represents an accumulated (counted) Measurement, e.g. an energy value.

	:LimitSets: The Measurements using the LimitSet. Default: "list"
	:AccumulatorValues: Measurement to which this value is connected. Default: "list"
		'''

	cgmesProfile = Measurement.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.EQ.value, ],
						'LimitSets': [cgmesProfile.EQ.value, ],
						'AccumulatorValues': [cgmesProfile.EQ.value, ],
						 }
# Also the information from which package file a class was read is stored in the serializationProfile dictionary.
#chatgpt: In CIM CGMES 3.0, the serializationProfile attribute is not needed because the serialization format and rules are defined by the standard itself. The attribute was used in earlier versions of CIM, such as CIM15 and CIM16, to customize the serialization behavior for specific profiles or implementations. However, in CIM CGMES 3.0, the serialization format is standardized, and there is no need for a separate attribute to define serialization profiles. Therefore, the serializationProfile attribute can be removed from the code without affecting its functionality.
	serializationProfile = {}

	__doc__ += '\n Documentation of parent class Measurement: \n' + Measurement.__doc__ 

	def __init__(self, LimitSets = "list", AccumulatorValues = "list",  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.LimitSets = LimitSets
		self.AccumulatorValues = AccumulatorValues
		
	def __str__(self):
		str = 'class=Accumulator\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
