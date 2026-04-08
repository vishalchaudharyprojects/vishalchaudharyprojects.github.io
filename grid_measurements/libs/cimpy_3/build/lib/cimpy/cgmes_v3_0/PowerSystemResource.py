from .IdentifiedObject import IdentifiedObject

#updated as per TC57CIM Profile part from standard book
class PowerSystemResource(IdentifiedObject):
	'''
	A power system resource can be an item of equipment such as a switch, an equipment container containing many individual items of equipment such as a substation, or an organisational entity such as sub-control area. Power system resources can have measurements associated.

	:Controls: Regulating device governed by this control output. Default: "list"
	:Measurements: The power system resource that contains the measurement. Default: "list"
	:Location: Location of this power system resource. Default: None
		'''

	cgmesProfile = IdentifiedObject.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.GL.value, cgmesProfile.DY.value, cgmesProfile.SSH.value, cgmesProfile.OP.value, cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, cgmesProfile.SC.value, ],
						'Controls': [cgmesProfile.OP.value, ],
						'Measurements': [cgmesProfile.OP.value, ],
						'Controls': [cgmesProfile.OP.value, ],

						 }

	serializationProfile = {}

	__doc__ += '\n Documentation of parent class IdentifiedObject: \n' + IdentifiedObject.__doc__ 

	def __init__(self, Controls = "list", Measurements = "list", Location = None,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.Controls = Controls
		self.Measurements = Measurements
		self.Location = Location
		
	def __str__(self):
		str = 'class=PowerSystemResource\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
