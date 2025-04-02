from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
# 저장된 데이터를 로드
loaded_case_db = FAISS.load_local(
    folder_path="./data/vector_db_case",
    embeddings=embeddings,
    allow_dangerous_deserialization=True,
    index_name="case_vector"
)

loaded_criteria_db = FAISS.load_local(
    folder_path="./data/vector_db_criteria",
    embeddings=embeddings,
    allow_dangerous_deserialization=True,
    index_name="criteria_vector"
)


_case_retriever = loaded_case_db.as_retriever(k=3)
_criteria_retriever = loaded_criteria_db.as_retriever(k=10)
def get_case_retriever():
    return _case_retriever
def get_criteria_retriever():
    return _criteria_retriever

def double_retrieve(query):
    return _case_retriever.invoke(query)+_criteria_retriever.invoke(query)
