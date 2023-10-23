from setuptools import setup, find_packages

setup(
    name='jkeutils',
    version='0.3.2',
    packages=find_packages(),
    install_requires=[
        'requests',
        'asyncio',
        'aiohttp',
        'tiktoken',
        'openai'
    ],
)
