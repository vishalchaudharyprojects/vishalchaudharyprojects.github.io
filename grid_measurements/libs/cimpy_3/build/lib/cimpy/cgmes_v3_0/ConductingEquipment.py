from .Equipment import Equipment

#updated as per TC57CIM Profile part 452, CoreEquipment profile Main
class ConductingEquipment(Equipment):
	'''
	The parts of the AC power system that are designed to carry current or that are conductively connected through terminals.

	:BaseVoltage: All conducting equipment with this base voltage.  Use only when there is no voltage level container used and only one base voltage applies.  For example, not used for transformers. Default: None
	:Terminals: Conducting equipment have terminals that may be connected to other conducting equipment terminals via connectivity nodes or topological nodes. Default: "list"
	:SvStatus: The status state variable associated with this conducting equipment. Default: None
		'''

	cgmesProfile = Equipment.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.DY.value, cgmesProfile.SSH.value, cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, cgmesProfile.SC.value, cgmesProfile.SV.value, ],
						'Terminals': [cgmesProfile.DY.value, cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						'BaseVoltage': [cgmesProfile.EQ.value, ],
						'SvStatus': [cgmesProfile.SV.value, ],
						 }

	serializationProfile = {}

	__doc__ += '\n Documentation of parent class Equipment: \n' + Equipment.__doc__ 

	def __init__(self, Terminals = "list", BaseVoltage = None, SvStatus = None,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.Terminals = Terminals
		self.BaseVoltage = BaseVoltage
		self.SvStatus = SvStatus
		
	def __str__(self):
		str = 'class=ConductingEquipment\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
