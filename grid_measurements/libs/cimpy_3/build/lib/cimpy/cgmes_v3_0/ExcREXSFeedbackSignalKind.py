from .Base import Base

#updated as per TC57CIM Profile part from standard book
class ExcREXSFeedbackSignalKind(Base):
	'''
	Type of rate feedback signals.

		'''

	cgmesProfile = Base.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.DY.value, ],
						 }

	serializationProfile = {}

	

	def __init__(self,  ):
	
		pass
	
	def __str__(self):
		str = 'class=ExcREXSFeedbackSignalKind\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
