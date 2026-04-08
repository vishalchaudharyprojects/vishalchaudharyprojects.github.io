from .PowerSystemResource import PowerSystemResource

#newly defined as per TC57CIM Profile part 452, CoreEquipment profile Main
class BoundaryPoint(PowerSystemResource):
	'''
	Designates a connection point at which one or more model authority sets shall connect to. The location of the connection 
    point as well as other properties are agreed between organisations responsible for the interconnection, hence all attributes of the class represent this agreement. 
      It is primarily used in a boundary model authority set which can contain one or many BoundaryPoint-s among other Equipment-s and their connections.

		'''

	cgmesProfile = PowerSystemResource.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						'fromEndIsoCode': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						'fromEndName': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						'fromEndNameTso': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						'toEndIsoCode': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						'toEndName': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						'toEndNameTso': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						'isDirectCurrent': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						'isExcludedFromAreaInterchange': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						'ConnectivityNode': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						 }

	serializationProfile = {}

	__doc__ += '\n Documentation of parent class PowerSystemResource: \n' + PowerSystemResource.__doc__ 

	def __init__(self, fromEndIsoCode = '', fromEndName = '', fromEndNameTso = '', toEndIsoCode = '', toEndName = '', toEndNameTso = '', isDirectCurrent = False, isExcludedFromAreaInterchange = False, ConnectivityNode = None,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.fromEndIsoCode = fromEndIsoCode
		self.fromEndName = fromEndName
		self.fromEndNameTso = fromEndNameTso
		self.toEndIsoCode = toEndIsoCode
		self.toEndName = toEndName
		self.toEndNameTso = toEndNameTso
		self.isDirectCurrent = isDirectCurrent
		self.isExcludedFromAreaInterchange = isExcludedFromAreaInterchange
		self.ConnectivityNode = ConnectivityNode
		
	def __str__(self):
		str = 'class=BoundaryPoint\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
