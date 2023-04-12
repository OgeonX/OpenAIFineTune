# prepare_and_finetune.py

import os
import pprint
import glob
import json
import requests
import re
import time
import hashlib
from dotenv import load_dotenv

load_dotenv()

def process_py_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    return content

def remove_comments(code):
    code = re.sub(r'#.*', '', code)
    code = re.sub(r'\'\'\'.*?\'\'\'', '', code, flags=re.DOTALL)
    code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
    return code

def create_prompt_completion_pairs(code_snippets):
    pairs = []
    for snippet in code_snippets:
        cleaned_snippet = remove_comments(snippet)
        function_or_class_match = re.search(r'(def|class)\s+(\w+)', cleaned_snippet)

        if function_or_class_match:
            prompt = f"Write the implementation of the {function_or_class_match.group(1)} '{function_or_class_match.group(2)}':"
            pairs.append({"prompt": prompt, "completion": cleaned_snippet})
    return pairs

def write_jsonl(data, output_file):
    with open(output_file, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

def calculate_checksum(file_path):
    with open(file_path, 'rb') as f:
        file_content = f.read()
        return hashlib.sha256(file_content).hexdigest()

def upload_dataset(api_key, file_path):
    # Create a file entry
    create_file_response = requests.post(
        'https://api.openai.com/v1/files',
        headers={'Authorization': f"Bearer {api_key}"},
        data={
            'purpose': 'fine-tune',
        },
        files={
            'file': (os.path.basename(file_path), open(file_path, 'rb'))
        }
    )
    create_file_response_json = create_file_response.json()

    if 'id' not in create_file_response_json:
        print("Error creating file entry:")
        print(create_file_response_json)
        exit(1)

    file_id = create_file_response_json['id']

    # Wait for the file to be processed
    while True:
        file_status_response = requests.get(
            f'https://api.openai.com/v1/files/{file_id}',
            headers={'Authorization': f"Bearer {api_key}"}
        )
        file_status_response_json = file_status_response.json()

        if 'status' in file_status_response_json and file_status_response_json['status'] == 'processed':
            break

        time.sleep(1)  # Wait for 1 second before checking the file status again

    return {'id': file_id}

def fine_tune_model(api_key, dataset_id, model_name):
    files = [{
        'key': 'file0',
        'filename': 'training_file.jsonl',
        'filetype': 'text',
        'url': f"https://api.openai.com/v1/files/{dataset_id}/content",
        'checksum': calculate_checksum(output_file)
    }]
    
    response = requests.post(
        'https://api.openai.com/v1/fine-tunes',
        headers={'Authorization': f"Bearer {api_key}", 'Content-Type': 'application/json'},
        json={
            'model': model_name,
            'training_file': dataset_id
        }
    )
    return response.json()

def wait_for_fine_tune_completion(api_key, fine_tune_id):
    while True:
        fine_tune_status_response = requests.get(
            f'https://api.openai.com/v1/fine-tunes/{fine_tune_id}',
            headers={'Authorization': f"Bearer {api_key}"}
        )
        fine_tune_status_response_json = fine_tune_status_response.json()

        status = fine_tune_status_response_json['status']
        if status == 'completed':
            break
        elif status == 'error':
            print("Error during fine-tuning:")
            pprint.pprint(fine_tune_status_response_json)
            exit(1)

        time.sleep(10)  # Wait for 10 seconds before checking the fine-tuning status again

    return fine_tune_status_response_json

def list_fine_tunes(api_key):
    response = requests.get(
        'https://api.openai.com/v1/fine-tunes',
        headers={'Authorization': f"Bearer {api_key}"}
    )
    return response.json()

def print_fine_tunes_info(api_key):
    fine_tunes = list_fine_tunes(api_key)
    print("Previous fine-tunes and their costs:")
    for fine_tune in fine_tunes['data']:
        fine_tune_id = fine_tune['id']
        cost = None
        for event in fine_tune['events']:
            if 'message' in event and 'Fine-tune costs' in event['message']:
                cost = event['message'].replace('Fine-tune costs', '').strip()
        print(f"Fine-tune ID: {fine_tune_id}, Cost: {cost}")

# Find all .py files in the current directory and subfolders
current_dir = os.getcwd()
py_files = glob.glob(os.path.join(current_dir, "**/*.py"), recursive=True)

# Process each .py file
processed_files = [process_py_file(file_path) for file_path in py_files]

# Create prompt-completion pairs
prompt_completion_pairs = create_prompt_completion_pairs(processed_files)

# Create "JSON" folder if it doesn't exist
json_folder = os.path.join(current_dir, "JSON")
os.makedirs(json_folder, exist_ok=True)

# Write the prompt-completion pairs to a JSONL file
output_file = os.path.join(json_folder, "output_file.jsonl")
write_jsonl(prompt_completion_pairs, output_file)

api_key = os.getenv("OPENAI_API_KEY")
upload_response = upload_dataset(api_key, output_file)

if 'id' not in upload_response:
    print("Error uploading dataset:")
    print(upload_response)
    exit(1)

dataset_id = upload_response['id']

# Fine-tune the model using the uploaded dataset
model_name = "davinci"  # Replace with the desired base model name
fine_tune_response = fine_tune_model(api_key, dataset_id, model_name)

# Wait for the fine-tuning to complete
fine_tune_id = fine_tune_response['id']
completed_fine_tune = wait_for_fine_tune_completion(api_key, fine_tune_id)

# Print the completed fine-tuning response
pprint.pprint(completed_fine_tune)

# Print all previous fine-tunes and their costs
print_fine_tunes_info(api_key)


