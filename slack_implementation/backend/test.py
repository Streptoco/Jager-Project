import ollama
import chromadb

documents = [
    "Afik Atias: \"ok, so we decided that we will meet on wednesday and continue to work on the science project\"",
    "Yuval Levy: \"great, i will bring my computer\"",
    "Roni Kuz: \"i will be there first thing in the morning to ensure we get the room in Pomento library\"",
    "Yuvel Levy: \"I believe that where will be traffic in the morning so i will probably be late\"",
    "Roni Kuz: \"afik where are you? we are wating for 30 minutes and you dont answer\"",
    "Yuval Levy: \"we will start working without you\"",
    "Afik Atias: \"Im sorry guys i dont feel good, i think i cant come",
    "Yuval Levy: \"you always do it! we cant trust you, we decided to eliminate you from the project!\"",
    "Rony Kuz: \"yes and i dont love you anymore\"",
    "Afik Atias: \"im sorry guys..\"",
]

client = chromadb.Client()
collection = client.create_collection(name="docs")

# store each document in a vector embedding database
for i, d in enumerate(documents):
    response = ollama.embeddings(model="all-minilm", prompt=d)
    embedding = response["embedding"]
    collection.add(
        ids=[str(i)],
        embeddings=[embedding],
        documents=[d]
    )

    # an example prompt
prompt = "sis someone angry on someone else in the converion?"

# generate an embedding for the prompt and retrieve the most relevant doc
response = ollama.embeddings(
    prompt=prompt,
    model="all-minilm"
)
results = collection.query(
    query_embeddings=[response["embedding"]],
    n_results=1
)
data = results['documents'][0][0]

# generate a response combining the prompt and data we retrieved in step 2
output = ollama.generate(
    model="llama3",
    prompt=f"Using this data: {data}. Respond to this prompt: {prompt}"
)

print(output['response'])