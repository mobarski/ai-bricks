# AI-bricks

🚧 This is pre-alpha software. Anything can change without any notice.

## Installation

`pip install git+https://github.com/mobarski/ai-bricks.git`

## Idea

The main idea behind ai-bricks is to have one, simple interface to different models / agents / chains / etc.

For example - all models support `complete` and `complete_many` regardless of batch support in the api.

Another example - chat based models and instruct-like models use the same `complete` interface. You can pass system_prompt to instruct-like model and it will be handled properly.

**Basically - you can easily swap models.**

Also: all models return usage information ('total_tokens', 'completion_tokens','prompt_tokens'), API cost and round-trip-time.

## Usage examples

#### OpenAI

```python
from ai_bricks.api import openai

# complete
m1 = openai.model('gpt-3.5-turbo') # API_KEY read from env variables OPENAI_KEY or OPENAI_API_KEY
text = m1.complete('Hello there!')['text']
text1, text2 = m1.complete_many(['Hello!','Bonjour!'])['texts']

# insert
m2 = openai.model('text-davinci-003')
text = m2.insert('[insert] Kenobi!')['text']

# embed
m3 = openai.model('text-embedding-ada-002')
vector = m3.embed('Hello there!')['vector']

```

#### Anthropic

```python
from ai_bricks.api import anthropic

m1 = anthropic.model('claude-instant-v1') # API_KEY from env variables ANTHROPIC_KEY or ANTHROPIC_API_KEY
text = m1.complete('Hello there!')['text']
text1, text2 = m1.complete_many(['Hello!','Bonjour!'])['texts']
```



#### co:here

```python
from ai_bricks.api import cohere
import os

cohere.use_key(os.getenv('COHERE_KEY')) # NOT REQUIRED as API KEY by default is read from env variables

# complete
m1 = cohere.model('xlarge')
text = m1.complete('Hello there!')['text']

# embed
vector = m1.embed('Hello there!')['vector']
vectors = m1.embed_many(['Hello there!','General Kenobi!'])['vectors']

```

