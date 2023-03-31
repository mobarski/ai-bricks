# ===[ UTILS ]======================================================================================

# JSON
import json
def from_json(text):
	text = text.strip()
	try:
		return json.loads(text)
	except:
		text = text.replace("'", '"')
		return json.loads(text)

# TEMPLATES
from jinja2 import Template
def render(template, **kw):
	return Template(template).render(**kw)


# EXCEPTIONS
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
	"evaluate single python expression; imported modules: math, time, random, datetime; do not import anything else; use only one line of code"
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
PAGE = {{ p }}
CONTENT = {{ s.strip() }}

{% endfor %}

OTHER PAGES = {{ json.dumps(other_pages) }}
"""

def wikipedia_search_many(query):
	"query wikipedia with a list of entities / subjects"
	n = 1
	limit = None # limit summary length
	summaries = [] # list of (page,summary) tuples
	other_pages = []
	for q in from_json(query):
		pages = wikipedia.search(q)
		for i,p in enumerate(pages):
			try:
				summary = wikipedia.summary(p)[:limit]
			except:
				continue
			summaries += [(p,summary)]
			if len(summaries) >= n:
				other_pages += pages[i+1:]
				break
	if summaries:
		kw = locals()
		kw['json'] = json
		output = render(wiki_template, **kw).rstrip()
	else:
		output = 'No results!'
	return output

# SUNSET
def wikipedia_search(query):
	"wikipedia summary about person, place, company, historical event, or other subject. "
	if " and "	in query or " or " in query or " vs " in query or ", " in query or " & " in query:
		return 'Error: Never use "and", "or", "vs", ",", or "&" in the query!'
	n = 1
	limit = None
	query = query.strip()
	pages = wikipedia.search(query)
	if not pages and query[0]==query[-1]=='"':
		pages = wikipedia.search(query.replace('"',''))
	summaries = []
	other_pages = []
	for i,p in enumerate(pages):
		try:
			summary = wikipedia.summary(p)[:limit]
		except:
			continue
		summaries += [(p,summary)]
		if len(summaries) >= n:
			other_pages += pages[i+1:]
			break
	if summaries:
		kw = locals()
		output = render(wiki_template, **kw).rstrip()
	else:
		output = 'No results! Remember to use only one entity in the query.'
	return output

@return_exceptions
def wikipedia_set_lang(text):
	return str(wikipedia.set_lang(text))

# XXX
if __name__=="__main__":
	print(wikipedia_search_many('["moons of saturn","moons of jupiter"]'))
