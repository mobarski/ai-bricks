import sys; sys.path[0:0] = ['.','..'] # for local testing

from ai_bricks.api import openai
from ai_bricks import agent

aa = agent.actions
#aa.wikipedia_search.__name__ = 'wikipedia-index'
actions = [
    #aa.wikipedia_search,
    aa.wikipedia_search_many,
    aa.python_eval,
]

#q = "Who is Leo DiCaprio's girlfriend? What is her current age raised to the 0.43 power?"
#q = "Which planet has the biggest moon - Jupiter or Saturn?"
q = "Which planet has the moon with the biggest surface gravity force - Jupiter or Saturn?"
#q = "Which planet has bigger moon - Jupiter or Saturn?"

model = openai.model('gpt-3.5-turbo', temperature=0.5) # key from OPENAI_API_KEY env variable
a = agent.get('react')(model=model, actions=actions)
answer = a.run(q)
