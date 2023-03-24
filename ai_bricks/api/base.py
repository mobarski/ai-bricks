
class BaseModel:
	PARAMS = ['model']
	MAPPED = {}

	def __init__(self, name, **kwargs):
		self.name = name
		self.usage = {}
		self.config = {}
		self.config.update(kwargs)
		self.config['model'] = name
		self.callbacks = {}

	def add_callback(self, kind, fun):
		# kind: before|after
		chain = self.callbacks[kind]
		if fun not in chain:
			chain.append(fun)

	def callbacks_before(self, kwargs):
		for callback in self.callbacks.get('before',[]):
			callback(kwargs, self)
	
	def callbacks_after(self, out, resp):
		for callback in self.callbacks.get('after',[]):
			callback(out, resp, self)

	def update_kwargs(self, kwargs, kw):
		"add config to kwargs and then add kw"
		for k,v in self.config.items():
			if k in self.PARAMS:
				kwargs[k] = v
		for k,v in kw.items():
			if k in self.PARAMS and k not in ['model']:
				kwargs[k] = v


