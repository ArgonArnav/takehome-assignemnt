from flask import Flask, render_template, request, jsonify
from pydantic import BaseModel
from typing import List
import os
import google.generativeai as genai
# from google.ai import generativelanguage as glm
# from google.cloud import aiplatform


# client = aiplatform.gapic.TextServiceClient()
# client = genai.text.TextServiceClient()
genai.configure(api_key="AIzaSyCGFaJB7dMn0ZidStYJubn2JnUiqWnvwRU")

model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__)

class GetQuestionAndFactsResponse(BaseModel):
    question: str
    facts: List[str]
    status: str

facts_dict = {}

def process_documents(question, documents):
    facts = []

    for doc in documents:
        # Use Gemini Text Query API for fact extraction
        response = model.generate_content(
            # model = model,
            f"Question: {question}\nDocument:\n{doc}",
            # task_type="Extract relevant facts from the document"
        )

        extracted_facts = response.text.strip().split("\n")

        # Update the facts list based on the extracted facts from this document
        for fact in extracted_facts:
            if "remove:" in fact:
                # Remove the fact (similar logic as before)
                fact_to_remove = fact.replace("remove:", "").strip()
                if fact_to_remove in facts:
                    facts.remove(fact_to_remove)
            elif fact not in facts:
                # Add the fact if it's not already in the list
                facts.append(fact)

    return facts

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_question_and_documents', methods=['POST'])
def submit_question_and_documents():
    req_data = request.get_json()
    question = req_data['question']
    documents = req_data['documents']

    global facts_dict
    facts_dict = {  # Clear previous data for idempotency
        'question': question,
        'documents': documents,
        'status': 'processing'
    }

    print(jsonify(facts_dict))

    return jsonify(), 200

@app.route('/get_question_and_facts', methods=['GET'])
def get_question_and_facts():
    global facts_dict

    if facts_dict:
        if facts_dict['status'] == 'processing':
            return jsonify({
                'question': facts_dict['question'],
                'status': 'processing'
            }), 200
        else:
            facts = process_documents(facts_dict['question'], facts_dict['documents'])
            facts_dict['facts'] = facts
            facts_dict['status'] = 'done'

    # Create GetQuestionAndFactsResponse object with validated data
    response = GetQuestionAndFactsResponse(**facts_dict)
    return jsonify(response.dict()), 200



# Consider consolidating these routes if Gemini offers a combined functionality
@app.route('/process', methods=['POST'])
def process():
    question = request.form['question']
    call_logs = [request.files[file].read().decode('utf-8') for file in request.files]

    extracted_facts = process_documents(question, call_logs)

    return render_template('result.html', extracted_facts=extracted_facts)

if __name__ == '__main__':
    app.run(debug=True)
