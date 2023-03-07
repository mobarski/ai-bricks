import cohere
import os

api_key = None


def use_key(key):
	global api_key
	api_key = key
if not openai.api_key:
	use_key(os.getenv('COHERE_KEY'))


# models: medium|xlarge
def model(name, **kwargs):
	return TextModel(name, **kwargs)


class TextModel:
	PARAMS = ['model','temperature','stop_sequences'] # TODO
	
	def __init__(self, name, **kwargs):
		self.config = kwargs
		self.config['model'] = name
		self.client = cohere.Client(api_key)

	def complete(self, prompt):
		out = {}
		#
		kwargs = dict(
			prompt = prompt,
			max_tokens = 100, # TODO
		)
		for k,v in self.config.items():
			if k in self.PARAMS:
				kwargs[k] = v
		#
		resp = self.client.generate(**kwargs)
		#
		out['text'] = resp.generations[0].text
		out['raw'] = resp # XXX
		return out
	
	def embed(self, text):
		out = {}
		resp = self.embed_many([text])
		out['vector'] = resp['vectors'][0]
		return out
	
	def embed_many(self, texts):
		out = {}
		resp = self.client.embed(texts)
		out['vectors'] = resp.embeddings
		return out


# REF: https://cohere.ai/pricing
# REF: https://dashboard.cohere.ai/api-keys
# REF: https://docs.cohere.ai/reference/generate
# REF: https://docs.cohere.ai/reference/embed
# REF: https://docs.cohere.ai/reference/tokenize
