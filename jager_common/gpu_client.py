import datetime
import time

import paramiko


class GPUClient:
    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.private_key_path = '/Users/yuvall/Desktop/FinishProject/afikat-hpc.key'
        self.private_key = paramiko.RSAKey(filename=self.private_key_path)
        self.hostname = 'gpu.mta.ac.il'
        self.port = 22
        self.max_retries = 5
        self.retry_interval = 8
        self.now = datetime.datetime.now()
        self.target_line_for_generate = 'the Bot answer is:'
        #self.prompt_engineer = "You are a slack assistant named Jager. your purpose is to help us search the history of our conversations but you dont mention this."
        self.prompt_engineer = (f"You are an AI assistant created to help users with a wide variety of tasks. Your "
                                f"name is Jager-Agent-V2 and you were developed by Jager team. The user will provide "
                                f"you with a context which is ten messages taken from the history of the conversation "
                                f"that can be related to the question asked."
                                f". you are given the message content "
                                f"the timestamp and the user that sent it. Based on this context please provide a "
                                f"concise and informative response to the user's question. Your response should be "
                                f"tailored to the user's question and the given context. Use the information in the "
                                f"context to formulate your answer while also drawing from your general knowledge to "
                                f"provide a comprehensive response and let the user know if you need more "
                                f"information to answer the question asked. Remember to be friendly helpful "
                                f"and to-the-point in your response. In your response you don't need to mention the "
                                f"context. the date and time today is {self.now}"
                                f" if your answer relates to the date, please dont forget it.")

    def establish_connection(self):
        print('Establishing connection to GPU Cluster')
        self.client.connect(self.hostname, port=self.port, username='afikat', pkey=self.private_key, timeout=60)
        print('Connected successfully')

    def connect(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.establish_connection()
                return 1
            except TimeoutError as e:
                print("Conntection Failed.. retry")
                time.sleep(self.retry_interval)
                retries += 1
        print(f"Failed to establish SSH connection after {self.max_retries} attempts.")
        return None

    def disconnect(self):
        print('Disconnecting from GPU Cluster')
        self.client.close()

    def ask(self, data, prompt):
        if self.connect() == 1:
            data = data.replace(",", "\'\\, ")
            # submit_job_command = f"sbatch --export=ALL,prompt_engineer=\'{self.prompt_engineer}\",data_base=\"this is the context given to you {data}\",prompt=\" the question that you were asked is {prompt}\" sbatch_gpu_simple_question"
            submit_job_command = f"sbatch --export=ALL,prompt_engineer='{self.prompt_engineer}',data_base='use this data to answer the question you will be asked if it helps you {data}',prompt='the question is {prompt}' sbatch_gpu_simple_question"
            print(submit_job_command)
            (stdin, stdout, stderr) = self.client.exec_command(submit_job_command)
            submitted_job = stdout.read().decode('utf-8').strip()
            time.sleep(2)
            print('log printing: ', submitted_job)
            if 'Submitted batch job' not in submitted_job:
                print('Failed to submit batch job')
                return None

            job_id = ''.join([char for char in submitted_job if char.isdigit()])
            print(job_id)
            job_status = self.wait_for_job_to_end(job_id)
            if job_status == 0:
                return None
            #DEBUG PRINTS
            #print('cat command: ', 'cat job-' + job_id + '.out')
            (stdin, stdout, stderr) = self.client.exec_command('cat job-' + job_id + '.out')
            job_output = stdout.read().decode('utf-8').strip()
            #print('log printing: ', job_output)
            bot_answer = self.extract_answer(job_output)
            print('bot answer: ', bot_answer)
            self.disconnect()
            return bot_answer
        else:
            return None

    def extract_answer(self, job_output):
        lines = job_output.splitlines()
        try:
            index = next((i for i, line in enumerate(lines) if self.target_line_for_generate in line), None)
            extracted_lines = lines[index + 1:]
            answer = '\n' .join(extracted_lines)
            return answer
        except ValueError:
            return job_output.strip().splitlines()[-1]

    def check_if_job_completed(self, job_id):
        print('Checking Job number:', job_id)
        (stdin, stdout, stderr) = self.client.exec_command('squeue --me')
        output = stdout.read().decode('utf-8').strip()
        for line in output.splitlines():
            if str(job_id) in line:
                return True
        return False

    def wait_for_job_to_end(self, job_id, interval=1):
        i = 0
        while True:
            i += 1
            if i > 200:
                print("Job did not complete within 200 seconds")
                return 0
            if self.check_if_job_completed(job_id):
                print(f"Job {job_id} is still running...")
                time.sleep(interval)
            else:
                print(f"Job {job_id} has completed.")
                return 1

