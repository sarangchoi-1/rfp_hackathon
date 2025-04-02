import os
import json
import requests
from typing import List
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
from data.Retrieve import double_retrieve

env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(dotenv_path=env_path)

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

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

def rag_pipeline(query: str) -> str:
    documents = double_retrieve(query) 
    context = [doc.page_content for doc in documents]
    answer = generate_answer(context, query)
    return answer