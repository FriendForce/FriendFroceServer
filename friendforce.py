from app import app, db
from app.models import Person, Tag, Label


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Person': Person, 'Tag': Tag, 'Label':Label}

if __name__ == '__main__':
    app.run(use_reloader=True, port=5000, threaded=True)
