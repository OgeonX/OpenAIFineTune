import os
import requests
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Set the API URL and headers
url = "https://api.openai.com/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}",
}

# Make the request to get the list of available models
response = requests.get(url, headers=headers)
models = response.json()

# Print all available models
print("Available models:")
for model in models['data']:
    print(f"- {model['id']}")

# Check if GPT-4 is in the list of available models
gpt4_available = False
for model in models['data']:
    if model['id'] == "gpt-4":
        gpt4_available = True
        break

if gpt4_available:
    print("\nGPT-4 is available to your account.")
else:
    print("\nGPT-4 is not available to your account.")
