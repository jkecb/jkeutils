import json
import os
from .exponential_backoff_request import AsyncExponentialBackoffRequest
import tiktoken
import re
import openai
import asyncio

async def askai(user_message, system_message="", model="gpt-3.5-turbo", return_json=False):
    
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")

    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    if isinstance(user_message, str):
        messages = [{"role": "user", "content": user_message}]
        if system_message:
            messages.insert(0, {"role": "system", "content": system_message})
    elif isinstance(user_message, list):
        messages=user_message # TODO: Add list value check
    else:
        raise TypeError("user_message should be either a string or a list of strings.")


    payload = {
        "model": model,
        "messages": messages
    }

    requester = AsyncExponentialBackoffRequest()
    response = await requester.post(endpoint, headers=headers, json=payload)  # Using json=payload directly

    if response.status == 200:  # Using .status instead of .status_code
        response_data = await response.json()  # await the asynchronous .json() method
        if return_json:
            return response_data
        else:
            return response_data["choices"][-1]["message"]["content"].strip()
            
    else:
        response.raise_for_status()  # This remains the same, but be sure aiohttp has this method. If not, you might need to raise an exception manually based on the status code.

async def askai_openai(user_message, system_message="", model="gpt-3.5-turbo", max_retries=3, return_json=False):
    """
    Communicates with OpenAI's API to get a model's response.
    
    :param user_message: Message from the user.
    :param system_message: System message to preface the conversation.
    :param model: Model to use for generating the response.
    :param max_retries: Number of retries in case of an error.
    :param return_json: Whether to return the full JSON response or just the content.
    :return: Model's response or full JSON response based on return_json.
    """
    if isinstance(user_message, str):
        if system_message:
            messages = [{"role": "system", "content": system_message}]
        else:
            messages = []
        messages.append({"role": "user", "content": user_message})
    elif isinstance(user_message, list):
        messages=user_message # TODO: Add list value check
    else:
        raise TypeError("user_message should be either a string or a list of strings.")

    for i in range(max_retries):
        try:
            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=messages
            )
            
            if return_json:
                return response.json()
            else:
                return response.choices[-1].text.strip()

        except openai.error.OpenAIError as e:
            if i < max_retries - 1:  # i is 0 indexed
                await asyncio.sleep(2)  # Wait for 2 seconds before retrying
                continue
            else:
                raise e  # If max_retries is reached, raise the error

    return None  # This will be reached if for some reason the loop completes without returning

async def translate(text, target_language="English", model="gpt-3.5-turbo",two_pass=True):
    system_message = "You are a professional translation engine. You translate accurately, fluently and reliably."
    user_message = f"Translate to {target_language}, return only translated content, don't include original text. Text to be translated:\n{text}"
    translation_prompt=f'''
Translation Guideline:
- Retain specific terms/names, put it after the translation in brackets, for example: "乔（Joe）".
- Divide the translation into two parts and print each result:
1. Translate directly based on the content, without omitting any information.
2. Based on the first direct translation, rephrase it to make the content more easily understood and conform to {target_language} expression habits, while adhering to the original meaning.
Without any comment, return the result in the following python dict format:
[{{"direct_translation": "direct translation here",
"better_translation": "better translation here",}}]
Reply OK to this message and I'll send you text to be translated to {target_language} afterwards.'''
    args = {
        'target_language': target_language,
        'model': model,
        'two_pass': two_pass
    }
    
    # If input is list transalte every item.
    if isinstance(text,list):
        return await asyncio.gather(*[translate(entry,**args) for entry in text])   
        
    # Check model length
    num_tokens=count_tokens(translation_prompt+system_message+text)
    model_length=model_token_length(model)

    # If multiple paragraphs and too long use recursion to split.
    if '\n' in text and num_tokens>=1200:
        text_list=text.splitlines()
        translated=await asyncio.gather(*[translate(text,**args) for text in text_list])
        # clean_translated=[i.split('\n')[0] for i in translated]
        return '\n'.join(translated)    
    
    if model_length is None :
        model_length=4000
    if num_tokens > model_length/2 :
        if num_tokens < 5000:
            print(f"Part using gpt-3.5-turbo-16k instead as input has {num_tokens} tokens")
            model="gpt-3.5-turbo-16k"
        elif num_tokens>=5000: # Translate half at a time.
            print(f'Too long, spliting...')
            if '。' in text:
                sentence_spliter='。'
            if '. ' in text:
                sentence_spliter='. '
            if sentence_spliter is None:
                raise ValueError(f"The input has {num_tokens} tokens, which exceeds 5000 tokens.")
            sentence_list=text.split(sentence_spliter)
            mid=len(sentence_list) // 2
            first_half=sentence_spliter.join(sentence_list[:mid])
            second_half=sentence_spliter.join(sentence_list[mid:])
            if 'english' in target_language.lower():
                join_spliter='. '
            if 'chinese' in target_language.lower():
                join_spliter='。'
            return join_spliter.join([await translate(first_half,**args),await translate(second_half,**args)])
    
    if two_pass==True:
        dialogue_msg= [
            {"role": "system", "content": system_message},
            {"role": "user", "content": translation_prompt},
            {"role": "assistant", "content": "OK"},
            {"role": "user", "content": f'{{"text": "{text}","target_language": "{target_language}",}}'},
        ]

        response_text=await askai(dialogue_msg,model=model)
        pattern = r'"better_translation":[\s\n]*[“"”]([\s\S]*?)[“"”]?,?[\s\n]*}'
        match = re.search(pattern, response_text)
        if match:
            return match.group(1)
        else:
            return response_text
    else:
        return await askai(user_message,system_message,model=model)

def count_tokens(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def model_token_length(model_name):
    # Regex pattern to match numbers followed by 'k' surrounded by special characters or at the start/end of the string
    pattern = r'(?<=[^a-zA-Z0-9])(\d+)k(?=[^a-zA-Z0-9]|$)|^(\d+)k'
    
    # Find matches
    matches = re.findall(pattern, model_name)
    
    # If a match is found, convert the number before 'k' to an integer, multiply by 1000 and return
    if matches:
        # Take the first match's first capturing group (as it's a tuple due to the two capturing groups in the regex)
        number_str = [group for group in matches[0] if group][0]
        return int(number_str) * 1000
    else:
        return None

