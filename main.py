from openai import OpenAI
import json
from dotenv import load_dotenv
import os
import requests

from rag_pipeline.rag_pipeline import rag_pipeline

load_dotenv(dotenv_path="./config/.env")

# filename = "YOUR_FILE_NAME"  # ex: ./image.png
 
# url = "https://api.upstage.ai/v1/document-digitization"
# headers = {"Authorization": f"Bearer {os.getenv('UPSTAGE_API_KEY')}"}
# files = {"document": open(filename, "rb")}
# data = {"ocr": "force", "base64_encoding": "['table']", "model": "document-parse"}
# response = requests.post(url, headers=headers, files=files, data=data)

# print(response.json())

print(rag_pipeline("팔협지가 누구야?"))