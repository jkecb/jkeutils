import json
import os
from exponential_backoff_request import ExponentialBackoffRequest

def openai_post(user_message, system_message="", model="gpt-3.5-turbo"):
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

    requester = ExponentialBackoffRequest()
    response = requester.post(endpoint, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        response_data = response.json()
        response_data["response"] = response_data["choices"][-1]["message"]["content"].strip()
        return response_data
    else:
        response.raise_for_status()

def translate(text, target_language="Simplified Chinese"):
    system_message = "You are a professional translator. You translate accurately, fluently and reliably."
    user_message = f"Translate to {target_language}, return only translated content, don't include original text. Text to be translated:\n{text}"

    response_data = openai_post(user_message,system_message)
    translation = response_data.get("response", "")

    return translation

