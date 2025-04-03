from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_upstage import UpstageDocumentParseLoader
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.document_loaders import TextLoader
#import crawring
print("dataloader is loaded!")
embeddings = OpenAIEmbeddings()
dimension_size = len(embeddings.embed_query("hello world"))

db_case = FAISS(
    embedding_function=OpenAIEmbeddings(),
    index=faiss.IndexFlatL2(dimension_size),
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)

db_criteria = FAISS(
    embedding_function=OpenAIEmbeddings(),
    index=faiss.IndexFlatL2(dimension_size),
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)

def load_data(file_path):
    if file_path.endswith(".pdf"):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=128
        )
        loader = UpstageDocumentParseLoader(
            file_path,
            ocr="auto",
            api_key="up_gmnfyAHKJDRkVBrd8949aKfcK80EF",
            split="page",
            output_format="text",
            coordinates=False,
        )
        pages = loader.load()
        pages = text_splitter.split_documents(pages)
        return pages
    elif file_path.endswith(".txt"):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=256,
            chunk_overlap=64
        )
        loader = TextLoader(file_path, encoding='utf-8')
        pages = loader.load()
        pages = text_splitter.split_documents(pages)
        return pages


for file in os.listdir("./data/data_source"):
    print(file)
    file_path = f"./data/data_source/{file}"
    if file.startswith("case_"): # 케이스 데이터 로드
        db_case.add_documents(documents=load_data(file_path))
    elif file.startswith("criteria_"): # 기준 데이터 로드   
        db_criteria.add_documents(documents=load_data(file_path))
db_case.save_local(folder_path="./data/vector_db_case", index_name="case_vector")
db_criteria.save_local(folder_path="./data/vector_db_criteria", index_name="criteria_vector")



