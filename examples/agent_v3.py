import sys; sys.path[0:0] = ['.','..'] # for local testing
from ai_bricks.api import openai
from ai_bricks import agent
aa = agent.actions

actions = [
    aa.wikipedia_search,
    aa.python_eval,
]

model = openai.model('gpt-3.5-turbo', temperature=0.5) # key from OPENAI_KEY env variable
a = agent.get('react')(model=model, actions=actions)
answer = a.run("Which planet has the biggest moon - Jupiter or Saturn?")
