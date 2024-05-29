from flask import Flask, jsonify

app = Flask(__name__)
@app.route('/', methods=['GET'])
def print_hello():
    print("hello world")
    data = {'message': 'Hello, world!'}
    return jsonify(data)
app.run(host='0.0.0.0', port=5000, debug=True)