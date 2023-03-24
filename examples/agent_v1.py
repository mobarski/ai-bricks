import sys; sys.path[0:0] = ['.','..'] # for local testing
from ai_bricks import agent
from ai_bricks import agent_actions
from ai_bricks.api import openai
from ai_bricks.api import anthropic
import datetime

# model = openai.model('text-davinci-003', temperature=0) # key from OPENAI_KEY env variable
model = openai.model('gpt-3.5-turbo', temperature=0) # key from OPENAI_KEY env variable
# model = openai.model('gpt-4', temperature=0) # key from OPENAI_KEY env variable
# model = anthropic.model('claude-instant-v1', temperature=0.5) # key from ANTHROPIC_KEY env variable
# model = anthropic.model('claude-v1', temperature=0.5) # key from ANTHROPIC_KEY env variable
# model = anthropic.model('claude-v1.2', temperature=0.5) # key from ANTHROPIC_KEY env variable

actions = {
	'[wikipedia-summary]': agent_actions.wikipedia_summary,
	'[wikipedia-search]':  agent_actions.wikipedia_search,
	'[python-eval]':       agent_actions.python_eval,
}

hints = f"""
	You are augmented with the following actions: {' '.join(actions)}.
	Action names are always surrounded by squere brackets: [example-action-name].
	Following modules are already imported in [python-eval]: math, time, datetime, random.
	Remember that [python-eval] only evaluetes expressions (up to 300 chars) and not code blocks!
	Don't import any module on your own in [python-eval].
	Current time: {datetime.datetime.today()}
"""

question = "What is the sum of square root of every third number from 123 to the year of the recent Russian invasion of Ukraine?"

resp = agent.v2(question, model=model, actions=actions, hints=hints, iter_limit=10)
print('agent response:', resp)
rtt_sum = sum(resp["rtt_list"])
cost_sum = sum(resp.get('cost_list',[]))
cnt = len(resp["rtt_list"])

print(f'\nDONE IN {rtt_sum:0.1f}s AND {cnt} steps ({rtt_sum/cnt:0.2f}s per step) FOR ${cost_sum:0.4f}')
print()
print('FINAL ANSWER:', resp['text'])
print()
