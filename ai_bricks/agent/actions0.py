# ===[ UTILS ]======================================================================================

from jinja2 import Template
def render(template, **kw):
	return Template(template).render(**kw)


import traceback
from functools import wraps

VERBOSE_EXCEPTIONS = False

def return_exceptions(fun):
	@wraps(fun)
	def wrapped(*a,**kw):
		try:
			return fun(*a,**kw)
		except Exception as e:
			return traceback.format_exc() if VERBOSE_EXCEPTIONS else str(e)
	return wrapped

# EXPERIMENTAL / SANDBOX
def get_actions(tools, hints:dict=None) -> dict:
	actions = {}
	help = {}
	hints = hints or {}
	for fun in tools:
		name = fun.__name__
		actions[name] = fun
		#
		instr = fun.__doc__ or ''
		hint = hints.get(name, '')
		sep = '; ' if instr and hint else ''
		help[name] = instr + sep + hint
	return {'actions':actions, 'instructions':help}

# ===[ PYTHON ]=====================================================================================

@return_exceptions
def python_eval(text):
	"evaluate python expression; imported modules: math, time, random, datetime; do not import anything else"
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

wiki_template = """
{% for p,s in summaries %}
PAGE: {{p}}
{{s}}

{% endfor %}

OTHER PAGES: {{', '.join(pages[n+1:])}}
"""

def wikipedia_summaries(query):
	"search wikipedia and return up to 3 page summaries; use only one entity in the query"
	n = 3
	query = query.strip()
	pages = wikipedia.search(query)
	if not pages and query[0]==query[-1]=='"':
		pages = wikipedia.search(query[1:-1])
	summaries = []
	for p in pages:
		try:
			summary = wikipedia.summary(p)
		except:
			continue
		summaries += [(p,summary)]
		if len(summaries) >= n:
			break
	if summaries:
		output = render(wiki_template, **locals()).rstrip()
	else:
		output = 'No results! Remember to use only one entity in the query.'
	return output

@return_exceptions
def wikipedia_search(text):
	"get names of wikipedia pages matching a search query"
	return str(wikipedia.search(text))

@return_exceptions
def wikipedia_summary(text):
	"get summary of a wikipedia page"
	return str(wikipedia.summary(text))

@return_exceptions
def wikipedia_page_links(text):
	"get links of a wikipedia page"
	return str(wikipedia.page(text).links)

@return_exceptions
def wikipedia_page(text):
	return str(wikipedia.page(text).content)

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

