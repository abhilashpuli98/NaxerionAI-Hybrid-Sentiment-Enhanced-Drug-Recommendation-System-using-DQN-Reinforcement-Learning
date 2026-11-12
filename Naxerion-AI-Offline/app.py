import ollama
import gradio as gr

SYSTEM_PROMPT = "You are a helpful offline Naxerion AI assistant."

def chat(user_message, history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    for user, assistant in history:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": assistant})

    messages.append({"role": "user", "content": user_message})

    response = ollama.chat(
        model="llama3.2:1b",
        messages=messages
    )

    assistant_message = response["message"]["content"]

    history.append((user_message, assistant_message))
    return history

with gr.Blocks(title="Offline Naxerion LLM") as demo:
    gr.Markdown("##  Offline Naxerion AI")

    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="Type your message and press Enter")

    msg.submit(chat, [msg, chatbot], chatbot)

demo.launch()
#uvicorn main:app --host 0.0.0.0 --port 8000 --reload
