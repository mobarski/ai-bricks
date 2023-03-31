# ===[ UTILS ]======================================================================================
from pprint import pprint

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
from bs4 import BeautifulSoup

# TODO: SUMMARY vs CONTENT
wiki_summary_template = """
{% for p,s in summaries %}
PAGE = {{ p }}
SUMMARY = {{ s.strip() }}

{% endfor %}

OTHER PAGES = {{ json.dumps(other_pages) }}
"""

def wikipedia_search_many(query):
	"query wikipedia with a list of entities / subjects and return a summary for each one"
	try:
		from_json(query)
	except:
		return "Input must be JSON list!"
	n = 1 # number of summaries per query item
	limit = None # limit summary length
	summaries = [] # list of (page,summary) tuples
	other_pages = []
	done = set()
	for q in from_json(query):
		q_summaries = []
		pages = wikipedia.search(q)
		for i,p in enumerate(pages):
			try:
				#p = wikipedia.suggest(p) # TEST
				summary = wikipedia.summary(p)[:limit]
			except:
				continue
			if p in done:
				continue
			q_summaries += [(p,summary)]
			done.add(p)
			if len(q_summaries) >= n:
				summaries.extend(q_summaries)
				other_pages += pages[i+1:]
				break
	if summaries:
		kw = locals()
		kw['json'] = json
		output = render(wiki_summary_template, **kw).rstrip()
	else:
		output = 'No results!'
	return output


wiki_data_template = """
{% for p,t in data %}
PAGE = {{ p }}
TABLES =
{{ t }}

{% endfor %}
"""

def wikipedia_get_data(query):
	"query wikipedia with a list of entities / subjects and return the main data table for each one"
	try:
		from_json(query)
	except:
		return "Input must be JSON list!"
	n = 1
	limit = 4000
	n_tables = 2
	n_pages = 2
	done = set()
	data = []
	for q in from_json(query):
		q_data = []
		pages = [q] + wikipedia.search(q)[:1]
		#print('PAGES',pages) # XXX
		for i,p in enumerate(pages):
			try:
				#p = wikipedia.suggest(p) # TEST
				page = wikipedia.page(p)
			except:
				continue
			if p in done:
				continue
			tables = _wikipedia_tables(page, n_tables=n_tables)
			q_data += [(p,tables)]
			done.add(p)
			if len(q_data) >= n:
				data.extend(q_data)
				break
		if len(q_data) >= n_pages:
			break
	if data:
		#print('DATA (len)', len(data), [x[0] for x in data], [len(x[1]) for x in data]) # XXX
		kw = locals()
		kw['json'] = json
		kw['len'] = len
		#output = render(wiki_data_template, **kw).rstrip()
		output = '\n\n'.join([f"PAGE = {p}\nTABLES = {t}\n\n" for p,t in data[::-1]]) + '\n\n'
		if len(from_json(query)) > n_pages:
			output += f'\n\nOutput truncated to {n_pages} pages!'
	else:
		output = 'No results!'
	return output[:limit]


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
		output = render(wiki_summary_template, **kw).rstrip()
	else:
		output = 'No results! Remember to use only one entity in the query.'
	return output


def wikipedia_set_lang(text):
	return str(wikipedia.set_lang(text))


def _extract_tables_from_html(html):
	soup = BeautifulSoup(html, 'html.parser')
	tables = []
	for tab in soup.find_all('table'):
		table = []
		for tr in tab.find_all('tr'):
			row = []
			for td in tr.find_all(['td','th']):
				row += [td.text.strip().replace(f'\xa0',' ')]
			table += [row]
		tables += [table]
	return tables

def _wikipedia_tables(page, n_tables=2):
	"extract tables from wikipedia page and return them as text"
	if not page or not n_tables:
		return ''
	html = page.html()
	tables = _extract_tables_from_html(html)
	selected = tables[:n_tables] # TODO: find best tables
	output = []
	for table in selected:
		for row in table:
			cells = [x.strip().replace('\xa0',' ') for x in row]
			if len(cells)==1:
				cells = ['\n'+cells[0]]
			output += [' | '.join(cells)]
		output += ['']
	return '\n'.join(output)


# ===[ XXX ]======================================================================================

if __name__=="__main__":
	#pages = wikipedia.search('Europa (moon)')
	#query = wikipedia.suggest('Europa (moon)')
	#pprint(query)
	#print(wikipedia.summary(query))
	#page = wikipedia.page(query)
	#print(page.summary)
	#pprint(dir(page))
	#pprint(wikipedia.summary(pages[0].replace(' ','_'), sentences=10))
	#p = wikipedia.page(pages[0])
	#print(dir(p))
	#print(help(wikipedia.summary))
	#print(wikipedia_search_many('["moons of saturn","moons of jupiter"]'))
	#print(wikipedia_get_data('["moons of saturn","moons of jupiter"]'))
	#p = 'Moons_of_Jupiter'
	#page = wikipedia.page(p)
	#print(_wikipedia_tables(page))
	#tables = _extract_tables_from_html(page.html())
	#pprint(tables[1])
	print(wikipedia_get_data("['Jupiter moons', 'Saturn moons']"))
	print(wikipedia_get_data("['Saturn moons']"))
	#print(wikipedia.search("Saturn moons"))
	#pprint(wikipedia.page('Moons of Saturn'))
	#pprint(wikipedia.page('Saturn moons'))

