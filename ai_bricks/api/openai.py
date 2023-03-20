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


global_config = {}
def set_global(key, value):
	global_config[key] = value

def model(name, **kwargs):
	if name.startswith('gpt-'):
		_class = ChatModel
	elif 'embedding' in name:
		_class = EmbeddingModel
	else:
		_class = TextModel
	return _class(name, **kwargs)

callbacks = {'before':[], 'after':[]}
def add_callback(kind, fun):
	"add callback to every model created after this call"
	# kind: before|after
	chain = callbacks[kind]
	if fun not in chain:
		chain.append(fun)

# ===[ MODELS ]================================================================


class BaseTextModel:
	def __init__(self, name, **kwargs):
		self.config = {}
		self.config.update(global_config)
		self.config.update(kwargs)
		self.config['model'] = name
		self.max_tokens = _get_model_max_tokens(name)
		self.callbacks = {k:v.copy() for k,v in callbacks.items()}
		try:
			self.encoder = tiktoken.encoding_for_model(name)
		except KeyError:
			self.encoder = tiktoken.encoding_for_model('text-davinci-003')

	def token_count(self, text):
		return len(self.encoder.encode(text))

	def add_callback(self, kind, fun):
		# kind: before|after
		chain = self.callbacks[kind]
		if fun not in chain:
			chain.append(fun)

	def update_kwargs(self, kwargs, kw):
		"add config to kwargs and then add kw"
		for k,v in self.config.items():
			if k in self.PARAMS:
				kwargs[k] = v
		for k,v in kw.items():
			if k in self.PARAMS and k not in ['model']:
				kwargs[k] = v

	def callbacks_before(self, kwargs):
		for callback in self.callbacks.get('before',[]):
			callback(kwargs, self)
	
	def callbacks_after(self, out, resp):
		for callback in self.callbacks.get('after',[]):
			callback(out, resp, self)


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
		self.callbacks_after(out, resp)
		return out


class ChatModel(BaseTextModel):
	PARAMS = ['model','temperature','top_p','n','stream','stop','presence_penalty','frequency_penalty','logit_bias','user']
	
	def complete(self, prompt, **kw):
		out = {}
		#
		messages = []
		pre_prompt = self.config.get('pre_prompt','')
		if pre_prompt:
			messages += [{'role':'system', 'content':pre_prompt}]
		messages += [{'role':'user', 'content':prompt}]
		kwargs = dict(
			max_tokens = self.max_tokens - self.token_count(prompt + pre_prompt),
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
		self.callbacks_after(out, resp)
		return out


# ===[ HELPERS ]===============================================================

# REF: https://platform.openai.com/docs/models
def _get_model_max_tokens(model):
	model_max_tokens = {
		'gpt-3.5-turbo':4096,
		'gpt-3.5-turbo-0301':4096,
		'text-davinci-003':4000,
		'text-davinci-002':4000,
		'text-davinci-001':4000,
		'code-davinci-002':8000,
		'text-embedding-ada-002':8191,
	}
	return model_max_tokens.get(model, 2048)
