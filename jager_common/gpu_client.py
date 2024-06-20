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
        self.retry_interval = 5
        self.target_line_for_generate = 'the Bot answer is:'

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

    def ask(self, prompt):
        if self.connect() == 1:
            submit_job_command = f"sbatch --export=ALL,my_arg='{prompt}' sbatch_gpu_simple_question"
            print(submit_job_command)
            (stdin, stdout, stderr) = self.client.exec_command(submit_job_command)
            submitted_job = stdout.read().decode('utf-8').strip()
            print('log printing: ', submitted_job)
            job_id = ''.join([char for char in submitted_job if char.isdigit()])
            print(job_id)
            self.wait_for_job_to_end(job_id)
            #DEBUG PRINTS
            #print('cat command: ', 'cat job-' + job_id + '.out')
            (stdin, stdout, stderr) = self.client.exec_command('cat job-' + job_id + '.out')
            job_output = stdout.read().decode('utf-8').strip()
            #print('log printing: ', job_output)
            bot_answer = self.extract_answer(job_output)
            print('bot answer: ', bot_answer)
            self.disconnect()
            return bot_answer

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
                break
            if self.check_if_job_completed(job_id):
                print(f"Job {job_id} is still running...")
                time.sleep(interval)
            else:
                print(f"Job {job_id} has completed.")
                break


#if __name__ == '__main__':
    '''
    print('Establishing connection to GPU Cluster')
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        private_key_path = 'C:\\Users\\AfikAtias\\Desktop\\afikat-hpc.key'
        private_key = paramiko.RSAKey(filename=private_key_path)
        client.connect('gpu.mta.ac.il', port=22, username='afikat', pkey=private_key, timeout=5)
        print('Connected successfully')
        prompt = "can you explain shortly why the sky are blue?"
        submit_job_command = f"sbatch --export=ALL,my_arg='{prompt}' sbatch_gpu_simple_question"
        print(submit_job_command)
        (stdin, stdout, stderr) = client.exec_command(submit_job_command)
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
    '''
