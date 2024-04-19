import json
import os

import requests
from groq import Groq


def execute_python_code(code: str) -> str:
    # AgentRun API - Make sure it is running
    response = requests.post("http://localhost:8000/v1/run/", json={"code": code})
    output = response.json()["output"]
    return output


MODEL = "llama3-70b-8192"


client = Groq(api_key="gsk_your api key")

tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": "Sends a python code snippet to the code execution environment and returns the output. The code execution environment can automatically import any library or package by importing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The code snippet to execute. Must be a valid python code. Must use print() to output the result.",
                    },
                },
                "required": ["code"],
            },
        },
    },
]


def chat_completion_request(messages, tools=None, tool_choice="auto", model=MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=0.1,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


def get_answer(query):
    messages = []
    messages.append(
        {
            "role": "system",
            "content": """You are a helpful assistant that helps users. Use the execute_python_code tool to run code if a question is better solved with code. 
            Otherwise, you can use data from your training. You can use any package in the code snippet by simply importing. Like `import requests` would work fine.\n
            Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous.
            """,
        }
    )
    messages.append({"role": "user", "content": query})

    chat_response = chat_completion_request(messages, tools=tools)

    message = chat_response.choices[0].message
    # tool call versus content
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        arg = json.loads(tool_call.function.arguments)["code"]
        print(f"Executing code: {arg}")
        answer = execute_python_code(arg)
        # Optional: call an LLM again to turn the answer to a human friendly response
        query = (
            "Help translate the code output to a human friendly response. This was the user query: "
            + query
            + " The code output is: "
            + answer
        )
        answer = get_answer(query)
    else:
        answer = message.content

    return answer


# 'The answer is 3,952,152 '
print(get_answer("what's 12312 *321?"))
# "The average daily movement of Apple's stock over the last 3 days was $2.39."
print(get_answer("what's the average daily move of Apple stock in the last 3 days?"))
#'The capital of France is Paris.'
print(get_answer("what's the capital of France?"))
