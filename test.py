import requests
import json

url = "http://127.0.0.1:5000/submit_question_and_documents"
data = {
    "question": "What are our product design?",
    "documents": ["https://raw.githubusercontent.com/ArgonArnav/TAKEHOME-ASSIGNMENT/main/call-logs.txt"]
}

headers = {'Content-type': 'application/json'}

response = requests.post(url, data=json.dumps(data), headers=headers)
print(response.text)