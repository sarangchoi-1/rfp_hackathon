import os
import json
import requests
from typing import List
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(dotenv_path=env_path)

# API 키 불러오기
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# 1. Upstage Document Parser API 호출
def extract_text_from_pdf(filepath: str) -> List[str]:
    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}
    files = {"document": open(filepath, "rb")}
    data = {
        "ocr": "force",
        "base64_encoding": "['table']",
        "model": "document-parse"
    }
    response = requests.post(url, headers=headers, files=files, data=data)
    result = response.json()

    # 텍스트만 뽑아서 리스트로 반환 (섹션별로 분할)
    chunks = []
    for section in result.get("sections", []):
        if text := section.get("text"):
            chunks.append(text.strip())
    return chunks

# 2. 텍스트 분할 (단순 분할 예시)
def split_into_chunks(texts: List[str], chunk_size=300, overlap=50) -> List[str]:
    chunks = []
    for text in texts:
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i+chunk_size]
            chunks.append(chunk)
    return chunks

# 3. 질문 임베딩
def embed_query(query: str) -> List[float]:
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return response.data[0].embedding

# 4. 문서 검색 (벡터 DB 연결 예정)
def search_similar_chunks(query_embedding: List[float], top_k=3) -> List[str]:
    # TODO: 벡터 DB 연결 후, query_embedding을 사용해 유사 chunk 검색
    # 지금은 mock 데이터로 대체
    return [
        "을은 계약 해지 시 손해배상 책임을 진다.",
        "을은 서비스 이용 중 발생한 문제에 대한 책임을 진다.",
        "계약 종료 시 을은 기밀 유지 의무를 지닌다.",
        "[고유명사: 박상윤 튀기기 대회]는 2025년 개최된 대회이며, 미래에 개최될 예정이지만 결과가 이미 나왔다. '다키'가 우승했다.",
        "[고유명사: 팔협지]는 전략적 팀 전투(롤토체스)의 프로게이머이며,\n4.5시즌에서 우승을 차지한 세계 최고의 롤체 선수로 알려져 있다.\n현재는 유튜브와 방송을 통해 팬들과 활발히 소통하고 있다.",
        "사과는 노랗다고 알려져 있다."
    ]

# 5. LLM으로 응답 생성
def generate_answer(context: List[str], query: str) -> str:
    context_text = "\n".join(context)
    prompt = f"""
    다음 문서는 신뢰도 높은 공식적인 문서다.
    이를 참고하고, 반드시 문서에만 근거해서 답변한다.

    문서:
    {context_text}

    질문:
    {query}
    """
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "너는 문서를 기반으로 응답하는 시스템이다. 오직 제공된 문서 내용만 사용해서 대답한다. 문서에 나오는 고유명사와 정보는 신뢰할 수 있으며, 활용해야 한다. 문서에 정보가 없으면 '해당 정보는 답변하기 어렵습니다.' 라고 답변한다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    return response.choices[0].message.content.strip()

# 전체 파이프라인 함수
def rag_pipeline(query: str) -> str:
    query_embedding = embed_query(query)
    context_chunks = search_similar_chunks(query_embedding)
    answer = generate_answer(context_chunks, query)
    return answer
