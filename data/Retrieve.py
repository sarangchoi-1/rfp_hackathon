import sys
import os
from pathlib import Path

# Load environment variables from config/.env
config_dir = Path(__file__).parent.parent / "config"
env_path = config_dir / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")
else:
    print(f"Warning: .env file not found at {env_path}")

print(f"Python path: {sys.path}")
print(f"Python version: {sys.version}")

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY environment variable is not set")
    print("Please set your OpenAI API key using one of these methods:")
    print("1. Set environment variable: export OPENAI_API_KEY='your-api-key'")
    print("2. Create a .env file in the config directory with: OPENAI_API_KEY=your-api-key")
    raise ValueError("OPENAI_API_KEY environment variable is not set")

try:
    print("Attempting to import langchain_community...")
    import langchain_community
    print(f"langchain_community version: {langchain_community.__version__}")
    from langchain_community.vectorstores import FAISS
    print("Successfully imported langchain_community")
    
    print("Attempting to import langchain_openai...")
    import langchain_openai
    print("Successfully imported langchain_openai")
    from langchain_openai import OpenAIEmbeddings
    print("Successfully imported OpenAIEmbeddings")
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"Installed packages:")
    os.system("pip list")
    raise

# Get the absolute path to the data directory
DATA_DIR = Path(__file__).parent
print(f"Data directory: {DATA_DIR}")

try:
    print("Initializing OpenAI embeddings...")
    embeddings = OpenAIEmbeddings()
    print("Successfully initialized embeddings")
    
    print("Loading case database...")
    case_db_path = str(DATA_DIR / "vector_db_case")
    print(f"Case DB path: {case_db_path}")
    loaded_case_db = FAISS.load_local(
        folder_path=case_db_path,
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
        index_name="case_vector"
    )
    print("Successfully loaded case database")

    print("Loading criteria database...")
    criteria_db_path = str(DATA_DIR / "vector_db_criteria")
    print(f"Criteria DB path: {criteria_db_path}")
    loaded_criteria_db = FAISS.load_local(
        folder_path=criteria_db_path,
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
        index_name="criteria_vector"
    )
    print("Successfully loaded criteria database")

    _case_retriever = loaded_case_db.as_retriever(k=3)
    _criteria_retriever = loaded_criteria_db.as_retriever(k=10)
    print("Successfully initialized retrievers")
except Exception as e:
    print(f"Error initializing vector stores: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Data directory path: {DATA_DIR}")
    print(f"Directory contents: {os.listdir(DATA_DIR)}")
    raise

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
