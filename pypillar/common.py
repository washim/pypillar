import subprocess
import json
import os


class Worker:
    def __init__(self, tasks, original_input, request_id, task_input={}):
        self.tasks = tasks
        self.original_input = original_input
        self.request_id = request_id
        self.task_input = task_input
        self.output = None
        self.error = {}
        self.sys_error = False

    def run(self):
        for rule in self.tasks:
            try:
                command = ['python', rule['script'], json.dumps(rule), self.original_input, self.request_id, self.task_input]
                runtime_log = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
                with open(rule['runtime_log'], "w+") as outfile:
                    outfile.write(runtime_log)

                if runtime_log.find('PYPILLAR_TASK_INPUT') != -1:
                    self.task_input = runtime_log.strip()
                elif runtime_log.find('PYPILLAR_RESULT') != -1:
                    self.output = runtime_log.strip()
                    break
                else:
                    self.output = '{"PYPILLAR_RESULT":{}}'

            except subprocess.CalledProcessError as exc:
                with open(rule['runtime_log'], "w+") as outfile:
                    outfile.write(exc.output)

                self.error['message'] = f'Task({rule["name"]}): Failed. Check task log for more info.'
                self.sys_error = True
                break

        if self.sys_error:
            self.sys_error = False
            return self.error
        else:
            return self.output

class Tasks:
    def __init__(self, path):
        self.path = path
        self.all_data = []

    def GetAllTasks(self, project_id=None):
        if os.path.exists(self.path) == False:
            with open(self.path, 'w+') as outfile:
                outfile.write('[]')

        with open(self.path) as outfile:
            all_data = json.load(outfile)

        if project_id:
            all_data = list(filter(lambda item: item['pid'] == project_id, all_data))

        self.all_data = sorted(all_data, key=lambda i: i['weight'])

    def AddTask(self, record):
        self.GetAllTasks()
        self.all_data.append(record)
        with open(self.path, 'w+') as outfile:
            json.dump(self.all_data, outfile)


class Pojects:
    def __init__(self, path):
        self.path = path
        self.all_data = []

    def GetAllProjects(self):
        if os.path.exists(self.path) == False:
            with open(self.path, 'w+') as outfile:
                outfile.write('[]')

        with open(self.path) as outfile:
            self.all_data = json.load(outfile)

    def AddProject(self, record):
        self.GetAllProjects()
        self.all_data.append(record)
        with open(self.path, 'w+') as outfile:
            json.dump(self.all_data, outfile)