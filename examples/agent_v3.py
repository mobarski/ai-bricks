import sys; sys.path[0:0] = ['.','..'] # for local testing
from ai_bricks.api import openai
from ai_bricks import agent

agent.actions.wikipedia_summaries.__name__="wikipedia_search"
actions = [
    agent.actions.wikipedia_summaries,
    agent.actions.python_eval,
]

model = openai.model('gpt-3.5-turbo', temperature=0.5) # key from OPENAI_KEY env variable
a = agent.get('react')(model=model, actions=actions)
answer = a.run("Which planet has the biggest moon - Jupiter or Saturn?")
