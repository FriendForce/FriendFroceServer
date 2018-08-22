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
    print ("got person")
    print (data)
    if 'id' in data:
        q = Person.query.filter(Person.slug == data['id'])
        if q.count() > 0:
            person = q[0]
            person.updated = datetime.datetime.now()

    if 'first_name' not in data and 'last_name' not in data and 'name' not in data:
        return "ERROR: missing required field"
    person = Person()
    if 'name' in data:
        person.first_name = data['name'].split(' ')[0].title()
        person.last_name = data['name'].split(' ')[1].title()
    else:
        person.first_name = data['first_name'].title()
        person.last_name = data['last_name'].title()
    pre_slug = "%s %s %d"%(person.first_name.lower(), person.last_name.lower(),random.randint(0,10000000))
    person.slug = slugify.slugify(pre_slug)
    #weird thing: need to create the response before committing object?
    response = jsonify(person.to_deliverable())
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


@app.route('/api/tag/delete', methods=['POST'])
def delete_tag():
    data = request.get_json() or {}
    if 'id' in data:
        q = Tag.query.filter(Tag.slug == data['id']).delete()
        db.session.commit()
        return jsonify({'action':'delete', 'id':data['id']})
    else:
        return jsonify('error: no id')



@app.route('/api/tag', methods=['POST'])
def create_tag():
    data = request.get_json() or {}
    print ("got tag request")
    print (data)
    tag = Tag()
    # Check if tag already exists - this check should be more elaborate
    if 'id' in data:
        q = Tag.query.filter(Tag.slug == data['id'])
        if q.count() > 0:
            tag = q[0]
            tag.updated = datetime.datetime.now()
    if 'originator' in data:
        originator = Person.query.filter(Person.slug==data['originator'])[0]
        tag.originator = originator.id
        tag.originator_slug = originator.slug
    if 'subject' in data:
        subject = Person.query.filter(Person.slug==data['subject'])[0]
        tag.subject = subject.id
        tag.subject_slug = subject.slug
    if 'text' or 'label' in data:
        if 'label' in data:
            tag.text = data['label']
        else:
            tag.text = data['text']
        tag.type = find_tag_type(tag.text)
        #Create a label
        label = create_label_from_tag(tag)
        db.session.add(label)
        tag.label = label.id
    if 'publicity' in data:
        tag.publicity = data['publicity']
    else:
        tag.publicity = 'public'
    tag.slug = slugify.slugify("%s %s %s"%(tag.originator_slug, tag.subject_slug, tag.text))
    response = jsonify(tag.to_deliverable())
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
