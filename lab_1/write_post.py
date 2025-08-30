from dotenv import load_dotenv
import os

from openai import OpenAI

load_dotenv(override=True)


# Check the key - if you're not using OpenAI, check whichever key you're using! Ollama doesn't need a key.


openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print(
        "OpenAI API Key not set - please head to the troubleshooting guide in the setup folder"
    )


def init_openai():
    openai = OpenAI(api_key=openai_api_key)
    return openai


def write_post(openai: OpenAI, rules: list[dict]):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # or gpt-4o, gpt-4.1, gpt-3.5-turbo, etc.
        messages=rules,
        temperature=0.7,
        max_tokens=100,
    )
    return response.choices[0].message.content


def write_haiku(client: OpenAI):
    rules = [
        {
            "role": "system",
            "content": "You are a helpful assistant that writes blog posts.",
        },
        {"role": "user", "content": "Write me a haiku about the sea."},
    ]
    post = write_post(client, rules)

    rules_second_part = [
        {"role": "system", "content": "You are a expert in the haiky about the sea."},
        {"role": "user", "content": f"rang the level of the haiku to 10, haiku:{post}"},
    ]
    post_second_part = write_post(client, rules_second_part)
    print(post)
    print(post_second_part)


def main():
    client = init_openai()
    write_haiku(client)


if __name__ == "__main__":
    main()
