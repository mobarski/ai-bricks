import sys; sys.path[0:0] = ['.','..'] # for local testing
from ai_bricks.api import openai

# global callback
openai.add_callback('before', lambda kw,self: print('(global callback) kw:',kw))

# ===[ model1 ]===============================================================

m1 = openai.model('text-davinci-003', temperature=0)

m1.add_callback('before', lambda kw,self: print('(model1 callback) kw:',kw))

resp1 = m1.complete('emulate word2vec: king - man + woman =')

print('resp1:', resp1)
print('config:', m1.config)

# ===[ model2 ]===============================================================

m2 = openai.model('gpt-3.5-turbo', temperature=0)

m2.add_callback('before', lambda kw,self: print('(model2 callback) kw:',kw))

resp2 = m2.complete('emulate word2vec: car - road + water =')

print('resp2:', resp2)
print('config:', m2.config)

resp3 = m2.complete('emulate word2vec: car - road + water =', sys_prompt='surround the answer with tripple angle brackets like <<<this>>>')
print('resp3:', resp3)
