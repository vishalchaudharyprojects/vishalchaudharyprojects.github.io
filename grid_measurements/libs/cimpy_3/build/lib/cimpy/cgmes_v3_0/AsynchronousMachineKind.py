from .Base import Base

#updated as per TC57CIM Profile part 452, CoreEquipment profile
class AsynchronousMachineKind(Base):
	'''
	Kind of Asynchronous Machine.

		'''

	cgmesProfile = Base.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.SSH.value, ],
						 }

	serializationProfile = {}

	

	def __init__(self,  ):
	
		pass
	
	def __str__(self):
		str = 'class=AsynchronousMachineKind\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
