from flask import Flask, jsonify
from jager_common import gpu_client
app = Flask(__name__)
@app.route('/', methods=['GET'])
def print_hello():
    print("hello world")
    data = {'message': 'Hello, world!'}
    return jsonify(data)

if __name__ == '__main__':
    client = gpu_client.GPUClient()
    client.ask("can you explain shortly why the sky are blue?")
    #app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=('cert.crt', 'key.key'))
    #app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=('fullchain.pem', 'privkey.pem'))
