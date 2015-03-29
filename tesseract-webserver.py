#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image
import flask
from flask import Flask
from flask import request


TESSDATA_PREFIX = os.environ.get('TESSDATA_PREFIX') or '/usr/share/tesseract/tessdata'
TESSERACT_PATH = os.environ.get('TESSERACT_PATH') or 'tesseract'
PORT = os.environ.get('TESS_SERVER_PORT') or 5033

app = Flask(__name__)


def list_lang(tess_data_dir):
    if isinstance(tess_data_dir, Path):
        path = tess_data_dir
    else:
        path = Path(tess_data_dir)
    if not path.is_dir():
        raise IOError('bad dir {}'.format(tess_data_dir))
    return lambda lang_file: lang_file.name.rstrip('.traineddata'), path.glob('*.traineddata')


langs = dict(list_lang(TESSDATA_PREFIX))

@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/solve', methods=['POST'])
def solve():
    lang = request.form.get('l', None) or request.args.get('l', 'eng')
    lang = lang.lower().strip()
    if lang not in langs:
        resp = {'err': True, 'msg': 'language "{}" is not valid'.format(lang)}
        return flask.jsonify(**resp), 500

    picture_file = request.files['pict']
    if not picture_file:
        resp = {'err': True, 'msg': 'no picture file'}
        return flask.jsonify(**resp), 500
    with NamedTemporaryFile(suffix='.bmp') as in_tmp_file:
        img = Image.open(picture_file)
        img.save(in_tmp_file, 'BMP')
        in_tmp_file.flush()
        cmd = [TESSERACT_PATH, in_tmp_file.name, 'stdout', '-l', lang]
        environ = os.environ
        if 'TESSDATA_PREFIX' not in environ:
            environ = dict(environ)
            environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                                 env=environ)
        stdout, stderr = popen.communicate()
        if stderr:
            resp = {'err': True, 'msg': str(stderr, 'utf-8').strip()}
        else:
            resp = {'err': False, 'msg': str(stdout, 'utf-8').strip()}
        return flask.jsonify(**resp)


if __name__ == '__main__':
    app.run(port=PORT)