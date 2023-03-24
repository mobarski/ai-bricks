"OpenAI API adapter / facade"

# TODO: max_new_tokens
# TODO: chat-pre-prompt

# TODO: refactor kwargs
# TODO: refactor encoder

# TODO: images
# TODO: audio


import tiktoken
import openai
import time
import os

def use_key(key):
	openai.api_key = key
if not openai.api_key:
	use_key(os.getenv('OPENAI_KEY'))

def model(name, **kwargs):
	if name.startswith('gpt-'):
		_class = ChatModel
	elif 'embedding' in name:
		_class = EmbeddingModel
	else:
		_class = TextModel
	return _class(name, **kwargs)

global_config = {}
def set_global(key, value):
	global_config[key] = value

callbacks = {'before':[], 'after':[]}
def add_callback(kind, fun):
	"add callback to every model created after this call"
	# kind: before|after
	chain = callbacks[kind]
	if fun not in chain:
		chain.append(fun)

# ===[ MODELS ]================================================================

from .base import BaseModel

# TODO: rtt and usage as callbacks

class BaseTextModel(BaseModel):
	def __init__(self, name, **kwargs):
		super().__init__(name, **kwargs)
		self.config.update(global_config)
		self.callbacks = {k:v.copy() for k,v in callbacks.items()} # TODO: better update
		self.max_tokens = _get_model_max_tokens(name)
		try:
			self.encoder = tiktoken.encoding_for_model(name)
		except KeyError:
			self.encoder = tiktoken.encoding_for_model('text-davinci-003')

	def token_count(self, text):
		return len(self.encoder.encode(text))
	
	def get_usd_cost(self, usage):
		model = self.config['model']
		prompt_tokens = usage['prompt_tokens']
		output_tokens = usage['total_tokens'] - prompt_tokens
		prompt_price = {
			'gpt-4':0.03,
			'gpt-4-32k':0.06,
			'gpt-3.5-turbo':0.002,
			'text-davinci-003':0.02,
			'text-davinci-002':0.02,
			'text-davinci-001':0.02,
			'text-curie-001':0.002,
			'text-babbage-001':0.0005,
			'text-ada-001':0.0004,
			'text-embedding-ada-002':0.0004,
		}.get(model)
		output_price = {
			'gpt-4':0.06,
			'gpt-4-32k':0.12,
			'text-embedding-ada-002':0,
		}.get(model, prompt_price)
		return (prompt_tokens/1000 * prompt_price) + (output_tokens/1000 * output_price) # TODO: math.ceil ???


class TextModel(BaseTextModel):
	PARAMS = ['model','temperature','top_p','n','stream','stop','presence_penalty','frequency_penalty','logit_bias','user',   'logprobs','echo','best_of']
	
	def complete(self, prompt, **kw):
		out = {}
		#
		kwargs = dict(
			max_tokens = self.max_tokens - self.token_count(prompt),
			prompt = prompt,
		)
		self.update_kwargs(kwargs, kw)
		self.callbacks_before(kwargs)
		t0 = time.time()
		#
		resp = openai.Completion.create(**kwargs)
		#
		out['rtt'] = time.time() - t0
		out['text']  = resp['choices'][0]['text']
		out['usage'] = dict(resp['usage'])
		self.callbacks_after(out, resp)
		return out

	def complete_many(self, prompts, **kw):
		out = {}
		#
		kwargs = dict(
			max_tokens = self.max_tokens - max([self.token_count(p) for p in prompts]),
			prompt = prompts,
		)
		self.update_kwargs(kwargs, kw)
		self.callbacks_before(kwargs)
		t0 = time.time()
		#
		resp = openai.Completion.create(**kwargs)
		#
		out['rtt'] = time.time() - t0
		out['texts'] = [x['text'] for x in resp['choices']]
		out['usage'] = dict(resp['usage'])
		self.callbacks_after(out, resp)
		return out

	def insert(self, prompt, marker='[insert]', **kw):
		out = {}
		#
		prompt1,_,prompt2 = prompt.partition(marker)
		kwargs = dict(
			max_tokens = self.max_tokens - self.token_count(prompt),
			prompt = prompt1,
			suffix = prompt2,
		)
		self.update_kwargs(kwargs, kw)
		self.callbacks_before(kwargs)
		t0 = time.time()
		#
		resp = openai.Completion.create(**kwargs)
		#
		out['rtt'] = time.time() - t0
		out['text']  = resp['choices'][0]['text']
		out['usage'] = dict(resp['usage'])
		out['cost'] = self.get_usd_cost(resp['usage'])
		self.callbacks_after(out, resp)
		return out


class ChatModel(BaseTextModel):
	PARAMS = ['model','temperature','top_p','n','stream','stop','presence_penalty','frequency_penalty','logit_bias','user']
	
	def complete(self, prompt, **kw):
		out = {}
		#
		messages = []
		sys_prompt = kw.get('sys_prompt', self.config.get('sys_prompt',''))
		if sys_prompt:
			messages += [{'role':'system', 'content':sys_prompt}]
		messages += [{'role':'user', 'content':prompt}]
		kwargs = dict(
			max_tokens = self.max_tokens - self.token_count(prompt + sys_prompt),
			messages = messages,
		)
		self.update_kwargs(kwargs, kw)
		kwargs['max_tokens'] -= 30 # UGLY: workaround for not counting chat specific tokens
		self.callbacks_before(kwargs)
		t0 = time.time()
		#
		resp = openai.ChatCompletion.create(**kwargs)
		#
		out['rtt'] = time.time() - t0
		out['text'] = resp['choices'][0]['message']['content']
		out['usage'] = dict(resp['usage'])
		out['cost'] = self.get_usd_cost(resp['usage'])
		self.callbacks_after(out, resp)
		return out


class EmbeddingModel(BaseTextModel):
	PARAMS = ['model','user']
	
	def embed(self, text, **kw):
		out = self.embed_many([text], **kw)
		out['vector'] = out['vectors'][0]
		del out['vectors']
		return out

	def embed_many(self, texts, **kw):
		out = {}
		#
		kwargs = dict(
			input = texts,
		)
		self.update_kwargs(kwargs, kw)
		self.callbacks_before(kwargs)
		t0 = time.time()
		#
		resp = openai.Embedding.create(**kwargs)
		#
		out['rtt'] = time.time() - t0
		out['vectors'] = [x['embedding'] for x in resp['data']]
		out['usage']  = dict(resp['usage'])
		out['cost'] = self.get_usd_cost(resp['usage'])
		self.callbacks_after(out, resp)
		return out


# ===[ HELPERS ]===============================================================

# REF: https://platform.openai.com/docs/models
def _get_model_max_tokens(model):
	model_max_tokens = {
		'gpt-4':8192,
		'gpt-4-32k':32768,
		'gpt-3.5-turbo':4096,
		'gpt-3.5-turbo-0301':4096,
		'text-davinci-003':4000,
		'text-davinci-002':4000,
		'text-davinci-001':4000,
		'code-davinci-002':8000,
		'text-embedding-ada-002':8191,
	}
	return model_max_tokens.get(model, 2048)
