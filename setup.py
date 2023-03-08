from setuptools import setup, find_packages

setup(
	name='ai_bricks',
	version='0.0.6',
	description='AI adapter / facade',
	author='Maciej Obarski',
	install_requires=[
		'openai',
		'tiktoken',
		'cohere',
	],
	packages=find_packages()
)
