import ollama

def chat(model: str, system_prompt: str, user_message: str, history: list):
    messages = [{"role": "system", "content": system_prompt}]

    for m in history[-6:]:
        messages.append({
            "role": m.get("role", "user"),
            "content": m.get("content", "")
        })

    messages.append({"role": "user", "content": user_message})

    response = ollama.chat(
        model=model,
        messages=messages
    )

    return response["message"]["content"]
