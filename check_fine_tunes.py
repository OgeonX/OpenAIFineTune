import os
import requests
from dotenv import load_dotenv
import pprint

load_dotenv()

# Define the cost per second for each base model
COST_PER_SECOND = {
    "davinci": 0.0004
}

def print_all_fine_tunes(api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get("https://api.openai.com/v1/fine-tunes", headers=headers)
    fine_tunes = response.json()

    print("All fine-tunes:")
    for ft in fine_tunes['data']:
        fine_tune_id = ft['id']
        base_model = ft['model']
        created_at = ft['created_at']
        ended_at = ft['updated_at']
        status = ft['status']
        print(f"Fine-tune ID: {fine_tune_id}")
        print(f"Base model: {base_model}")
        print(f"Created at: {created_at}")
        print(f"Status: {status}")
        
        if status == "succeeded":
            duration = ended_at - created_at
            cost = duration * COST_PER_SECOND[base_model]
            print(f"Duration: {duration} seconds")
            print(f"Cost: ${cost:.4f}")

        print("Fine-tune details:")
        pprint.pprint(ft)
        print('-' * 40)

api_key = os.getenv("OPENAI_API_KEY")
print_all_fine_tunes(api_key)
