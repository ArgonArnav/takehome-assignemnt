from flask import Flask, render_template, request, jsonify
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
import requests

# Configure Google Generative AI
genai.configure(api_key="AIzaSyCGFaJB7dMn0ZidStYJubn2JnUiqWnvwRU")

# Initialize Flask app
app = Flask(__name__)

# Define Pydantic model for response
class GetQuestionAndFactsResponse(BaseModel):
    question: str
    facts: List[str]
    status: str

# Store data globally
facts_dict = {
    'question': '',
    'documents': [],
    'facts': [],
    'status': ''
}

# Function to process documents and extract facts
def process_documents(question, documents):
    facts = []

    for doc in documents:
        response = genai.GenerativeModel('gemini-pro').generate_content(
            f"Question: {question}\nDocument:\n{doc}"
        )

        extracted_facts = response.text.strip().split("\n")

        for fact in extracted_facts:
            if "remove:" in fact:
                fact_to_remove = fact.replace("remove:", "").strip()
                if fact_to_remove in facts:
                    facts.remove(fact_to_remove)
            elif fact not in facts:
                facts.append(fact)

    return facts

# Route for home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to submit question and documents
@app.route('/submit_question_and_documents', methods=['POST'])
def submit_question_and_documents():
    req_data = request.get_json()

    if not req_data:
        return jsonify(error="No JSON data received"), 400
    
    question = req_data.get('question')
    documents = req_data.get('documents')

    if not question:
        return jsonify(error="Question not provided"), 400

    if not documents:
        return jsonify(error="Documents not provided"), 400

    if not isinstance(documents, list):
        return jsonify(error="Documents should be a list"), 400

    documents_content = []
    for doc_url in documents:
        try:
            response = requests.get(doc_url)
            if response.status_code == 200:
                documents_content.append(response.text)
            else:
                return jsonify(error=f"Failed to fetch document from {doc_url}"), 400
        except Exception as e:
            return jsonify(error=f"Failed to fetch document from {doc_url}: {str(e)}"), 400

    global facts_dict
    facts_dict = {
        'question': question,
        'documents': documents_content,
        'status': 'processing'
    }

    return jsonify({}), 200

# Route to get question and facts
@app.route('/get_question_and_facts', methods=['GET'])
def get_question_and_facts():
    global facts_dict

    if facts_dict:
        if facts_dict['status'] == 'processing':
            return jsonify({
                'question': facts_dict['question'],
                'status': 'processing'
            }), 200
        elif facts_dict['status'] == 'done':
            facts = process_documents(facts_dict['question'], facts_dict['documents'])
            facts_dict['facts'] = facts
            response = GetQuestionAndFactsResponse(**facts_dict)
            facts_dict = {
                'question': '',
                'documents': [],
                'facts': [],
                'status': ''
            }
            return jsonify(response.dict()), 200

    return jsonify(error="No question and documents submitted"), 400

# Route to process question and documents
@app.route('/process', methods=['POST'])
def process():
    question = request.form['question']
    documents = request.files.getlist('documents')
    call_logs = [doc.read().decode('utf-8') for doc in documents]

    global facts_dict
    facts_dict = {
        'question': question,
        'documents': call_logs,
        'status': 'done'
    }

    extracted_facts = process_documents(question, call_logs)

    return render_template('result.html', extracted_facts=extracted_facts)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
