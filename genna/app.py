from flask import Flask, render_template, request, redirect, url_for, Response
from functools import wraps
import os
import pandas as pd
from src.content import DataSet, get_global_vars
from src.utils import switch_button_state, PassUtils

app = Flask(__name__)
"""app.config['GENNA_INPUT_PATH'] = './data/datasets'
app.config['GENNA_CONFIG_FILE_PATH'] = 'config.yaml'
app.config['GENNA_ANNOTATIONS_PATH'] = './data/configs'
app.config['NAV_BAR'] = {
    'name': 'Home', 'link': '/'
}
#app.config['PREFIX'] = 'example1'
app.config['WORKFLOW_HEADER'] = 'example2'
app.config['WORKFLOW_STEP'] = 0
app.config['WORKFLOW_CONFIG'] = 'example'
app.config['WORKFLOW_NEXT_BUTTON_URL'] = 'transition1'"""
#### BASIC AUTH
def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    with open('pass_hash.key','r') as f:
        hsh = f.read().strip()
    print(PassUtils.hash_password(password))
    return username == 'bobby86' and PassUtils.check_hashed_password(password,hsh)

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def generate_page_config(app: Flask, config_name, list_files, list_configs, file_name):
    return dict(
        prefix = app.config['PREFIX'],
        nav_bar = app.config['NAV_BAR'],
        editable_config = False if 'WORKFLOW_CONFIG' in app.config else True,
        next_btn_url = app.config['WORKFLOW_NEXT_BUTTON_URL'],
        list_configs = list_configs, file_name = file_name,
        config_name = config_name, list_files = list_files,
        header = app.config['WORKFLOW_HEADER']
    )

@app.route("/")
@requires_auth
def home0():
    # Load list_files and list_configs as global variables
    list_configs, list_files = get_global_vars(app.config['GENNA_INPUT_PATH'], app.config['GENNA_CONFIG_FILE_PATH'])
    # print(app.static_url_path)
    # Default values for intro screen
    file_name = '.csv' if len(list_files)==0 else list_files[0]
    if 'WORKFLOW_CONFIG' in app.config:
        print('WORKFLOW_CONFIG', app.config['WORKFLOW_CONFIG'] )
        config_name = app.config['WORKFLOW_CONFIG']
    else:
        config_name = 'example'
    print('file_name', file_name )
    ds = DataSet(file_name, app.config['GENNA_INPUT_PATH'], app.config['GENNA_ANNOTATIONS_PATH'], config_name, app.config['GENNA_CONFIG_FILE_PATH'])
    ds.all()
    page_config = generate_page_config(app, config_name, list_files, list_configs, file_name)
    return render_template("base.html", 
            page_config = page_config, 
            ds = ds, )

@app.route("/annotate/<string:config_name>/<string:file_name>")
@requires_auth
def home(file_name,config_name):
    list_configs, list_files = get_global_vars(app.config['GENNA_INPUT_PATH'], app.config['GENNA_CONFIG_FILE_PATH'])
    ds = DataSet(file_name, app.config['GENNA_INPUT_PATH'], app.config['GENNA_ANNOTATIONS_PATH'], config_name, app.config['GENNA_CONFIG_FILE_PATH'])
    ds.all()
    page_config = generate_page_config(app, config_name, list_files, list_configs, file_name)
    pd.DataFrame(ds.ds_list).to_csv(os.path.join(app.config['ANNOTATIONS_LATEST_PATH'],f'{file_name}_{config_name}.csv'))
    return render_template("base.html", 
            page_config=page_config, 
            ds = ds, )



### ADD LINE
@app.route("/add_line/<string:config_name>/<string:file_name>/<string:dp_id>")
@requires_auth
def add_line(dp_id, file_name, config_name):
    list_configs, list_files = get_global_vars(app.config['GENNA_INPUT_PATH'], app.config['GENNA_CONFIG_FILE_PATH'])
    ds = DataSet(file_name, app.config['GENNA_INPUT_PATH'], app.config['GENNA_ANNOTATIONS_PATH'], config_name, app.config['GENNA_CONFIG_FILE_PATH'])
    ds.add_line(dp_id)
    ds.all()
    page_config = generate_page_config(app, config_name, list_files, list_configs, file_name)

    return render_template("base.html", 
            page_config=page_config, 
            ds = ds, )

### LABELLING
@app.route("/label/<string:label_type>/<string:config_name>/<string:file_name>/<string:label_name>/<string:dp_id>", methods=['POST'])
@requires_auth
def update(label_name, dp_id, file_name, config_name, label_type):
    received_url = request.form['url']
    received_label_name = request.form['label_name']
    label_title = request.form['label_title'].strip()

    ds = DataSet(file_name, app.config['GENNA_INPUT_PATH'], app.config['GENNA_ANNOTATIONS_PATH'], config_name, app.config['GENNA_CONFIG_FILE_PATH'])
    outcome = ds.annotate(idx = dp_id, content = label_name, label_type = label_type)
    #return redirect(f"/annotate/{config_name}/{file_name}#{dp_id}")
    
    data = {
        'name':f'button[name="{received_url}"]',
        'class':switch_button_state(received_label_name),
        'label_title':label_title,
        'outcome': outcome
    }
    print(outcome)
    return data

### ADDING COMMENTS
@app.route("/comment/<string:label_type>/<string:config_name>/<string:file_name>/<string:dp_id>", methods=['POST'])
@requires_auth
def add_comment(dp_id, file_name, config_name, label_type):
    comment = request.form.get("comment_field")
    print(label_type)
    ds = DataSet(file_name, app.config['GENNA_INPUT_PATH'], app.config['GENNA_ANNOTATIONS_PATH'], config_name, app.config['GENNA_CONFIG_FILE_PATH'])
    outcome = ds.annotate(idx = dp_id, content = comment, label_type = label_type)
    #return redirect(f"/annotate/{config_name}/{file_name}#{dp_id}")
    return {
        'outcome': outcome
        }

### CONTENT EDITING - EDIT
@app.route("/content_edits/<string:config_name>/<string:file_name>/<string:dp_id>", methods=['POST'])
@requires_auth
def edit_text(dp_id, file_name, config_name):
    comment = request.form.get("comment_field").strip()
    received_url = request.form['url']
    new_url = received_url.replace('content_edits','remove_edits')

    ds = DataSet(file_name, app.config['GENNA_INPUT_PATH'], app.config['GENNA_ANNOTATIONS_PATH'], config_name, app.config['GENNA_CONFIG_FILE_PATH'])
    outcome = ds.annotate(idx = dp_id, content = comment, label_type = 'content')
    print(outcome)
    #return redirect(f"/annotate/{config_name}/{file_name}#{dp_id}")
    return {
       'outcome': outcome,
       'name': f'badge[name="{received_url}"]',
       'class': "badge bg-info",
       'new_url': new_url
        }

### CONTENT EDITING - RESET EDIT
@app.route("/remove_edits/<string:config_name>/<string:file_name>/<string:dp_id>", methods=['POST'])
@requires_auth
def remove_edits(dp_id, file_name, config_name):
    received_url = request.form['url']
    new_url = received_url.replace('remove_edits','content_edits')

    ds = DataSet(file_name, app.config['GENNA_INPUT_PATH'], app.config['GENNA_ANNOTATIONS_PATH'], config_name, app.config['GENNA_CONFIG_FILE_PATH'])
    outcome = ds.annotate(idx = dp_id, content = '', label_type = 'content', remove_edits = True)
    print(outcome)
    original_content = ds.get_target(dp_id)
    #return redirect(f"/annotate/{config_name}/{file_name}#{dp_id}")
    return {
        'outcome': outcome,
        'name': f'badge[name="{received_url}"]',
        'original_content': original_content,
        'class': "badge badge-transparent",
        'new_url': new_url
        }

if __name__ == '__main__':
    app.run(port=5050, debug=os.environ.get('DEBUG',False))