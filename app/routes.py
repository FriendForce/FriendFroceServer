from app import app, db
from app.models import Person
import json

@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"

@app.route('/create_person/<person_name>')
def create_person(person_name):
    person = Person(name=person_name)
    db.session.add(person)
    db.session.commit()
    return "Added %s to db"%(person_name)

@app.route('/show_all_persons')
def show_all_persons():
    q = Person.query.all()
    names = list(map(lambda person: person.name, q))
    return json.dumps(names)
