from jinja2 import Template
import datetime
import re

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
I will forget everything I learned in this session except for the note.
I will name this section "Final Note".
"""

EXAMPLES = """
Example:

Question: Who is higher, King Arthur or Queen Guinevere?
Thought: I shoul look up the height of King Arthur first, then Queen Guinevere and then compare them.
Action: wikipedia-search
Action Input: "King Arthur" height
Observation: ['King Arthur']
Reward: 0
"""

MAIN_PROMPT = """
Answer the following questions as best you can.
Question: {{ question }}

You are augmented with the following actions: {{ ' '.join(actions) }}.
Following modules are already imported in *python-eval*: math, time, datetime, random.
Remember that *python-eval* only evaluetes expressions (up to 300 chars) and not code blocks!
Don't import any module on your own in *python-eval*.
Be careful and avoid off by one errors.
Current time: {{ current_time }}

Use the following format:
Plan: start by making a plan that also includes notes from previous sessions (if any) sorted chronologicaly
Thought: you should always think about what to do
Action: the action to take, should be one of {{ ' '.join(actions) }}
Action Input: the input to the action
Observation: the result of the action
Reward: 1 if progress was made, 0 otherwise
... (this Thought/Action/Action Input/Observation/Reward can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question
{{ examples }}

{% if notes %}Notes from previous sessions:
{% for note in notes %}- {{ note }}
{% endfor %}
{% endif %}
"""

def get_system_prompt(question, actions):
	current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	examples = ""
	notes = [
		'To find moons in the solar system that are bigger than Mercury, look for a list of natural satellites on Wikipedia and compare their sizes to that of Mercury. The 20 natural satellites that are large enough to be gravitationally rounded are: Ganymede, Titan, Callisto, Io, Moon, Europa, Triton, Eris, Pluto, Haumea, Makemake, Ceres, Rhea, Charon, Umbriel, Ariel, Dione, Tethys, Oberon, and Titania. None of these moons are bigger than Mercury, which has a diameter of 4879.4 km.',
		'Unfortunately, I was not able to find any moons in the solar system that are larger than Mercury. However, I can use the list of natural satellites on Wikipedia to compare the sizes of the largest moons to that of Mercury.',
		'There are no known moons in the solar system that are larger than the planet Mercury. However, the largest natural satellites in the solar system are Ganymede, Titan, Callisto, Io, Moon, Europa, Triton, Eris, Pluto, Haumea, Makemake, Ceres, Rhea, Charon, Umbriel, Ariel, Dione, Tethys, Oberon, and Titania.',
		'To find natural satellites in the solar system that are bigger than Mercury, search for "list of natural satellites" on Wikipedia and compare their sizes to that of Mercury. The 20 natural satellites that are large enough to be gravitationally rounded are: Ganymede, Titan, Callisto, Io, Moon, Europa, Triton, Eris, Pluto, Haumea, Makemake, Ceres, Rhea, Charon, Umbriel, Ariel, Dione, Tethys, Oberon, and Titania. None of these moons are bigger than Mercury, which has a diameter of 4879.4 km.',
	]
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
				obs = f'Action "{action}" is not allowed. Allowed actions: {" ".join(actions)}.'
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
