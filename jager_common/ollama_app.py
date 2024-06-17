from flask import Flask, request, jsonify
import requests
import json
import ollama

ollama_app = Flask(__name__)
generateUrl = 'http://localhost:11434/api/generate'
@ollama_app.route('/ask', methods=['GET'])
def ask_llama_question():
    messageData = request.args
    prompt = messageData['prompt']
    body = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }
    ai_response = requests.post(generateUrl, json=body)
    response_data = json.loads(ai_response.text)
    answer = response_data["response"]
    print(answer)
    response = {'answer': answer, 'prompt': prompt}
    return response

if __name__ == '__main__':
    ollama_app.run(host='0.0.0.0', port=4000, debug=True)

