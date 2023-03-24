from setuptools import setup, find_packages

setup(
	name='ai_bricks',
	version='0.0.8',
	description='AI adapter / facade',
	author='Maciej Obarski',
	install_requires=[
		'openai',
		'tiktoken',
		'cohere',
		'anthropic',
	],
	packages=find_packages()
)
