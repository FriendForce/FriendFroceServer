from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

import os

app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import Result


@app.route('/')
def hello():
    return "Hello World!"

if __name__ == '__main__':
    print(os.environ['APP_SETTINGS'])
    app.run()
