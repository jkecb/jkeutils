# jkeutils
Some magical python function made possible by LLMs. Openai usage much simplified.

## Setup
Put OPENAI_API_KEY in your environment variable. 

Then,
> pip install git+https://github.com/jkecb/jkeutils

## Usage
> from jkeutils import EBRequest, aichat, translate
> translate("Hello world!", target_language="Simplified Chinese")
>> '你好，世界！'
> aichat("Who's Joe Biden?")
>>'Joe Biden is an American politician who currently serves as the 46th President of the United States. He was born on November 20, 1942, in Scranton, Pennsylvania. Prior to becoming President, Biden served as Vice President under President Barack Obama from 2009 to 2017. He had a long political career that included serving as a U.S. Senator from Delaware from 1973 to 2009. Biden is a member of the Democratic Party and has focused on issues such as healthcare, climate change, and racial justice throughout his career.'
