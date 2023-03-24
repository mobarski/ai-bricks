from textwrap import dedent
import re

# TODO: pruning
# TODO: loop detection

EXAMPLE = """
	Example:
	
	Question: Who is higher, King Arthur or Queen Guinevere?
	Thought: I shoul look up the height of King Arthur first, then Queen Guinevere and then compare them.
	Action: [wikipedia-search]
	Action Input: "King Arthur" height
	Observation: ['King Arthur']
"""
EXAMPLE = ""

def v1(question, model, actions, hints='', iter_limit=5):
	out = {'text':''}
	tmp = {'rtt_list':[], 'cost_list':[]}
	print(f'\nQUESTION: {question}\n')
	prompt = f"""
	Answer the following questions as best you can.
	Question: {question}
	
	{hints}

	Use the following format:
	Thought: you should always think about what to do
	Action: the action to take, should be one of {' '.join(actions)}
	Action Input: the input to the action
	Observation: the result of the action
	... (this Thought/Action/Action Input/Observation can repeat N times)
	Thought: I now know the final answer
	Final Answer: the final answer to the original input question

	{EXAMPLE}

	Begin!
	"""
	prompt = dedent(prompt)
	# print(prompt) # XXX
	for i in range(iter_limit):
		x = model.complete(prompt, stop=['Observation:'])
		tmp['rtt_list'].append(x['rtt'])
		tmp['cost_list'].append(x.get('cost',0))
		print()
		print(f"### rtt {x['rtt']:0.2f}s")
		#print('usage',x.get('usage',{}))
		steps = re.findall('(?m)^([A-Z][^:]+):\s*(.*?)(?:\n|$)', x['text'])
		for step in steps:
			print(step[0]+':',step[1])
			pass
		if not steps:
			prompt = prompt + "Reflection: I didn't followed the format. I will try again.\n"
			print("Reflection: I didn't followed the format. I will try again.") # XXX
			continue
		elif steps[-1][0] == 'Final Answer':
			out['status'] = 'ok'
			out['text'] = dict(steps).get('Final Answer', x['text']) # TODO
			out['steps'] = steps
			break
		# elif steps[-2][0] == 'Action' and steps[-1][0] == 'Action Input':
		elif [s[0] for s in steps[-2:]] == ['Action','Action Input']:
			action = steps[-2][1].strip().partition(' ')[0]
			input0 = steps[-2][1].strip().partition(' ')[2] # workaround for not so smart models
			input  = steps[-1][1].strip() or input0
			if action[0]!="[":
				action = '['+action+']'
			if action not in actions:
				obs = f'Action "{action}" is not allowed. Allowed actions: {" ".join(actions)}.'
			else:
				obs = actions[action](input)
			prompt = prompt + x['text'].rstrip() + f'\nObservation: {str(obs).rstrip()}\n'
			print(f"Observation: {str(obs).rstrip()}") # XXX
			#print(prompt) # XXX
		else:
			prompt = prompt + "Reflection: I didn't followed the format. I will try again.\n"
			print("Reflection: I didn't followed the format. I will try again.") # XXX
			continue
	else:
		out['status'] = 'Error: iterations limit reached'
	print() # XXX
	for x in ['rtt_list','cost_list']:
		out[x] = tmp[x]
	return out


def v2(question, model, actions, hints='', iter_limit=5):
	out = {'text':''}
	tmp = {'rtt_list':[], 'cost_list':[]}
	print(f'\nQUESTION: {question}\n')
	sys_prompt = f"""
Answer the following questions as best you can.
Question: {question}

{hints}

Use the following format:
Thought: you should always think about what to do
Action: the action to take, should be one of {' '.join(actions)}
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

{EXAMPLE}
"""
	#print('SYS PROMPT:', sys_prompt) # XXX
	prompt = """Begin!\n"""
	for i in range(iter_limit):
		x = model.complete(prompt, sys_prompt=sys_prompt, stop=['Observation:'])
		tmp['rtt_list'].append(x['rtt'])
		tmp['cost_list'].append(x.get('cost',0))
		print()
		print(f"### rtt {x['rtt']:0.2f}s")
		#print('usage',x.get('usage',{}))
		steps = re.findall('(?m)^([A-Z][^:]+):\s*(.*?)(?:\n|$)', x['text'])
		for step in steps:
			print(step[0]+':',step[1])
			pass
		if not steps:
			prompt = prompt + "Reflection: I didn't followed the format. I will try again.\n"
			print("Reflection: I didn't followed the format. I will try again.") # XXX
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
			prompt = prompt + x['text'].rstrip() + f'\nObservation: {str(obs).rstrip()}\n'
			print(f"Observation: {str(obs).rstrip()}") # XXX
			#print(prompt) # XXX
		else:
			prompt = prompt + "Reflection: I didn't followed the format. I will try again.\n"
			print("Reflection: I didn't followed the format. I will try again.") # XXX
			continue
	else:
		out['status'] = 'Error: iterations limit reached'
	print() # XXX
	for x in ['rtt_list','cost_list']:
		out[x] = tmp[x]
	return out
