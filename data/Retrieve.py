from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
# 저장된 데이터를 로드
loaded_case_db = FAISS.load_local(
    folder_path="vector_db_case",
    embeddings=embeddings,
    allow_dangerous_deserialization=True,
    index_name="case_case_1.pdf"
)

loaded_criteria_db = FAISS.load_local(
    folder_path="vector_db_criteria",
    embeddings=embeddings,
    allow_dangerous_deserialization=True,
    index_name="criteria_criteria_1.pdf"
)

# 검색 쿼리 입력
query = "LNG 트럭용에 관한 RFP를 작성하려고 하는데 관련 사례를 찾아줘."

# 검색 실행
results = loaded_case_db.similarity_search(query)

print(results)

