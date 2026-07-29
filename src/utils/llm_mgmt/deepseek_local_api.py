import requests
import json

OLLAMA_API = "http://localhost:11435/api/chat"


def chat_with_deepseek(message, history=None):
    if history is None:
        history = []

    # print(message)
    messages = history + [{"role": "user", "content": message}]

    data = {
        "model": "deepseek-r1:8b",
        "messages": messages,
        "stream": True
    }

    try:
        # Disable proxies (curl often ignores system proxies that requests uses)
        # Add generous timeout: 10s to connect, 300s to read (generation can be slow)
        response = requests.post(
            OLLAMA_API,
            json=data,
            stream=True,
            proxies={"http": None, "https": None},  # Bypass env proxies
            timeout=(10, 300)
        )

        # If we get a 4xx/5xx, show the actual response body before raising
        if not response.ok:
            print(f"HTTP Error {response.status_code}: {response.text[:500]}")
            response.raise_for_status()

        full_answer = ""

        # decode_unicode=True ensures we get strings, not bytes
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue

            try:
                json_data = json.loads(line)
            except json.JSONDecodeError as je:
                print(f"\n[JSON Decode Error] Line content: {repr(line[:200])}")
                raise

            # Ollama streaming format: {"message": {"content": "..."}, "done": false}
            if json_data.get("done"):
                break

            chunk = json_data.get("message", {}).get("content", "")
            full_answer += chunk

        return full_answer

    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
        print("Hint: Is Ollama running? Check with: curl http://localhost:11434/api/tags")
    except requests.exceptions.Timeout as e:
        print(f"Timeout Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {type(e).__name__}: {e}")

    return ""


if __name__ == "__main__":
    print("✅ DeepSeek-R1-8B Robot（M2 16GB）")
    print("Input 'quit' to Exit\n")

    chat_history = []

    while True:
        user_input = input("You：")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("👋 Exit Program")
            break

        answer = chat_with_deepseek(user_input, chat_history)
        if answer:
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": answer})
            print(f'Bot: {answer}')