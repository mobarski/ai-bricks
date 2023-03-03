# AI-bricks

🚧 This is pre-alpha software. Anything can change without any notice.

## Installation

`pip install git+https://github.com/mobarski/ai-bricks.git`

## Usage examples

#### OpenAI

```python
from ai_bricks.api import openai
import os

openai.use_key(os.getenv('OPENAI_KEY'))

m1 = openai.model('gpt-3.5-turbo')
text = m1.complete('Hello there!')['text']

m2 = openai.model('text-davinci-003')
text = m2.insert('[insert] Kenobi!')['text']

m3 = openai.model('text-embedding-ada-002')
vector = m3.embedding('Hello there!')['vector']

```

#### co:here

```python
from ai_bricks.api import cohere
import os

cohere.use_key(os.getenv('COHERE_KEY'))

m1 = cohere.model('xlarge')
text = m1.complete('Hello there!')['text']
```

