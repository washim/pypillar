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
from tinydb import TinyDB, where, Query
from pypillar.common import Worker
from datetime import datetime

__version__ = '0.0.3'

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.urandom(12),
        VERSION=__version__
    )
    app.runtime_log_path = os.path.join(app.instance_path, 'runtime')
    app.task_log_folder = 'task_log'
    app.io_folder = 'io'

    if os.path.isdir(app.instance_path) == False:
        os.mkdir(app.instance_path)

    if os.path.isdir(app.runtime_log_path) == False:
        os.mkdir(app.runtime_log_path)

    app.DB = TinyDB(os.path.join(app.instance_path, 'db.json'))

    @app.route('/')
    def home():
        return redirect(url_for('projects'))

    @app.route('/task-log/<string:tid>', methods=['GET', 'POST'])
    def task_log(tid):
        task = app.DB.table('tasks').get(where('id') == tid)
        try:
            with open(task['task_log_path']) as outfile:
                log_content = outfile.read()
        except:
            log_content = 'No logs found yet.'

        if not len(log_content):
            log_content = 'No logs found yet.'

        try:
            log_content = json.dumps(json.loads(log_content), indent=4)
        except:
            pass

        return render_template('task_log.html', data=log_content)

    @app.route('/run/<string:pid>', methods=['GET', 'POST'])
    def run(pid):
        class RunForm(FlaskForm):
            class Meta:
                csrf = False
            input = TextAreaField('Api Post Data', render_kw={'rows': 10})

        form = RunForm()
        return render_template('run.html', pid=pid, form=form, form_title='Provide input data to run this project tasks', btn_name='Run Now')

    @app.route('/editor', methods=['GET', 'POST'])
    def editor():
        class EditorForm(FlaskForm):
            class Meta:
                csrf = False
            code_editor = TextAreaField('Code Editor', validators=[validators.input_required()])

        form = EditorForm()

        with open(request.args.get('file'), encoding='utf-8') as outfile:
            form.code_editor.data = outfile.read()

        if request.method == 'POST' and form.validate_on_submit():
            with open(request.args.get('file'), 'wb') as outfile_write:
                outfile_write.write(str(request.form['code_editor']).encode('utf-8'))

            flash('Script updated successfully', 'success')

            return redirect(url_for('editor', file=request.args.get('file')))

        return render_template('form.html', form=form, form_title='Live Code Editor')

    @app.route('/history/<string:pid>/<string:type>/<string:action>/<string:id>', methods=['GET', 'POST'])
    @app.route('/history/<string:pid>/<string:type>/<string:action>', methods=['GET', 'POST'])
    def history(pid, type, action, id=None):
        params = {'pid': pid, 'type': type, 'action': action, 'id': id}
        if type == 'io' and action == 'lists':
            file_data = []
            file_path = os.path.join(app.runtime_log_path, pid, app.io_folder)
            for file in os.listdir(file_path):
                file_info = {}
                if file.endswith('.in'):
                    file_info['request_id'] = file.split('.')[0]
                    file_info['timestamp'] = os.path.getmtime(os.path.join(file_path, file))
                    file_data.append(file_info)

            file_data = list(sorted(file_data, key=lambda x: x['timestamp'], reverse=True))
            for item in file_data:
                item['timestamp'] = datetime.fromtimestamp(item['timestamp']).strftime("%A, %B %d, %Y %I:%M:%S")
            return render_template('io.html', results=file_data, params=params)

        elif type == 'io' and action == 'view' and id:
            input = os.path.join(app.runtime_log_path, pid, app.io_folder, id + '.in')
            output = os.path.join(app.runtime_log_path, pid, app.io_folder, id + '.out')
            with open(input) as outfile:
                input_data = json.dumps(json.loads(outfile.read()), indent=4)
            with open(output) as outfile:
                output_data = json.dumps(json.loads(outfile.read()), indent=4)
            return render_template('requests.html', params=params, input_data=input_data, output_data=output_data)
        elif type == 'io' and action == 'delete' and id:
            input = os.path.join(app.runtime_log_path, pid, app.io_folder, id + '.in')
            output = os.path.join(app.runtime_log_path, pid, app.io_folder, id + '.out')
            os.remove(input)
            os.remove(output)
            flash('Request deleted successfully.', 'success')
            return redirect(url_for('history', pid=pid, type='io', action='lists'))

    @app.route('/api/<string:project_id>', methods=['GET', 'POST'])
    def run_api(project_id):
        data = []
        request_id = uuid1().hex

        if request.method == 'POST' and project_id:
            io_log_path = os.path.join(app.runtime_log_path, project_id, app.io_folder)
            if request.get_data():
                try:
                    data = json.loads(request.get_data())
                except Exception as e:
                    return jsonify({"JSONDecodeError": str(e)})

            original_input_file = os.path.join(io_log_path, request_id + '.in')
            with open(original_input_file, 'w+') as outfile:
                outfile.write(json.dumps(data))

            alltasks = app.DB.table('tasks').search(where('pid') == project_id)
            runner = Worker(alltasks, original_input_file, request_id)
            response = runner.run()

            original_output_file = os.path.join(io_log_path, request_id + '.out')
            with open(original_output_file, 'w+') as outfile:
                outfile.write(response)
            return response
        else:
            return jsonify({'error': 'Bad request', 'message': 'requestid and projectid required.', 'status': 400})

    @app.route('/projects', methods=['GET', 'POST'])
    def projects():
        allprojects = app.DB.table('projects').all()
        return render_template('projects.html', results=allprojects)

    @app.route('/tasks/<string:pid>', methods=['GET', 'POST'])
    def tasks(pid):
        alltasks = app.DB.table('tasks').search(where('pid') == pid)
        return render_template('tasks.html', results=alltasks)

    @app.route('/create-project/<string:action>/<string:id>', methods=['GET', 'POST'])
    @app.route('/create-project', methods=['GET', 'POST'])
    def create_project(action=None, id=None):
        class ProjectForm(FlaskForm):
            class Meta:
                csrf = False
            name = StringField('Project Name', validators=[validators.input_required()])

        form = ProjectForm()
        projects = app.DB.table('projects')

        if action == 'edit':
            project = projects.get(where('id') == id)
            form.name.data = project['name']

        if request.method == 'POST' and form.validate_on_submit():
            project_id = uuid1().hex
            project_log_path = os.path.join(app.runtime_log_path, project_id)
            project_io_log_path = os.path.join(project_log_path, app.io_folder)
            project_task_log_path = os.path.join(project_log_path, app.task_log_folder)

            if os.path.isdir(project_log_path) == False:
                os.mkdir(project_log_path)

            if os.path.isdir(project_io_log_path) == False:
                os.mkdir(project_io_log_path)

            if os.path.isdir(project_task_log_path) == False:
                os.mkdir(project_task_log_path)

            if action == 'edit':
                projects.update({'name': request.form['name']}, Query().id == id)
                flash('Project updated successfully', 'success')
                return redirect(url_for('create_project', action=action, id=id))
            else:
                projects.insert(dict(id=project_id, name=form.name.data))
                flash('Project created successfully', 'success')
                return redirect(url_for('create_project'))

        return render_template('form.html', form=form, form_title='Create or Edit project')

    @app.route('/create-task/<string:pid>/<string:action>/<string:id>', methods=['GET', 'POST'])
    @app.route('/create-task/<string:pid>', methods=['GET', 'POST'])
    def create_task(pid, action=None, id=None):
        class TaskForm(FlaskForm):
            class Meta:
                csrf = False
            name = StringField('Task Name', validators=[validators.input_required()])
            weight = SelectField('Task weight', choices=[(item, item) for item in range(-100, 100, 1)], coerce=int, default=0)
            python_script = StringField('Python absolute script', validators=[validators.input_required()])

        form = TaskForm()
        tasks = app.DB.table('tasks')

        if action == 'edit':
            task = tasks.get(where('id') == id)
            form.name.data = task['name']
            form.weight.data = int(task['weight'])
            form.python_script.data = task['script']

        if request.method == 'POST' and form.validate_on_submit():
            if not os.path.isfile(form.python_script.data):
                flash('Python script does not exist', 'error')
                return redirect(url_for('create_task', pid=pid))

            task_id = uuid1().hex
            task_log_path = os.path.join(app.runtime_log_path, pid, app.task_log_folder, task_id + '.out')

            if action == 'edit':
                tasks.update(dict(name=request.form['name'], weight=request.form['weight'], script=request.form['python_script']), Query().id == id)
                flash('Task update successfully', 'success')
                return redirect(url_for('create_task', pid=pid, action='edit', id=id))
            else:
                tasks.insert(dict(id=task_id, pid=pid, name=form.name.data, weight=form.weight.data, script=form.python_script.data, task_log_path=task_log_path))
                flash('Task created successfully', 'success')
                return redirect(url_for('create_task', pid=pid))

        return render_template('form.html', form=form, form_title='Create Task')

    @app.context_processor
    def context():
        site_context = {}
        site_context['version'] = __version__

        return site_context

    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    os.environ['FLASK_ENV'] = 'development'
