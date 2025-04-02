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


#각각의 데이터베이스를 기반으로 한 retriever 반환
#QA체인 등을 만들때 retriever 인자로 사용
def get_case_retriever():
    return _case_retriever
def get_criteria_retriever():
    return _criteria_retriever


#각각의 데이터베이스에서 검색한 결과를 합치는 함수
#반환값은 Document 형식
def double_retrieve(query):
    return _case_retriever.invoke(query)+_criteria_retriever.invoke(query)
