import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


from shahhosseini.IdeaEvaluation.scripts.utils import DEEPSEEK_V3
from utils import *

resp = call_llm(
    user_message="i am fatemeh and i am 24. return a json oject of my information",
    model_name=DEEPSEEK_V3,
    url=AVA
    ,
    api_key="dummy",
    temp=0.0,
    jsonify=True
)
print(resp)

# response = call_llm2(
#     "hello",
#     "You are a helpfull assitante",
#     jsonify=False,
#     temp=0.0,
#     base_url=SERVER_URL,
#     api_key="dummy",
#     model_name=QWEN4B,
#     max_retries=5,
# )

# print(response.text)

# from openai import OpenAI

# client = OpenAI(
#     api_key="dummy",
#     base_url="http://localhost:8001/v1",
# )

# resp = client.completions.create(
#     model="Qwen/Qwen3-4B",
#     prompt="Say hello in one short sentence.",
#     max_tokens=32,
#     temperature=0.0,
# )

# print(resp)