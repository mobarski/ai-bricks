import anthropic
import time
from math import ceil
from multiprocessing.pool import ThreadPool
import os


api_key = None

def use_key(key):
	global api_key
	api_key = key
if not api_key:
	use_key(os.getenv('ANTHROPIC_KEY', os.getenv('ANTHROPIC_API_KEY', '')))

# REF: https://console.anthropic.com/docs/api/reference
class TextModel:
	PARAMS = ['model','temperature','stop_sequences','max_tokens_to_sample']
	MAPPED = {'stop':'stop_sequences'}
	
	def __init__(self, name, **kwargs):
		self.name = name
		self.config = kwargs
		self.config['model'] = name
		self.client = anthropic.Client(api_key)
	
	def complete(self, prompt, **kw):
		out = {}
		#
		system_prompt = kw.get('system_prompt', self.config.get('system_prompt',''))
		final_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
		kwargs = dict(
			prompt = f"{anthropic.HUMAN_PROMPT} {final_prompt}{anthropic.AI_PROMPT}",
			max_tokens_to_sample = 1000, # TODO !!! XXX !!! XXX !!! XXX !!!
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
		if 'completion' not in resp:
			raise Exception(resp.get('detail',f'API ERROR: {resp}'))
		#
		out['rtt'] = time.time() - t0
		out['text'] = resp.get('completion','')
		out['cost'] = self.get_usd_cost(resp, kwargs)
		out['usage'] = self.get_usage(resp, kwargs)
		out['raw'] = resp # XXX
		return out

	# TODO: factor out
	def complete_many(self, prompts, **kw):
		def worker(prompt):
			return self.complete(prompt, **kw)
		n_workers = kw.get('n_workers', 4)
		pool = ThreadPool(n_workers)
		resp_list = pool.map(worker, prompts)
		out = {'rtt':0, 'cost':0, 'usage':{}, 'texts':[], 'raw':[]}
		for resp in resp_list:
			out['rtt'] += resp['rtt']
			out['cost'] += resp['cost']
			for k in resp['usage']:
				out['usage'][k] = out['usage'].get(k,0) + resp['usage'][k]
			out['texts'].append(resp['text'])
			out['raw'].append(resp['raw'])
		return out

	# REFL https://cdn2.assets-servd.host/anthropic-website/production/images/FINAL-PRICING.pdf
	def get_usd_cost(self, resp, kwargs):
		"return cost in USD of the response"
		prompt_price = {
			'claude-v1': 2.9,
			'claude-v1.2': 2.9, # ???
			'claude-instant-v1': 0.43,
		}.get(self.name, 0.0)
		output_price = {
			'claude-v1': 8.6,
			'claude-v1.2': 8.6, # ???
			'claude-instant-v1': 1.45,
		}.get(self.name, 0.0)
		prompt_cost = prompt_price * len(kwargs.get('prompt','')) / 1_000_000
		output_cost = output_price * max(0,len(resp.get('completion',''))-len(kwargs.get('start',''))) / 1_000_000
		return prompt_cost + output_cost

	def get_usage(self, resp, kwargs):
		"return usage of the response"
		prompt = kwargs.get('prompt','')
		output = resp.get('completion','')[len(kwargs.get('start','')):]
		out = {}
		#chars_per_token = 4.0 # ???
		#out['prompt_tokens'] = ceil(len(prompt)/chars_per_token)
		#out['completion_tokens'] = ceil(len(output)/chars_per_token)
		out['prompt_tokens'] = anthropic.count_tokens(prompt)
		out['completion_tokens'] = anthropic.count_tokens(output)
		out['total_tokens'] = out['prompt_tokens'] + out['completion_tokens']
		return out

# models: 
def model(name, **kwargs):
	return TextModel(name, **kwargs)
