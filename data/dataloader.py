import pandas as pd
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv 
import os
from langchain_upstage import UpstageDocumentParseLoader
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore

embeddings = OpenAIEmbeddings()
dimension_size = len(embeddings.embed_query("hello world"))

db = FAISS(
    embedding_function=OpenAIEmbeddings(),
    index=faiss.IndexFlatL2(dimension_size),
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)

def load_pdf_data(file_path):
    file_path = file_path
    loader = UpstageDocumentParseLoader(file_path, ocr="auto",api_key="up_gmnfyAHKJDRkVBrd8949aKfcK80EF",split="page",output_format="text",coordinates=False)
    pages = loader.load() 
    text_splitter = RecursiveCharacterTextSplitter( # 문장 분리
    chunk_size=256,
    chunk_overlap=64)
    pages = text_splitter.split_documents(pages)
    return pages


for file in os.listdir("data_sorce"):
    file = "case_1.pdf"
    file_path = f"data_sorce\{file}"
    if file.startswith("case_"): # 케이스 데이터 로드
        db.add_documents(documents=load_pdf_data(file_path))
        db.save_local(folder_path="vector_db_case", index_name=f"case_{file}")
    elif file.startswith("criteria_"): # 기준 데이터 로드   
        db.add_documents(documents=load_pdf_data(file_path))
        db.save_local(folder_path="vector_db_criteria", index_name=f"criteria_{file}")



