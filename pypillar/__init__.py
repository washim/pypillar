import os
import json
import click
from flask import (
    Flask, render_template, request, flash, redirect, url_for, jsonify
)
from flask.cli import FlaskGroup
from uuid import uuid1
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, validators
from pypillar.common import Worker, Tasks, Pojects

__version__ = '0.0.1-dev0'

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.urandom(12),
        WTF_CSRF_CHECK_DEFAULT=False,
        VERSION=__version__
    )
    app.TASK_LOGS_PATH = os.path.join(app.instance_path, 'runtime')

    if os.path.isdir(app.instance_path) == False:
        os.mkdir(app.instance_path)

    if os.path.isdir(app.TASK_LOGS_PATH) == False:
        os.mkdir(app.TASK_LOGS_PATH)

    @app.route('/')
    def home():
        return redirect(url_for('projects'))

    @app.route('/runtime_log/<string:tid>', methods=['GET', 'POST'])
    def runtime_log(tid):
        alltasks = Tasks(os.path.join(app.instance_path, 'tasks.json'))
        alltasks.GetAllTasks()
        task = list(filter(lambda item: item['id'] == tid, alltasks.all_data))
        try:
            with open(task[0]['runtime_log']) as outfile:
                log_content = outfile.read()
        except:
            log_content = 'No logs found yet.'

        if not len(log_content):
            log_content = 'No logs found yet.'

        try:
            log_content = json.dumps(json.loads(log_content), indent=4)
        except:
            pass

        return render_template('runtime_log.html', data=log_content)

    @app.route('/run', methods=['GET', 'POST'])
    def run():
        class RunForm(FlaskForm):
            input = TextAreaField('Api Post Data', render_kw={'rows': 10})

        form = RunForm()
        return render_template('run.html', form=form, form_title='Provide input data to run this project tasks', btn_name='Run Now')

    @app.route('/api', methods=['GET', 'POST'])
    def run_api():
        project_id = request.args.get('projectid')
        request_id = uuid1().hex
        if request.method == 'POST' and project_id:
            if len(request.form) > 0:
                original_input = {'PYPILLAR_ORIGINAL_INPUT': json.dump(request.form)}
            else:
                original_input = {'PYPILLAR_ORIGINAL_INPUT': []}

            alltasks = Tasks(os.path.join(app.instance_path, 'tasks.json'))
            alltasks.GetAllTasks(project_id)
            runner = Worker(alltasks.all_data, original_input, request_id)
            response = runner.run()
            return response
        else:
            return jsonify([{'error': 'Bad request', 'message': 'requestid and projectid required.', 'status': 400}])

    @app.route('/projects', methods=['GET', 'POST'])
    def projects():
        allprojects = Pojects(os.path.join(app.instance_path, 'projects.json'))
        allprojects.GetAllProjects()

        return render_template('projects.html', results=allprojects.all_data)

    @app.route('/tasks/<string:pid>', methods=['GET', 'POST'])
    def tasks(pid):
        alltasks = Tasks(os.path.join(app.instance_path, 'tasks.json'))
        alltasks.GetAllTasks()

        return render_template('tasks.html', results=alltasks.all_data)

    @app.route('/create-project/<string:id>', methods=['GET', 'POST'])
    @app.route('/create-project', methods=['GET', 'POST'])
    def create_project(id=None):
        class ProjectForm(FlaskForm):
            name = StringField('Project Name', validators=[validators.input_required()])

        form = ProjectForm()
        allprojects = Pojects(os.path.join(app.instance_path, 'projects.json'))

        if request.method == 'POST' and form.validate_on_submit():
            allprojects.AddProject(dict(id=uuid1().hex, name=form.name.data))
            flash('Project created successfully', 'success')

            return redirect(url_for('create_project'))

        return render_template('form.html', form=form, form_title='Create project')

    @app.route('/create-task/<string:pid>', methods=['GET', 'POST'])
    def create_task(pid):
        class TaskForm(FlaskForm):
            name = StringField('Task Name', validators=[validators.input_required()])
            weight = SelectField('Task weight', choices=[(item, item) for item in range(-100, 100, 1)], coerce=int, default=0)
            python_script = StringField('Python absolute script', validators=[validators.input_required()])

        form = TaskForm()
        alltasks = Tasks(os.path.join(app.instance_path, 'tasks.json'))

        if request.method == 'POST' and form.validate_on_submit():
            if not os.path.isfile(form.python_script.data):
                flash('Python script does not exist', 'error')
                return redirect(url_for('create_task', pid=pid))

            task_id = uuid1().hex
            task_log_path = os.path.join(app.TASK_LOGS_PATH, task_id + '.out')
            alltasks.AddTask(dict(id=task_id, pid=pid, name=form.name.data, weight=form.weight.data, script=form.python_script.data, runtime_log=task_log_path))
            flash('Task created successfully', 'success')

            return redirect(url_for('create_task', pid=pid))

        return render_template('form.html', form=form, form_title='Create Task')

    @app.route('/list-tasks')
    def list_tasks():
        return render_template('list-tasks.html')

    @app.context_processor
    def context():
        site_context = {}
        site_context['version'] = __version__

        return site_context

    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    os.environ['FLASK_ENV'] = 'development'
