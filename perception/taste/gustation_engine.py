from transformers import AutoModel, AutoTokenizer
import torch
import numpy as np
import requests
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import json

class GustationEngine:
    def __init__(self):
        # Initialize the transformer model
        self.tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
        self.model = AutoModel.from_pretrained('distilbert-base-uncased')
        
        # Initialize scikit-learn model
        self.classifier = Pipeline([
            ('scaler', StandardScaler()),
            ('svc', SVC(probability=True))
        ])

    def taste_embedding(self, description):
        # Tokenize and embed using transformers
        inputs = self.tokenizer(description, return_tensors='pt')
        outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).detach().numpy()

    def train(self, X, y):
        # Train the scikit-learn model
        embeddings = np.array([self.taste_embedding(x) for x in X])
        self.classifier.fit(embeddings, y)

    def predict(self, description):
        # Predict taste category
        embedding = self.taste_embedding(description)
        return self.classifier.predict(embedding), self.classifier.predict_proba(embedding)

    def get_flavor_data(self, compound_name):
        # Use the FlavorDB API to fetch compound data
        response = requests.get(f'https://flavordb.example/api/v1/compound/{compound_name}')
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            return None
