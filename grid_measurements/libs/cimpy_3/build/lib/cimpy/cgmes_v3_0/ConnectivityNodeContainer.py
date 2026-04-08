from .PowerSystemResource import PowerSystemResource

#updated as per TC57CIM Profile part 452, CoreEquipment profile Main TP_BD removed.
class ConnectivityNodeContainer(PowerSystemResource):
	'''
	A base class for all objects that may contain connectivity nodes or topological nodes.

	:ConnectivityNodes: Connectivity nodes which belong to this connectivity node container. Default: "list"
	:TopologicalNode: The topological nodes which belong to this connectivity node container. Default: "list"
		'''

	cgmesProfile = PowerSystemResource.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.EQ.value, cgmesProfile.TP.value, cgmesProfile.EQ_BD.value, ],
						'ConnectivityNodes': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						'TopologicalNode': [cgmesProfile.TP.value, ],
						 }

	serializationProfile = {}

	__doc__ += '\n Documentation of parent class PowerSystemResource: \n' + PowerSystemResource.__doc__ 

	def __init__(self, ConnectivityNodes = "list", TopologicalNode = "list",  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.ConnectivityNodes = ConnectivityNodes
		self.TopologicalNode = TopologicalNode
		
	def __str__(self):
		str = 'class=ConnectivityNodeContainer\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
