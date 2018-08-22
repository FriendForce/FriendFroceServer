from flask import jsonify, request, url_for
from app import app, db
from app.models import Person, Tag, Label
import json
import slugify
import random

def find_tag_type(tag_text):
    return "generic"

@app.route('/')
@app.route('/index')
def index():
    return "Hello, UPDATED World!"

@app.route('/create_person/<person_name>')
def create_new_person(person_name):
    person = Person(name=person_name)
    db.session.add(person)
    db.session.commit()
    return "Added %s to db"%(person_name)

@app.route('/api/person', methods=['POST'])
def create_person():
    data = request.get_json() or {}
    person = Person()

    if 'slug' in data:
        #handle the fact that it's a known person
        person.slug = data['slug']
    else:
        if 'first_name' not in data or 'last_name' not in data:
            return "ERROR: missing required field"
        person = Person()
        person.first_name = data['first_name'].title()
        person.last_name = data['last_name'].title()
        pre_slug = "%s %s %d"%(data['first_name'].lower(), data['last_name'].lower(),random.randint(0,10000000))
        person.slug = slugify.slugify(pre_slug)
    if 'is_user' in data:
        person.is_user = data.is_user
    #weird thing: need to create the response before committing object?
    response = jsonify(person.json())
    db.session.add(person)
    db.session.commit()
    return response

def create_label_from_tag(tag):
    #TODO: more sophisticated things for example
    # Loc: should be a type of label
    labels = Label.query.filter(Label.text==tag.text)
    if labels.count() > 0:
        return labels[0]
    else:
        label = Label()
        label.text = tag.text
        return label



@app.route('/api/tag', methods=['POST'])
def create_tag():
    data = request.get_json() or {}
    if not 'originator' in data or not 'subject' in data or not 'text' in data:
        return "ERROR: missing required field"
    # Originator and Subject will both be slugs
    originator = Person.query.filter(Person.slug==data['originator'])[0]
    subject = Person.query.filter(Person.slug==data['subject'])[0]
    tag = Tag()
    tag.originator = originator.id
    tag.subject = subject.id
    tag.subject_slug = subject.slug
    tag.originator_slug = originator.slug
    tag.text = data['text']
    tag.type = find_tag_type(tag.text)
    tag.slug = slugify.slugify("%s %s %s"%(originator.slug, subject.slug, data['text']))
    if 'publicity' in data:
        tag.publicity = data['publicity']
    else:
        tag.publicity = 'public'
    label = create_label_from_tag(tag)
    db.session.add(label)
    tag.label = label.id
    response = jsonify(tag.json())
    db.session.add(tag)
    db.session.commit()
    return response

@app.route('/api/labels', methods=['POST'])
def get_labels():
    data = request.get_json() or {}
    labels = Label.query.all()
    labels_out = list(map(lambda label: label.text, labels))
    return jsonify(labels_out)

@app.route('/api/known_tags', methods=['POST'])
def find_known_tags():
    data = request.get_json() or {}
    if not 'user' in data:
        return "ERROR: missing required field"
    user_id = Person.query.filter(Person.slug==data['user'])[0].id
    user_tags = Tag.query.filter(Tag.originator==user_id or Tag.publicity=='public').all()
    tags = list(map(lambda tag: tag.to_deliverable(), user_tags))
    return jsonify(tags)


@app.route('/api/known_persons', methods=['POST'])
def find_known_persons():
    data = request.get_json() or {}
    if not 'user' in data:
        return "ERROR: missing required field"
    user_id = Person.query.filter(Person.slug==data['user'])[0].id
    user_tags = Tag.query.filter(Tag.originator==user_id).all()
    ids = set(map(lambda tag:tag.subject, user_tags))
    persons = list(map(lambda person:person.to_deliverable(), Person.query.filter(Person.id.in_(ids)).all()))
    response = jsonify(persons)
    return response


@app.route('/show_all_persons')
def show_all_persons():
    q = Person.query.all()
    persons = list(map(lambda person: person.json(), q))
    return jsonify(persons)

@app.route('/show_all_tags')
def show_all_tags():
    q = Tag.query.all()
    tags = list(map(lambda tag: tag.json(), q))
    return jsonify(tags)

@app.route('/show_all_labels')
def show_all_labels():
    q = Label.query.all()
    labels = list(map(lambda label: label.json(), q))
    return jsonify(labels)

@app.route('/api/update_db', methods=['POST'])
def update_db():
    tags_to_update = Tag.query.filter(Tag.originator_slug == None)
    print("number of tags to update originator = %d"%tags_to_update.count())
    for tag in tags_to_update:
        tag.originator_slug = Person.query.filter(Person.id == tag.originator)[0].slug
        db.session.add(tag)
    tags_to_update = Tag.query.filter(Tag.subject_slug == None)
    print("number of tags to update subject = %d"%tags_to_update.count())
    for tag in tags_to_update:
        tag.subject_slug = Person.query.filter(Person.id == tag.subject)[0].slug
        db.session.add(tag)
    db.session.commit()
    response = jsonify('db updated!')
    return response
