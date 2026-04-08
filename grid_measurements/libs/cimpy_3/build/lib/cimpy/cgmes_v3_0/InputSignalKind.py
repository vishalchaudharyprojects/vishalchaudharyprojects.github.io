from .Base import Base

#updated as per TC57CIM Profile part from standard book
class InputSignalKind(Base):
	'''
	Input signal type.  In Dynamics modelling, commonly represented by j parameter.

		'''

	cgmesProfile = Base.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.DY.value, ],
						 }

	serializationProfile = {}

	

	def __init__(self,  ):
	
		pass
	
	def __str__(self):
		str = 'class=InputSignalKind\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
