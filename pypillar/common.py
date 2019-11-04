import subprocess
import json
import sys


class Worker:
    def __init__(self, tasks, post_data, request_id):
        self.tasks = tasks
        self.post_data = post_data
        self.request_id = request_id
        self.task_input = {}
        self.output = None
        self.error = {}
        self.data = {}
        self.sys_error = False

    def run(self):
        for rule in self.tasks:
            try:
                self.data['PYPILLAR_TASK_INFO'] = rule
                self.data['PYPILLAR_POST_DATA_FILE'] = self.post_data
                self.data['PYPILLAR_UNIQUE_REQUEST_ID'] = self.request_id
                self.data['PYPILLAR_TASK_INPUT'] = self.task_input

                command = [sys.executable, rule['script'], '--PYPILLAR', json.dumps(self.data)]
                runtime_log = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)

                with open(rule['task_log_path'], "w+") as outfile:
                    outfile.write(runtime_log)

                try:
                    runtime_log = json.loads(runtime_log)
                    if runtime_log.get('PYPILLAR_TASK_INPUT'):
                        self.task_input = runtime_log['PYPILLAR_TASK_INPUT']
                    if runtime_log.get('PYPILLAR_RESULT'):
                        self.output = runtime_log
                        break
                except Exception:
                    pass

            except subprocess.CalledProcessError as exc:
                with open(rule['task_log_path'], "w+") as outfile:
                    outfile.write(exc.output)

                self.error['error'] = f'Task({rule["name"]}): Failed. Check task log for more info.'
                self.sys_error = True
                break

        if self.sys_error:
            self.sys_error = False
            return json.dumps(self.error)

        elif self.output:
            return json.dumps(self.output)

        else:
            return json.dumps({"PYPILLAR_RESULT": {}})