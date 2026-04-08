from .ExcitationSystemDynamics import ExcitationSystemDynamics

#newly defined as per TC57CIM Profile part from standard book

class ExcNI(ExcitationSystemDynamics):
	'''
		'''

	cgmesProfile = ExcitationSystemDynamics.cgmesProfile

	possibleProfileList = {'class': [cgmesProfile.DY.value, ],
						'busFedSelector': [cgmesProfile.DY.value, ],
						'tr': [cgmesProfile.DY.value, ],
						'ka': [cgmesProfile.DY.value, ],
						'ta': [cgmesProfile.DY.value, ],
						'vrmax': [cgmesProfile.DY.value, ],
						'vrmin': [cgmesProfile.DY.value, ],
						'kf': [cgmesProfile.DY.value, ],
						'tf2': [cgmesProfile.DY.value, ],
						'tf1': [cgmesProfile.DY.value, ],
						'r': [cgmesProfile.DY.value, ],
						 }

	serializationProfile = {}

	__doc__ += '\n Documentation of parent class ExcitationSystemDynamics: \n' + ExcitationSystemDynamics.__doc__ 

	def __init__(self, busFedSelector = False, tr = 0, ka = 0.0, ta = 0, vrmax = 0.0, vrmin = 0.0, kf = 0.0, tf2 = 0, tf1 = 0, r = 0.0,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.busFedSelector = busFedSelector
		self.tr = tr
		self.ka = ka
		self.ta = ta
		self.vrmax = vrmax
		self.vrmin = vrmin
		self.kf = kf
		self.tf2 = tf2
		self.tf1 = tf1
		self.r = r
		
	def __str__(self):
		str = 'class=ExcNI\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
