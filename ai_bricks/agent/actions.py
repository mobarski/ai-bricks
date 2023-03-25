# ===[ UTILS ]======================================================================================

import traceback

VERBOSE_EXCEPTIONS = True

def return_exceptions(fun):
	def wrapped(*a,**kw):
		try:
			return fun(*a,**kw)
		except Exception as e:
			return traceback.format_exc() if VERBOSE_EXCEPTIONS else str(e)
	return wrapped

# ===[ PYTHON ]=====================================================================================

@return_exceptions
def python_eval(text):
	import math
	import time
	import random
	import datetime
	text = text.strip().strip('"')
	# monkey patching dangerous things
	time.sleep = None
	#builtins = {k:__builtins__[k] for k in ['list','set','range','sum','max','min','str','zip','round','abs','all','any','bool','chr','ord','dict','divmod','enumerate','filter','float','int','format','hash','hex','iter','len','map','oct','pow','slice','sorted','tuple','type','vars']}
	builtins = __builtins__ # TODO
	#
	_globals = {'math':math, 'time':time, 'random':random, 'datetime':datetime, '__builtins__':builtins}
	_locals = {}
	return str(eval(text, _globals, _locals))

# ===[ REQUESTS ]===================================================================================

import requests
from bs4 import BeautifulSoup
import re

@return_exceptions
def requests_get_headlines(url):
	html = requests.get(url).text
	soup = BeautifulSoup(html, 'html.parser')
	out = []
	for h in ['h1','h2']: #'h3','h4','h5','h6']:
		out += [x.get_text() for x in soup.findAll(h)]
	text = '\n'.join(out)
	text = re.sub(r'[\t ]+', ' ', text)
	return text[:1000]

# ===[ WIKIPEDIA ]==================================================================================

# REF: https://wikipedia.readthedocs.io/en/latest/code.html

import wikipedia

@return_exceptions
def wikipedia_summary(text):
	return str(wikipedia.summary(text))

@return_exceptions
def wikipedia_search(text):
	return str(wikipedia.search(text))

@return_exceptions
def wikipedia_page(text):
	return str(wikipedia.page(text).content)

@return_exceptions
def wikipedia_page_links(text):
	return str(wikipedia.page(text).links)

@return_exceptions
def wikipedia_page_html(text):
	return str(wikipedia.page(text).html())

@return_exceptions
def wikipedia_page_images(text):
	return str(wikipedia.page(text).images)

@return_exceptions
def wikipedia_page_references(text):
	return str(wikipedia.page(text).references)

@return_exceptions
def wikipedia_set_lang(text):
	return str(wikipedia.set_lang(text))

