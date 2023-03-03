from setuptools import find_packages, setup

setup(
	name='ai_bricks',
	version='0.0.1',
	description='AI adapter / facade',
	author='Maciej Obarski',
	install_requires=[
		'openai',
		'tiktoken',
	],
	packages=['ai_bricks'] #find_packages()
)
