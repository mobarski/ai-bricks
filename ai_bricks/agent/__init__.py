from . import actions
from . import react0
from . import react

def get(name):
	if name=='v1':
		return react0.v1
	elif name=='v2':
		return react0.v2
	elif name=='react':
		return react.Agent
