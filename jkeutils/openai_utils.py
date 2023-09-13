import json
import os
from .exponential_backoff_request import AsyncExponentialBackoffRequest

async def askai(user_message, system_message="", model="gpt-3.5-turbo", return_json=False):
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


async def translate(text, target_language="English"):
    system_message = "You are a professional translator. You translate accurately, fluently and reliably."
    user_message = f"Translate to {target_language}, return only translated content, don't include original text. Text to be translated:\n{text}"

    return await askai(user_message,system_message)

