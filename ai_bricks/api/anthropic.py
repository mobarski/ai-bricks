import anthropic
import time
import os

api_key = None

def use_key(key):
	global api_key
	api_key = key
if not api_key:
	use_key(os.getenv('ANTHROPIC_KEY'))

# TODO: ChatModel messages [('system','xxx'),('user','yyy'),('system','zzz'),('user','aaa')]
class TextModel:
	PARAMS = ['model','temperature','stop_sequences','max_tokens_to_sample']
	MAPPED = {'stop':'stop_sequences'}
	
	def __init__(self, name, **kwargs):
		self.config = kwargs
		self.config['model'] = name
		self.client = anthropic.Client(api_key)
	
	def complete(self, prompt, **kw):
		out = {}
		#
		kwargs = dict(
			prompt = f"{anthropic.HUMAN_PROMPT} {prompt}{anthropic.AI_PROMPT}",
			max_tokens_to_sample = 1000, # TODO
		)
		config = self.config.copy()
		config.update(kw) # NEW
		for k,v in config.items():
			k = self.MAPPED.get(k,k) # NEW
			if k in self.PARAMS:
				kwargs[k] = v
		t0 = time.time()
		#
		resp = self.client.completion(**kwargs)
		#
		out['rtt'] = time.time() - t0
		out['text'] = resp['completion']
		out['raw'] = resp # XXX
		return out


# models: 
def model(name, **kwargs):
	return TextModel(name, **kwargs)

