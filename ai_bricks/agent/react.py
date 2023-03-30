import shelve as kv
import datetime
import re

from jinja2 import Template
def render(template, **kw):
	return Template(template).render(**kw)

# TODO: reward
# TODO: reflexion
# TODO: pruning
# TODO: loop detection


REFLECTION_BAD_FORMAT = "Reflection: I didn't followed the format. I will try again."

REFLECTION_ITERATION_LIMIT = """
Reflection: I didn't find the answer.
I can now write a note to my future self that will help me find the answer next time (it can be longer than just one line).
I can also write a note to my future self that will help me remember what I learned in this session.
I can also include information about the tools I used - what is effective and what is not.
I will forget everything I learned in this session except for the note.
I will name this section "Final Note".
"""

EXAMPLES = """
Examples:

Notes from previous sessions:
- King Arthur is 1.83m tall

Question: Who is higher, King Arthur or Queen Guinevere?
Plan:
1. I know that King Arthur is 1.83m tall.
2. I must find a page about Queen Guinevere
3. I must read that page and find the height of Queen Guinevere
4. Then compare the heights
Thought: I should look up the height of King Arthur first.
Action: wikipedia-find-pages
Action Input: "King Arthur"
Observation: ['King Arthur']
Reward: 0
Thought: Now I should check summary of the first result.
...
"""
EXAMPLES = ""


# `wikipedia-find-pages` gives best resultes when queried with only one entity name at a time.
# `wikipedia-find-pages` returns only a list of page names and not the actual pages, to get the pages use `wikipedia-summary` with a single page name.

MAIN_PROMPT = """
Answer the following questions as best you can.
Question: {{ question }}

You are augmented with the following actions: {{ ' '.join(actions) }}.
Remembber that `wikipedia` can search only for one entity at a time!
Following modules are already imported in `python-eval`: math, time, datetime, random.
Remember that `python-eval` only evaluetes expressions (up to 300 chars) and not code blocks!
Don't import any module on your own in `python-eval`.
Be careful and avoid off by one errors.
Current time: {{ current_time }}

Use the following format:
Plan: start by making a plan that also includes notes from previous sessions (if any) sorted chronologicaly; use information from previous sessions to make a better plan
Thought: you should always think about what to do
Action: the action to take, should be one of {{ ' '.join(actions) }}
Action Input: the input to the action
Observation: the result of the action
Reward: 1 if progress was made, 0 otherwise
... (this Thought/Action/Action Input/Observation/Reward can repeat N times)
... (if you don't want to take action you can skip from one Thought to the next Thought)
Thought: I now know the final answer
Final Answer: the final answer to the original input question
{{ examples }}

{% if notes %}Notes from previous sessions:
{% for note in notes %}- {{ note }}
{% endfor %}
{% endif %}
"""

def get_system_prompt(question, actions, n_notes=2):
	current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	examples = EXAMPLES
	with kv.open('xxx.db') as db:
		notes = db.get('notes', [])[-n_notes:]
	return render(MAIN_PROMPT, **locals())

# ===[ v1 ]====================================================================

def v1(question, model, actions, iter_limit=5):
	out = {'text':''}
	tmp = {'rtt_list':[], 'cost_list':[]}
	#
	print(f'\nQUESTION: {question}\n')
	system_prompt = get_system_prompt(question, actions)
	print('SYSTEM PROMPT', system_prompt) # XXX
	prompt = "Begin!\n"
	for i in range(iter_limit):
		#print('PROMPT', prompt) # XXX
		x = model.complete(prompt, system_prompt=system_prompt, stop=['Observation:'])
		tmp['rtt_list'].append(x['rtt'])
		tmp['cost_list'].append(x.get('cost',0))
		print()
		print(f"### rtt {x['rtt']:0.2f}s")
		#print('usage',x.get('usage',{}))
		steps = re.findall('(?m)^([A-Z][^:]+):\s*(.*?)(?:\n|$)', x['text'])
		for step in steps:
			#print(step[0]+':',step[1])
			pass
		print(x['text'])
		if not steps:
			prompt = prompt + REFLECTION_BAD_FORMAT + "\n"
			print(REFLECTION_BAD_FORMAT) # XXX
			continue
		elif steps[-1][0] == 'Final Answer':
			out['status'] = 'ok'
			out['text'] = dict(steps).get('Final Answer', x['text']) # TODO
			out['steps'] = steps
			break
		elif [s[0] for s in steps[-2:]] == ['Action','Action Input']:
			action = steps[-2][1].strip().partition(' ')[0]
			input0 = steps[-2][1].strip().partition(' ')[2] # workaround for not so smart models
			input  = steps[-1][1].strip() or input0
			if action not in actions:
				obs = f'Invalid action "{action}". Valid action usage example "Action: python-eval"'
			else:
				obs = actions[action](input)
			prompt = prompt + x['text'].rstrip() + f'\nObservation: {str(obs).rstrip()}\n' + 'Reward:'
			print(f"Observation: {str(obs).rstrip()}") # XXX
			#print(prompt) # XXX
		else:
			prompt = prompt + REFLECTION_BAD_FORMAT + "\n"
			print(REFLECTION_BAD_FORMAT) # XXX
			continue
	else:
		out['status'] = 'Error: iterations limit reached'
		prompt = prompt + REFLECTION_ITERATION_LIMIT + "\n"
		x = model.complete(prompt, system_prompt=system_prompt)
		print('\nFINAL ERROR RESP',x['text']) # TODO
	print() # XXX
	for x in ['rtt_list','cost_list']:
		out[x] = tmp[x]
	return out

# ===[ v2 ]====================================================================

import colorama
colorama.init(autoreset=True)
FG = colorama.Fore

def v2(question, model, actions, iter_limit=5, verbose=True):
	out = {'text':''}
	tmp = {'rtt_list':[], 'cost_list':[]}
	def agg_cost(resp:dict):
		tmp['rtt_list'].append(resp['rtt'])
		tmp['cost_list'].append(resp.get('cost',0))
	#
	system_prompt = get_system_prompt(question, actions)
	prompt = "Begin!\n"
	start = ''
	#
	print(FG.MAGENTA+'\nQUESTION:', f'{question}\n')
	print(FG.MAGENTA+'SYSTEM PROMPT:\n', f'{system_prompt}') # XXX
	db = kv.open('xxx.db')
	for i in range(iter_limit):
		#print('PROMPT', prompt) # XXX
		x = model.complete(prompt, system_prompt=system_prompt, start=start, stop=['Observation:'])
		agg_cost(x)
		steps = re.findall('(?m)^([A-Z][^:]+):\s*(.*?)(?:\n|$)', x['text'])
		# 
		if verbose:
			print('---')
			#print(f"### rtt {x['rtt']:0.2f}s")
			#print('usage',x.get('usage',{}))
			for step in steps:
				print(FG.MAGENTA + step[0]+':',step[1])
				pass
			#print(f"{FG.BLUE}{x['text']}")

		# BAD FORMAT
		if not steps:
			prompt = prompt + REFLECTION_BAD_FORMAT + "\n"
			start = ''
			print(REFLECTION_BAD_FORMAT) # XXX
			continue

		# FINAL ANSWER
		elif steps[-1][0] == 'Final Answer':
			out['status'] = 'ok'
			out['text'] = dict(steps).get('Final Answer', x['text']) # TODO
			out['steps'] = steps
			break
		
		# ACTION
		elif [s[0] for s in steps[-2:]] == ['Action','Action Input']:
			action = steps[-2][1].strip().partition(' ')[0]
			input0 = steps[-2][1].strip().partition(' ')[2] # workaround for not so smart models
			input  = steps[-1][1].strip() or input0
			if action not in actions:
				obs = f'Action "{action}" is not allowed. Allowed actions: {" ".join(actions)}.'
			else:
				obs = actions[action](input)
			prompt = prompt + x['text'].rstrip() + f'\nObservation: {str(obs).rstrip()}\n'
			start = 'Reward:' # !!! gpt-3.5-turbo is super sensitive to this ending with space or not !!!
			print(FG.MAGENTA+"Observation:", f"{str(obs).rstrip()}") # XXX
			#print(prompt) # XXX
		
		else:
			prompt = prompt + REFLECTION_BAD_FORMAT + "\n"
			start = ''
			print(REFLECTION_BAD_FORMAT) # XXX
			continue
	else:
		out['status'] = 'Error: iterations limit reached'
		prompt = prompt + REFLECTION_ITERATION_LIMIT + "\n"
		reflection = model.complete(prompt, system_prompt=system_prompt)['text']
		reflection = re.sub('Final Note:\s+','',reflection)
		if 'Final Answer' in reflection:
			print(FG.RED+'FINAL ANSWER FOUND IN FINAL NOTE')
		db['notes'] = db.get('notes',[]) + [reflection]
		print('\nFINAL ERROR RESP', reflection) # TODO
		# print('\nNOTES')
		# for note in db['notes']:
			# print('-',FG.GREEN+note)
	print() # XXX
	for x in ['rtt_list','cost_list']:
		out[x] = tmp[x]
	# XXX
	db.close()
	return out

# ===[ UTILS ]=================================================================

# EXPERIMENTAL / NOT USED
def split(text):
	return re.findall('^(Plan|Thought|Action|Action Input|Observation|Reward|Final Answer):(.*?)(?=\n[A-Za-z ]+:)', text, re.MULTILINE|re.DOTALL)
