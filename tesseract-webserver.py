import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
import shutil

import flask
from flask import Flask
from flask import request


TESS_DATA = '/usr/share/tessdata'
TESSERACT_BASE = 'tesseract'

app = Flask(__name__)


def list_lang(tess_data_dir):
    if isinstance(tess_data_dir, Path):
        path = tess_data_dir
    else:
        path = Path(tess_data_dir)
    if not path.is_dir():
        raise IOError('bad dir {}'.format(tess_data_dir))
    return map(lambda lang_file: lang_file.name.rstrip('.traineddata'), path.glob('*.traineddata'))


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/solve', methods=['POST'])
def solve():
    lang = request.form['l'] or request.args.get('l', 'eng')
    lang = lang.lower().strip()
    if lang not in list_lang(TESS_DATA):
        resp = {'err': True, 'msg': 'language "{}" is not valid'.format(lang)}
        return flask.jsonify(**resp), 500

    picture_file = request.files['pict']
    if not picture_file:
        resp = {'err': True, 'msg': 'no picture file'}
        return flask.jsonify(**resp), 500
    with NamedTemporaryFile() as in_tmp_file:
        shutil.copyfileobj(picture_file, in_tmp_file)
        cmd = [TESSERACT_BASE, in_tmp_file.name, 'stdout', '-l', lang]
        environ = os.environ
        if 'TESSDATA_PREFIX' not in environ:
            environ = dict(environ)
            environ['TESSDATA_PREFIX'] = str(Path(TESS_DATA).parent)
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environ)
        stdout, stderr = popen.communicate()
        if stderr:
            resp = {'err': True, 'msg': str(stderr, 'utf-8').strip()}
        else:
            resp = {'err': False, 'msg': str(stdout, 'utf-8').strip()}
    return flask.jsonify(**resp)


if __name__ == '__main__':
    app.run()
