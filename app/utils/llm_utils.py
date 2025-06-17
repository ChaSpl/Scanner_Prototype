import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def query_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-4",  # Or "gpt-3.5-turbo" if you're budget-sensitive
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts structured data from CVs."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content
