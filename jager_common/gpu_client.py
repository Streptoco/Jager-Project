import datetime
import time

import paramiko


class GPUClient:
    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.private_key_path = 'C:\\Users\\AfikAtias\\Desktop\\afikat-hpc.key'
        self.private_key = paramiko.RSAKey(filename=self.private_key_path)
        self.hostname = 'gpu.mta.ac.il'
        self.port = 22
        self.max_retries = 5
        self.retry_interval = 8
        self.now = datetime.datetime.now()
        self.target_line_for_generate = 'the Bot answer is:'
        #self.prompt_engineer = "You are a slack assistant named Jager. your purpose is to help us search the history of our conversations but you dont mention this."
        self.prompt_engineer = (
            f"You are Jager-Agent-V3 an AI assistant developed by the Jager team to help users with various tasks. "
            f"You do not need to introduce yourself."
            f" Your responses should be concise and informative tailored to the user's questions. "
            f"Use the provided context which includes user messages with timestamps to formulate your answers. "
            f"If the question is unrelated to the context rely on your general knowledge"
            f"or indicate if you don't know the answer. "
            f"Always be friendly and helpful and feel free to ask for more information if needed. "
            f"Today's date and time is {self.now}."
        )

    def establish_connection(self):
        print('Establishing connection to GPU Cluster')
        self.client.connect(self.hostname, port=self.port, username='afikat', pkey=self.private_key, timeout=5)
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
            data = data.replace(",", "")
            submit_job_command = f"sbatch --export=ALL,prompt_engineer=\"{self.prompt_engineer}\",data_base=\"base you answer on this data {data}\",prompt=\" answer this question: {prompt}\" sbatch_gpu_simple_question"
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

