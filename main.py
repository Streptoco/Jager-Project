import subprocess
import time

from flask import Flask, jsonify
import paramiko

app = Flask(__name__)


@app.route('/', methods=['GET'])
def print_hello():
    print("hello world")
    data = {'message': 'Hello, world!'}
    return jsonify(data)


def check_if_job_complited(job_id, client):
    print('Checking Job number:' , job_id)
    (stdin, stdout, stderr) = client.exec_command('squeue --me')
    output = stdout.read().decode('utf-8').strip()
    for line in output.splitlines():
        if str(job_id) in line:
            return True
    return False


def wait_for_job_to_end(job_id, client, interval=1):
    i = 0
    while True:
        i += 1
        if i > 200:
            print("Job did not complete within 200 seconds")
            break
        if check_if_job_complited(job_id, client):
            print(f"Job {job_id} is still running...")
            time.sleep(interval)
        else:
            print(f"Job {job_id} has completed.")
            break


if __name__ == '__main__':
    print('Establishing connection to GPU Cluster')
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        private_key_path = 'C:\\Users\\AfikAtias\\Desktop\\afikat-hpc.key'
        private_key = paramiko.RSAKey(filename=private_key_path)
        client.connect('gpu.mta.ac.il', port=22, username='afikat', pkey=private_key, timeout=5)
        print('Connected successfully')
        (stdin, stdout, stderr) = client.exec_command(
            'sbatch --export=ALL,my_arg=\'can you explain shortly why the sky are blue?\' sbatch_gpu_simple_question')
        submitted_job = stdout.read().decode('utf-8').strip()
        print('log printing: ', submitted_job)
        job_id = ''.join([char for char in submitted_job if char.isdigit()])
        print(job_id)
        wait_for_job_to_end(job_id, client)
        #DEBUG PRINTS
        #print('cat command: ', 'cat job-' + job_id + '.out')
        (stdin, stdout, stderr) = client.exec_command('cat job-' + job_id + '.out')
        job_output = stdout.read().decode('utf-8').strip()
        #print('log printing: ', job_output)
        bot_answer = job_output.strip().splitlines()[-1]
        print('bot answer: ', bot_answer)
        client.close()
    except TimeoutError as e:
        print(e)
    #app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=('cert.crt', 'key.key'))
    #app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=('fullchain.pem', 'privkey.pem'))
