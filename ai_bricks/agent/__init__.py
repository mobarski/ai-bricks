from . import actions
from . import react
from . import react2

def get(name):
	if name=='v1':
		return react.v1
	elif name=='v2':
		return react.v2
	elif name=='react':
		return react2.Agent
