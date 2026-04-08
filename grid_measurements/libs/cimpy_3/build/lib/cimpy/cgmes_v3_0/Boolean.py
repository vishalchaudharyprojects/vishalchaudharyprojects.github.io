from .Base import Base

#updated as per TC57CIM Profile 
class Boolean(Base):
	'''
	A type with the value space "true" and "false".

		'''

	cgmesProfile = Base.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.DL.value, cgmesProfile.EQ.value, cgmesProfile.SSH.value, cgmesProfile.SV.value, cgmesProfile.DY.value, cgmesProfile.EQ_BD.value, cgmesProfile.GL.value,  cgmesProfile.OP.value, cgmesProfile.SC.value,],
						 }

	serializationProfile = {}

	

	def __init__(self,  ):
	
		pass
	
	def __str__(self):
		str = 'class=Boolean\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
