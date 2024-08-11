from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import json
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from huggingface_hub import HfApi
import requests
import time
from Icon_RAG import *


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///documents.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Document(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)

class Diagram(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    canvas_data = db.Column(db.Text, nullable=False)
    
class T5ForCoordinateRegression(torch.nn.Module):
    def __init__(self, model_path):
        super().__init__()
        self.model = T5ForConditionalGeneration.from_pretrained(model_path)
        self.regression_head = torch.nn.Linear(self.model.config.d_model, 2)

    def forward(self, input_ids, attention_mask):
        outputs = self.model.encoder(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden_state = outputs.last_hidden_state
        regression_output = self.regression_head(last_hidden_state[:, -1])
        return regression_output

# Load the fine-tuned model and tokenizer
model_path = "../../modelinference/T5ForCoordinateRegression/regression-model-flan-t5-base"
tokenizer = T5Tokenizer.from_pretrained(model_path)
model = T5ForCoordinateRegression(model_path)
model.eval()

HUGGING_FACE_API_TOKEN = "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"
MODEL_URL = "https://api-inference.huggingface.co/models/stevensu123/FlanT5PhraseGeneration"

def predict_coordinates(abstract, text, max_length=512):
    input_text = f"predict coordinates: {abstract} [SEP] predict coordinate of this text: {text}"
    inputs = tokenizer(input_text, max_length=max_length, padding="max_length", truncation=True, return_tensors="pt")

    with torch.no_grad():
        outputs = model(input_ids=inputs['input_ids'], attention_mask=inputs['attention_mask'])

    predicted_coords = outputs.squeeze().numpy()
    return predicted_coords[0], predicted_coords[1]  # x, y

def denormalize_coordinates(x_norm, y_norm, x_min, x_max, y_min, y_max):
    x_denorm = x_norm * (x_max - x_min) + x_min
    y_denorm = y_norm * (y_max - y_min) + y_min
    return x_denorm, y_denorm

# Coordinate ranges
x_min, x_max = -58, 3452
y_min, y_max = -179, 4697

def request_model_inference(input_data):
    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(MODEL_URL, headers=headers, json=input_data)
    
    if response.status_code == 503:
        data = response.json()
        if 'estimated_time' in data:
            estimated_time = data['estimated_time']
            print(f"Model is loading. Retrying in {estimated_time} seconds...")
            time.sleep(estimated_time)
            return request_model_inference(input_data)
    return response

# Initialize database
with app.app_context():
    db.create_all()

@app.route('/api/documents/<document_id>', methods=['GET'])
def get_document(document_id):
    document = db.session.get(Document, document_id) #the document_id is the primary key
    if document is None:
        return jsonify({"name": "Untitled Document", "content": ""})
    return jsonify({"name": document.name, "content": json.loads(document.content)})

@app.route('/api/documents/<document_id>', methods=['POST'])
def save_document(document_id):
    data = request.json
    name = data.get('name')
    content = data.get('content')
    content_str = json.dumps(content)  # Convert content to JSON string
    document = db.session.get(Document, document_id)
    if document is None:
        document = Document(id=document_id, name=name, content=content_str)
    else:
        document.name = name
        document.content = content_str
    db.session.add(document)
    db.session.commit()
    return jsonify({"status": "success"}), 200

@app.route('/api/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    try:
        document = Document.query.get(document_id)
        if document is None:
            return jsonify({"error": "Document not found"}), 404

        db.session.delete(document)
        db.session.commit()
        return jsonify({"message": "Document deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.session.close()

@app.route('/api/documents', methods=['GET'])
def get_all_documents():
    documents = Document.query.all()
    documents_data = [{"id": doc.id, "content": json.loads(doc.content), "name": doc.name} for doc in documents]
    return jsonify(documents_data)

@app.route('/api/diagrams/<diagram_id>', methods=['POST'])
def save_diagram(diagram_id):
    data = request.json
    name = data.get('name')
    canvas_data = data.get('canvas_data')
    canvas_data_str = json.dumps(canvas_data)  # Convert content to JSON string
    diagram = db.session.get(Diagram, diagram_id)
    if diagram is None:
        diagram = Diagram(id=diagram_id, name=name, canvas_data=canvas_data_str)
    else:
        diagram.name = name
        diagram.canvas_data = canvas_data_str
    db.session.add(diagram)
    db.session.commit()
    return jsonify({"status": "success"}), 200

@app.route('/api/diagrams/<diagram_id>', methods=['GET'])
def get_diagram(diagram_id):
    diagram = db.session.get(Diagram, diagram_id)
    if diagram is None:
        return jsonify({"name": "untitled diagram", "canvas_data": ""})
    return jsonify({"name": diagram.name, "canvas_data": json.loads(diagram.canvas_data)})

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    abstract = data.get('abstract')
    text = data.get('text')
    
    if not abstract or not text:
        return jsonify({'error': 'Abstract and text are required'}), 400

    try:
        x_pred, y_pred = predict_coordinates(abstract, text)
        x_denorm, y_denorm = denormalize_coordinates(x_pred, y_pred, x_min, x_max, y_min, y_max)
        response = {
            'normalized_coordinates': {
                'x': float(x_pred),
                'y': float(y_pred)
            },
            'denormalized_coordinates': {
                'x': float(x_denorm),
                'y': float(y_denorm)
            }
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# Define Google Cloud Storage settings (Public Access for now)
bucket_name = "scisketch_icon_search"
icon_directory = "icons"

@app.route('/inference', methods=['POST'])
def inference():
    input_data = request.get_json()
    response = request_model_inference(input_data)
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to get phrases from Hugging Face API'}), response.status_code
    
    phrases_response = response.json()
    
    # Extract the generated text
    if isinstance(phrases_response, dict) and 'generated_text' in phrases_response:
        generated_text = phrases_response['generated_text']
    elif isinstance(phrases_response, list) and len(phrases_response) > 0 and 'generated_text' in phrases_response[0]:
        generated_text = phrases_response[0]['generated_text']
    else:
        return jsonify({'error': 'Unexpected response format from Hugging Face API'}), 500
    
    # Split the generated text by commas and strip whitespace
    phrases = [phrase.strip() for phrase in generated_text.split(',') if phrase.strip()]
    
    abstract = input_data.get('inputs')
    results = []
    
    for phrase in phrases:
        x_pred, y_pred = predict_coordinates(abstract, phrase)
        x_denorm, y_denorm = denormalize_coordinates(x_pred, y_pred, x_min, x_max, y_min, y_max)
        
        # Perform icon search and generate URL
        similar_icons = search_similar_icons_by_text(phrase, 1)
        if similar_icons and "ids" in similar_icons:
            icon_path = similar_icons['metadatas'][0][0]['path']
            absolute_url = generate_gcs_url(bucket_name, os.path.join(icon_directory, os.path.basename(icon_path)))
        else:
            absolute_url = None

        results.append({
            'phrase': phrase,
            'x': float(x_denorm),
            'y': float(y_denorm),
            'icon_url': absolute_url  # added the icon url 
        })
    
    return jsonify({'results': results}), 200

if __name__ == '__main__':
    # app.run(host='localhost', port=5000, debug=True)
    app.run(debug=True)
