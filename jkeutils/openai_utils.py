import json
import os
from .exponential_backoff_request import AsyncExponentialBackoffRequest
import tiktoken
import re
import openai
import asyncio

async def askai(user_message, system_message="", model="gpt-3.5-turbo", return_json=False, requester=AsyncExponentialBackoffRequest()):
    if requester=='openai':
        return askai_openai(user_message,system_message,model,return_json)
    
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")

    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }
    messages = [{"role": "user", "content": user_message}]

    if system_message:
        messages.insert(0, {"role": "system", "content": system_message})

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
    
    for i in range(max_retries):
        try:
            response = await openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
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

async def translate(text, target_language="English", model="gpt-3.5-turbo",sentence_spliter=None,requester=AsyncExponentialBackoffRequest()):
    system_message = "You are a professional translator. You translate accurately, fluently and reliably."
    user_message = f"Translate to {target_language}, return only translated content, don't include original text. Text to be translated:\n{text}"

    if '\n' in text:
        text_list=text.splitlines()
        translated=await asyncio.gather(*[translate(text) for text in text_list])
        clean_translated=[i.split('\n')[0] for i in translated]
        return '\n'.join(clean_translated)    
    
    # Check model length
    num_tokens=count_tokens(user_message+system_message)
    model_length=model_token_length(model)
    if model_length is None :
        model_length=4000
    if num_tokens > model_length/2 :
        if num_tokens < 5000:
            print(f"Part using gpt-3.5-turbo-16k instead as input has {num_tokens} tokens")
            model="gpt-3.5-turbo-16k"
        elif num_tokens>5000: # Translate half at a time.
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
            return sentence_spliter.join([await translate(first_half,target_language,model),await translate(second_half,target_language,model)])
        
    return await askai(user_message,system_message,model=model,requester=requester)

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

