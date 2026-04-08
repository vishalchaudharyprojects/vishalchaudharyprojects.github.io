from .Switch import Switch

#newly defined as per TC57CIM Profile part 452, CoreEquipment profile CutsAndJumpers
class Jumper(Switch):
	'''
	A point where one or more conducting equipments are connected with zero resistance.

		'''

	cgmesProfile = Switch.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.EQ.value, cgmesProfile.EQ_BD.value, ],
						 }

	serializationProfile = {}

	__doc__ += '\n Documentation of parent class Connector: \n' + Switch.__doc__ 

	def __init__(self,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		pass
	
	def __str__(self):
		str = 'class=Jumper\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
