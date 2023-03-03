from setuptools import setup

setup(
	name='ai_bricks',
	version='0.0.3',
	description='AI adapter / facade',
	author='Maciej Obarski',
	install_requires=[
		'openai',
		'tiktoken',
		'cohere',
	],
	packages=['ai_bricks']
)
