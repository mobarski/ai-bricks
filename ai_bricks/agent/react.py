from textwrap import indent,dedent
import datetime
import re

# colors
import colorama
colorama.init(autoreset=True)
FG=colorama.Fore

# XXX
def log(id,*a):
	with open(f'log{id}.txt','a') as f:
		print(*a, file=f)

# ===[ UTILS ]=================================================================

# templates
from jinja2 import Template
def render(template, **kw):
	"render template with jinja2"
	return Template(template).render(**kw)

def get_doc(fun):
	"get docstring without newlines and extra spaces"
	doc = fun.__doc__ or ''
	doc = re.sub('\s+',' ',doc)
	return doc

# ===[ PROMPTS ]===============================================================


REFLECTION_BAD_FORMAT = "Reflection: I didn't followed the format. I will try again."

REFLECTION_NO_ANSWER = """
Reflection: I didn't find the answer.
I can now write a note to my future self that will help me find the answer next time (it can be longer than just one line).
I can also write a note to my future self that will help me remember what I learned in this session.
I can also include information about the tools I used - what is effective and what is not.
I will forget everything I learned in this session except for the note.
I will name this section "Final Note".
"""

EXAMPLES = """
"""

POST_OBSERVATION_REMINDER = "The next item must be a Summary followed by a Thought!"
POST_OBSERVATION_START = "" # response priming


MAIN_PROMPT = """
Task: Answer the following question as best you can.
Question: {{ question }}
{#Current time: {{ current_time }}#}

You are augmented with the following actions:
{% for action,doc in zip(actions,docs) %}
- {{ action }}: {{ doc }}
{%- endfor %}

Use the following response protocol and format:
{#Plan:
- start by making a plan
- use information from previous sessions to make a better plan#}
Question: {{ question }}
Thought: you should always think about what to do
Action: the action to take (only the name, not the arguments)
Input: the input to the action
Observation: the result of the action{#; you will see this only once, so store anything important in the next Memory field#}
Summary: key takeways - extract all data (esp numeric data) relevant to the question{#the most important information from the Observation that you want to remember#}, one item per line
Repeat:
- this Question/Thought/Action/Input/Observation{#/Memory#}{#/Reward#}/Summary can repeat N times
- if you don't want to take any action you can skip from one Thought to the next Thought
{# Reward: 1 if progress was made, 0 otherwise #}
{# Summary: knowledge extract from the last (and only the last!) observation; this field will stay in the context #}
Thought: I now know the final answer
Final Answer: the final answer to the original input question


Important:
- always follow the protocol - Thought, Action, Input, Observation, Summary, Thought, etc
- never use empty Input 
- you don't know current time and date
{#
- always follow Observation with Observation Summary, always!
- never use "and", "or", "vs" or "," in wikipedia input
#}
{{ examples }}

{% if notes %}Notes from previous sessions:
{% for note in notes %}- {{ note }}
{% endfor %}
{% endif %}
"""

# ===[ v3 ]====================================================================

class Agent:
	"Zero-shot ReAct agnet"
	def __init__(self, model, actions, id='a0'):
		self.id = id
		self.model = model
		self.actions = actions
		self.action_by_name = {a.__name__:a for a in actions}
		self.db = {} # TODO
		self.verbose = False
		self.cost = {'rtt_list':[], 'cost_list':[], 'total_tokens_list':[]}

	def run(self, question, n_turns=5, verbose=True) -> str:
		"run agent for n_turns, return answer if found"
		self.verbose = verbose
		self.set_system_prompt(question)
		self.prompt = 'Begin!\n'
		self.start = 'Plan:'
		answer = ''
		# main loop
		for i in range(n_turns):
			resp = self.complete()
			self.prompt += resp['text'].strip()+'\n' # TODO: here?
			log(1,'---')
			log(1,resp['text'].strip())
			steps = self.parse_steps(resp['text'])
			if verbose:
				print_steps(steps)
				print('---') # indicate end of model response
			answer = self.act(steps)
			if answer:
				break
		else:
			self.reflect_on_end()
		self.on_end(question, answer)
		return answer

	def act(self, steps) -> str:
		"act on steps, return answer if found"
		answer = ''
		# protocol error
		if not steps:
			self.reflect_on_error("I didn't follow the protocol.")
		# final answer
		elif steps[-1][0] == 'Final Answer':
			answer = steps[-1][1].strip()
		# action
		elif steps[-1][0] == 'Input' and steps[-2][0] == 'Action':
			action = steps[-2][1].strip()
			if action in self.action_by_name:
				input = steps[-1][1]
				self.action(action, input)
			else:
				self.reflect_on_error('I used an action that I am not supposed to use.')
		# protocol error
		else:
			self.reflect_on_error("I didn't follow the protocol.")
		#
		return answer
	
	def action(self, action, input):
		"perform action"
		fun = self.action_by_name[action]
		try:
			observation = fun(input)
		except Exception as e:
			observation = str(e)
		observation = normalize_output(observation)
		self.clear_observations()
		reminder = POST_OBSERVATION_REMINDER
		self.prompt += f'Observation: {observation}\nReminder: {reminder}\n'
		self.start = POST_OBSERVATION_START
		if self.verbose:
			print_steps([('Observation', observation)], FG.YELLOW)
			print_steps([('Reminder', reminder)], FG.CYAN)
		
	def complete(self) -> dict:
		"get response from model"
		resp = self.model.complete(self.prompt,
			     system_prompt=self.system_prompt,
				 start=self.start,
				 stop=['Observation:','Human:'])
		self.agg_cost(resp)
		return resp

	def parse_steps(self, text) -> list:
		"return list of tuples: (step-name, step-text)"
		pattern = "^([A-Z][^:]+):(.*?)(?=\\Z|^[A-Z][A-Za-z0-9 ]+:)"
		steps = re.findall(pattern, text, re.DOTALL|re.MULTILINE)
		return steps		

	def on_end(self, question, answer):
		"called at the end of the agent's run"
		if self.verbose:
			tokens = sum(self.cost['total_tokens_list'])
			cost_sum = sum(self.cost['cost_list'])
			rtt_sum = sum(self.cost['rtt_list'])
			cnt = len(self.cost['rtt_list'])
			print(f'\n{FG.RED}DONE IN {FG.WHITE}{rtt_sum:0.1f}s{FG.RED} ({cnt} steps, {rtt_sum/cnt:0.2f}s per step) FOR {FG.WHITE}${cost_sum:0.4f}{FG.RED} ({tokens} {self.model.name} tokens)')
			print(f'\n{FG.RED}Question: {FG.WHITE}{question.strip()}')
			print(f'\n{FG.RED}Final Answer: {FG.WHITE}{answer}\n')

	def clear_observations(self):
		"clear past observations from the prompt"
		pattern = "^Observation:(.*?)(?=\\Z|^[A-Z][A-Za-z0-9 ]+:)"
		#pattern = "^([A-Z][^:]+):(.*?)(?=\\Z|^[A-Z][A-Za-z0-9 ]+:)"
		before = len(self.prompt) # XXX
		log(0,'='*80)
		log(0,'prompt_before_clear', before, self.prompt)
		#self.prompt = re.sub(pattern, '', self.prompt, flags=re.DOTALL|re.MULTILINE)
		self.prompt = re.sub(pattern, 'Observation: (REMOVED)\n', self.prompt, flags=re.DOTALL|re.MULTILINE)
		# steps = self.parse_steps(self.prompt)
		# for i,_ in enumerate(steps):
		# 	if steps[i][0]=='Observation':
		# 		steps[i] = ('Observation', '(REMOVED)')
		#new_prompt = '\n'.join([f'{s[0]}: {s[1].strip()}' for s in steps])
		#self.prompt = new_prompt
		after = len(self.prompt) # XXX
		log(0,'prompt_after_clear', after, self.prompt)
		print(FG.RED+f'CLEAR: {after-before}') # XXX

	def reflect_on_error(self, msg):
		self.prompt += f'Reflection: {msg}\n'
		self.start = '' # TODO: check Plan: and Thought:
		if self.verbose:
			print_steps([('Reflection', msg)], FG.RED)
	
	def reflect_on_end(self):
		pass # TODO

	def reflect_on_reward(self):
		pass # TODO

	def set_system_prompt(self, question):
		# TODO: notes
		kw = {
			'question': question,
			'actions': [a.__name__ for a in self.actions],
			'docs':    [get_doc(a) for a in self.actions],
			'current_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			'getattr': getattr,
			'dedent': dedent,
			'zip': zip,
		}
		self.system_prompt = render(MAIN_PROMPT, **kw)
		if self.verbose:
			steps = self.parse_steps(self.system_prompt)
			print_steps(steps, color=FG.CYAN)

	def agg_cost(self, resp):
		self.cost['rtt_list'].append(resp['rtt'])
		self.cost['cost_list'].append(resp.get('cost',0))
		self.cost['total_tokens_list'].append(resp.get('usage',{}).get('total_tokens',0))
	
# =============================================================================

def normalize_output(x):
	text = str(x).strip()
	h = '\n' if '\n' in text else ''
	return h+text

def print_steps(steps, color=FG.MAGENTA):
	for k,v in steps:
		if k=='Reward':
			v = v.strip() # handle ... in the system_prompt
		else:
			v = normalize_output(v)
		print(f'{color}{k}:', v)

def test_parse_steps():
	from textwrap import dedent
	text = """
		Plan: - search-wikipedia for Leo DiCaprio's girlfriend
		- extract age from the response
		- python-eval the age to the 0.43 power
		Thought: I 
		Action: search-wikipedia
		Action Input: Who is Leo DiCaprio's girlfriend?
		Observation:
		Her name is Camila Morrone.
		She is 23 years old.
		Reward: 1
		Action: python-eval
		Action Input: 23**0.43
		Observation: 3.85
		Reward: 1
	"""
	text = dedent(text)
	print(FG.YELLOW+text)
	a = Agent(None,[])
	steps = a.parse_steps(text)
	print_steps(steps)

def test_system_prompt():
	def action1(x):
		"example action"
		return x

	def action2(x):
		"""Another example action.
		This time with multiline docstring.
		Pretty fancy, huh?
		"""
		return x
	a = Agent(None,[])
	a.actions = [action1, action2]
	a.set_system_prompt('QUESTION')
	system_prompt = a.system_prompt
	steps = a.parse_steps(system_prompt)
	print_steps(steps)

if __name__=="__main__":
	#test_parse_steps()
	test_system_prompt()
