import json
import re
import time

import requests

URL = "https://hamrah-e-ham-bot.liara.run/api/proxy/chat"
API_KEY = "HamraheHam-XweA84Yhsj08sSSaj;ovu87yhtnSoi7SU"  

AVAL_AI_KEY = "aa-HG1Q8R0pc3ESiSJTkjBOzpSmav9HM6uyDovm5EAMjyPXK8GO"
AVAL_AI_KEY_ROHBAN = "aa-6I3P1SpUUyeYzMnCKooe3EhF0LJPFu8XHC2h0oGU6LOfTfJ6"

AVAL_AI_URL = "https://api.avalai.ir/v1/chat/completions"
GEMINI = "gemini-2.5-flash-lite"
DEEPSEEK_V3 = "deepseek-v3.2"

QWEN4B = "Qwen/Qwen3-4B"
SERVER_URL =  "http://localhost:8001/v1"

def parse_json_from_string(json_string):
    clean_json_string = json_string.replace('```json\n', '').replace('\n```', '').replace('\n', '').strip()
    clean_json_string = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', clean_json_string)
    json_object = json.loads(clean_json_string)
    return json_object

def persona_to_natural_language(record):
    bk = record["background_knowledge"]

    return f"""
You are acting as {record['persona']}.

Background:
{record['background']}

Expertise profile:
- Literature familiarity: {bk['literature_familiarity']}/10
- Methodology depth: {bk['methodology_depth']}/10
- Application experience: {bk['application_experience']}/10
- Frontier sensitivity: {bk['frontier_sensitivity']}/10

Primary objective:
{record['goal']}

Potential bias or limitation:
{'; '.join(record['constraints'])}
""".strip()

import time
import requests

def _resolve_chat_url(url_or_base):
    url = url_or_base.rstrip("/")
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return f"{url}/chat/completions"
    return f"{url}/v1/chat/completions"


def _build_headers(api_key=None, url=None):
    headers = {"Content-Type": "application/json"}

    if not api_key:
        return headers

    if api_key.startswith("Bearer "):
        token = api_key
    else:
        token = f"Bearer {api_key}"

    # AvalAI and OpenAI-compatible servers both work with Authorization
    headers["Authorization"] = token
    return headers

def _strip_think_blocks(text):
    if not isinstance(text, str):
        return text
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()


def _strip_code_fences(text):
    if not isinstance(text, str):
        return text
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", stripped)
        stripped = re.sub(r"\n```$", "", stripped)
    return stripped.strip()


def _normalize_json_response_text(text):
    return _strip_code_fences(_strip_think_blocks(text))


def _supports_structured_output(url, model_name):
    endpoint = _resolve_chat_url(url)
    model = str(model_name or "")
    return (
        "localhost" in endpoint
        or "127.0.0.1" in endpoint
        or model.startswith("Qwen/")
        or model.casefold().startswith("qwen")
    )


def _parse_json_candidate(text):
    parsed = json.loads(text)
    if isinstance(parsed, str):
        parsed = json.loads(parsed)
    if isinstance(parsed, list):
        if len(parsed) == 1 and isinstance(parsed[0], dict):
            return parsed[0]
        raise ValueError("Expected a JSON object, got a JSON array")
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object")
    return parsed


def _extract_first_json_object(text):
    if not isinstance(text, str):
        return text

    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")

    in_string = False
    escape = False
    depth = 0

    for i, ch in enumerate(text[start:], start=start):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])

    raise ValueError("No balanced JSON object found in response")

def call_llm(
    user_message,
    system_message=None,
    jsonify=False,
    temp=0.7,
    url="http://localhost:8001/v1",
    max_retries=5,
    model_name="Qwen/Qwen3-4B",
    api_key="dummy",
    max_tokens=None,
    timeout=180,
    seed=None,
):
    endpoint = _resolve_chat_url(url)
    headers = _build_headers(api_key=api_key, url=endpoint)

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": user_message})

    data = {
        "model": model_name,
        "messages": messages,
        "temperature": temp,
    }

    if max_tokens is not None:
        data["max_tokens"] = max_tokens
    if seed is not None:
        data["seed"] = seed
    if jsonify and _supports_structured_output(url, model_name):
        data["response_format"] = {"type": "json_object"}

    for attempt in range(max_retries):
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=data,
                timeout=timeout,
            )

            if response.status_code != 200:
                print(f"Bad status: {response.status_code}")
                print(response.text[:2000])
                time.sleep(2 * (attempt + 1))
                continue

            response_json = response.json()
            res = response_json.get("choices", [{}])[0].get("message", {}).get("content")

            if res is None:
                print("Missing content, retrying...")
                time.sleep(2 * (attempt + 1))
                continue

            if jsonify:
                cleaned = _normalize_json_response_text(res)
                try:
                    return _parse_json_candidate(cleaned)
                except Exception as exc:
                    try:
                        return _extract_first_json_object(cleaned)
                    except Exception:
                        try:
                            return parse_json_from_string(cleaned)
                        except Exception:
                            print(f"Invalid JSON response, retrying... ({exc})")
                            print(cleaned[:1000])
                            time.sleep(2 * (attempt + 1))
                            continue

            return _normalize_json_response_text(res)

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}, retrying...")
            time.sleep(2 * (attempt + 1))

    raise Exception("Max retries exceeded")


def write_jsonl(path, records, mode="w"):
    with open(path, mode, encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def read_jsonl(path):
    pred_data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            pred_data.append(json.loads(line))
    return pred_data

def read_txt(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def find_jsonl_format_errors(file_path, show_valid_count=True):

    error_found = False
    valid_count = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_number, line in enumerate(f, start=1):
            stripped_line = line.strip()

            # Skip empty lines
            if not stripped_line:
                continue

            try:
                json.loads(stripped_line)
                valid_count += 1
            except json.JSONDecodeError as e:
                error_found = True
                print("\n❌ JSON formatting error detected")
                print(f"   Line number : {line_number}")
                print(f"   Error       : {e.msg}")
                print(f"   Column      : {e.colno}")
                print(f"   Position    : {e.pos}")
                print(f"   Line snippet: {stripped_line[e.pos-10:e.pos+20]}")
                print("-" * 60)

    if not error_found:
        print("✅ No formatting errors found.")
        if show_valid_count:
            print(f"Total valid JSON objects: {valid_count}")
