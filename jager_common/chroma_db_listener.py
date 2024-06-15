import chromadb
import ollama
from chromadb.config import Settings
from flask import Flask, request, jsonify

#persistDirectory = "C:\\Users\\AfikAtias\\PycharmProjects\\Jager-Project\\chromadb"
persistDirectory = "/opt/chromadb"
#chromaClient = chromadb.Client(Settings(persist_directory=persistDirectory))
chromaClient = chromadb.PersistentClient(path=persistDirectory)
collection = chromaClient.get_or_create_collection("slack_collection")
db_app = Flask(__name__)

@db_app.route('/addToDB', methods=['POST'])
def addToDB():
    messageData = request.get_json()
    timestamp = messageData['timestamp']
    user = messageData['user']
    text = messageData['text']
    channel = messageData['channel']
    print(messageData)
    data_to_add = user + " @ " + channel + ": " + text
    # Need to be replaced with and http request to the GPU Cluster if possible
    embedded_data = ollama.embeddings(model="all-minilm", prompt=data_to_add)
    collection.add(
        ids=[str(timestamp)],
        embeddings=[embedded_data["embedding"]],
        documents=[data_to_add]
    )
    print(collection)
    response = {'data': data_to_add}
    return jsonify(response)

@db_app.route('/queryDB', methods=['GET'])
def query_db():
    messageData = request.args
    prompt = messageData['prompt']
    # Need to be replaced with and http request to the GPU Cluster if possible
    embedded_prompt = ollama.embeddings(model="all-minilm", prompt=prompt)
    results = collection.query(
        query_embeddings=[embedded_prompt["embedding"]],
        n_results=1
    )
    data = results['documents'][0][0]
    # Need to be replaced with and http request to the GPU Cluster if possible
    output = ollama.generate(
        model="llama3",
        prompt=f"You are a slack assistant named Jager, your purpose is to help us search the history of our "
               f"conversations. Using this data: {data}. Respond to this prompt: {prompt}"
    )
    return jsonify(output['response'])

if __name__ == '__main__':
    db_app.run(host='0.0.0.0', port=4090, debug=True)
    #db_app.run(host='0.0.0.0', port=4090, debug=True, ssl_context=('fullchain.pem', 'privkey.pem'))


