
import datetime
from ai_bricks import agent
from ai_bricks import agent_actions
from ai_bricks.api import openai

model = openai.model('gpt-3.5-turbo', temperature=0) # key from OPENAI_KEY env variable

actions = {
	'[wikipedia-summary]': agent_actions.wikipedia_summary,
	'[wikipedia-search]':  agent_actions.wikipedia_search,
	'[python-eval]':       agent_actions.python_eval,
}

hints = f"""
	You are augmented with the following actions: {' '.join(actions)}.
	Action names are always surrounded by squere brackets: [example-action-name].
	Following modules are already imported in [python-eval]: math, time, datetime, random.
	Remember that [python-eval] only evaluetes expressions and not code blocks!
	Don't import any module on your own in [python-eval].
	You explore the world through your actions - DO NOT GIVE UP AFTER A SINGLE SEARCH!!!
	Current time: {datetime.datetime.today()}
"""

question = "What is the sum of every third number from 123 to the year of the recent Russian invasion of Ukraine?"

resp = agent.v1(question, model=model, actions=actions, hints=hints, iter_limit=10)
print(resp)



