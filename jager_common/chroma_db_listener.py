import glob
import json
import os
import re
import shlex

import chromadb
import ollama
from chromadb.config import Settings
from flask import Flask, request, jsonify
from jager_common import gpu_client

persistDirectory = "C:\\Users\\AfikAtias\\PycharmProjects\\Jager-Project\\chromadb"
#persistDirectory = "/opt/chromadb"
#chromaClient = chromadb.Client(Settings(persist_directory=persistDirectory))
chromaClient = chromadb.PersistentClient(path=persistDirectory)
collection = chromaClient.get_or_create_collection("slack_collection")
db_app = Flask(__name__)
gpuClient = gpu_client.GPUClient()


@db_app.route('/addToDB', methods=['POST'])
def addToDB():
    messageData = request.get_json()
    timestamp = messageData['timestamp']
    user = messageData['user']
    text = messageData['text']
    channel = messageData['channel']
    print("in /addToDB")
    print(messageData)
    data_to_add = user + " @ " + channel + ": " + text
    # Need to be replaced with and http request to the GPU Cluster if possible
    embedded_data = ollama.embeddings(model="all-minilm", prompt=data_to_add)
    collection.add(
        ids=[str(timestamp)],
        embeddings=[embedded_data["embedding"]],
        documents=[data_to_add]
    )
    response = {'data': data_to_add}
    return jsonify(response)


@db_app.route('/queryDB', methods=['GET'])
def query_db():
    print("in /queryDB")
    messageData = request.args
    prompt = messageData['prompt']
    user = prompt.split(":")[0]
    prompt = prompt.replace(user, "")
    prompt = prompt.strip()
    eng_prompt = f"The user: {user} asked this question: {prompt}"
    # Need to be replaced with and http request to the GPU Cluster if possible
    embedded_prompt = ollama.embeddings(model="all-minilm", prompt=prompt)
    results = collection.query(
        query_embeddings=[embedded_prompt["embedding"]],
        n_results=3
    )

    documents = results.get('documents', [])
    data = ""
    for i, doc_list in enumerate(documents):
        for j, doc in enumerate(doc_list):
            #print(j + 1, doc)
            #doc = doc.replace('#', "") #to remove unwanted #
            data = data + doc
    print(f"the question asked: {prompt} by the user {user} ")
    print("the data we use is ", data)
    output = gpuClient.ask(data, eng_prompt)
    if output is None:
        return jsonify("Sorry, I had an internal error. please try again later.")
    return jsonify(output)


def get_latest_md_filename():
    list_of_files = glob.glob(
        'C:\\Users\\AfikAtias\\PycharmProjects\\Jager-Project\\slack_implementation\\backend\\slack_messages_*.md')
    latest_file = max(list_of_files, key=os.path.getctime)
    #print(latest_file)
    return latest_file


@db_app.route('/loadDB', methods=['GET'])
def load_md_file_to_db():
    print("in /loadDB")
    filename = get_latest_md_filename()
    print("The file that will load to the database is ", filename)
    with open(filename, 'r', encoding='utf-8') as file:
        md_content = file.read()
        chunks = md_content.split('## ')
        #chunks = [line.strip() for line in chunks]
        annoying_message = re.compile(r'afikat \(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\)\nhi')
        entry_id = 0
        for i, chunk in enumerate(chunks):
            #Skipping the quetstions and the bot responses
            if "jageragent" in chunk or "jageragentv2" in chunk or "This message was deleted" in chunk or annoying_message.search(chunk):
                continue
            if i > 0:
                prev_line = chunks[i-1]
                prev_line = prev_line.replace('#', "")
            else:
                prev_line = ""
            if i < len(chunks)-1:
                next_line = chunks[i+1]
                next_line = next_line.replace('#', "")
            else:
                next_line = ""
            chunk = chunk.replace('#', "")
            total_entry = prev_line + chunk + next_line
            if entry_id == 4:
                print("prev line: ", prev_line)
                print("current line: ", chunk)
                print("next line: ", next_line)
                print("total enty: ", total_entry)
                print("------------------------------------------------")
            embedded_data = ollama.embeddings(model="all-minilm", prompt=total_entry)
            collection.add(
                ids=[str(entry_id)],
                embeddings=[embedded_data["embedding"]],
                documents=[total_entry]
            )
            entry_id += 1

    print("loaded " + str(entry_id) + " elements, collection size is: " + str(collection.count()))
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


if __name__ == '__main__':
    db_app.run(host='0.0.0.0', port=4090, debug=True)
    #db_app.run(host='0.0.0.0', port=4090, debug=True, ssl_context=('fullchain.pem', 'privkey.pem'))
