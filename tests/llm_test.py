import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from utils import AVAL_AI_KEY, AVAL_AI_URL, DEEPSEEK_V3, call_llm


response = call_llm(
    "hello",
    "You are a helpfull assitante",
    jsonify=False,
    temp=0.0,
    url=AVAL_AI_URL,
    api_key=AVAL_AI_KEY,
    model_name=DEEPSEEK_V3,
    max_retries=1,
)

print(response)
