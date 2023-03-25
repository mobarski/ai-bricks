from . import actions
from . import react

def get(name):
	if name=='v1':
		return react.v1
	elif name=='v2':
		return react.v2
