from flask import jsonify, request, url_for
from app import app, db
from app.models import Person, Tag, Label, Account
import json
import slugify
import random
import firebase_admin
from firebase_admin import credentials, auth
from datetime import datetime

cred = credentials.Certificate(app.config['FIREBASE_CREDENTIALS'])
firebase_admin.initialize_app(cred)

def create_account_from_token(token):
    account = Account()
    account.firebase_user_id = token['uid']
    account.email = token['email']
    account.email_verified = token['email_verified']
    account.name = token['name']
    account.photo_url = token['picture']
    account.updated = datetime.now()
    db.session.add(account)
    db.session.commit()
    return account

def associate_account_with_person(account):
    if account.person is not None:
        return account.person
    #For now do naive thing and assume we won't have name collisions
    names = account.name.split(' ')
    name_matches = Person.query.filter(Person.first_name==names[0] and Person.last_name==names[end] and Person.is_user==False)
    person_id = -1
    if name_matches.count() == 0:
        # Create a person
        print("creating a person for the account")
        person = Person()
        person.first_name = names[0]
        person.last_name = names[end]
        person.slug = person.create_slug()
        person.photo_url = account.photo_url
        person.is_user = True
        db.session.add(person)
        person_id = person.id
        account.add_person(person_id)
        db.session.add(account)
        db.commit()
    elif name_matches.count() == 1:
        # Associate account with person
        # TODO make it so you can have multiple accounts associated
        # with the same person
        print("associating single person with account")
        person = name_matches[0]
        person.is_user = True
        if person.photo_url is None or len(person.photo_url) is 0:
            person.photo_url = account.photo_url
        person.updated = datetime.now()

        db.session.add(person)
        person_id = person.id
        account.add_person(person_id)
        db.session.add(account)
        db.session.commit()
    elif name_matches.count() > 1:
        print("Multiple people with same name")
    return person_id


def get_account_and_person(undecoded_token):
    decoded_token = auth.verify_id_token(undecoded_token)
    account = Account.query.filter(Account.email==decoded_token['email'])
    account_id = -1
    person_id = -1
    if account.count() is 1:
        print("found existing account for %s"%decoded_token["email"])
        account_id = account[0].id
        person_id = account[0].person
    return (account_id, person_id)

def create_account_and_person(undecoded_token):
    decoded_token = auth.verify_id_token(undecoded_token)
    account = create_account_from_token(decoded_token)
    account_id = account.id
    person_id = associate_account_with_person(account)
    return (account_id, person_id)


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
    (account_id, person_id) = get_account_and_person(data['token'])
    person = Person()
    print ("got person")
    print (data)
    #handle an updated person
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
    db.session.add(person)

    #Create a tag indicating who created this person
    tag = Tag()

    db.session.add(tag)
    response = jsonify(person.to_deliverable())
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

def create_tag(subject_id, originator_id, text, publicity="public"):
    tag = Tag()
    tag.originator = originator_id
    tag.originator_slug = Person.query.filter(Person.id==originator_id)[0].slug
    tag.subject = subject_id
    tag.subject_slug = Person.query.filter(Person.id==subject_id)[0].slug
    tag.text = text
    label = create_label_from_tag(tag)
    db.session.add(label)
    tag.label = label.id
    tag.publicity = publicity
    tag.slug = tag.create_slug()
    return tag



@app.route('/api/tag', methods=['POST'])
def create_tag_request():
    print("got tag create request")
    data = request.get_json() or {}
    (account_id, person_id) = get_account_and_person(data['token'])
    # Check if tag already exists - this check should be more elaborate
    if 'id' in data:
        q = Tag.query.filter(Tag.slug == data['id'])
        if q.count() > 0:
            tag = q[0]
            tag.updated = datetime.datetime.now()
    subject = -1
    if 'subject' in data:
        subject = Person.query.filter(Person.slug==data['subject'])[0]
    else:
        print("Error could not create tag becasue no subject")
        return -1
    text = ""
    if 'text' or 'label' in data:
        if 'label' in data:
            text = data['label']
        else:
            text = data['text']
    else:
        print("Error could not create tag becasue no text")
        return -1
    publicity = "public"
    if 'publicity' in data:
        publicity = data['publicity']
    tag = create_tag(subject.id, person_id, text, publicity=publicity)
    db.session.add(tag)
    response = jsonify(tag.to_deliverable())
    db.session.commit()
    print("Created tag")
    return response

@app.route('/api/labels', methods=['POST'])
def get_labels():
    data = request.get_json() or {}
    labels = Label.query.all()
    labels_out = list(map(lambda label: label.text, labels))
    return jsonify(labels_out)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    (account_id, person_id) = get_account_and_person(data['token'])
    new_account = False
    if account_id is -1:
        (account_id, person_id) = create_account_and_person(data['token'])
        new_account = True
    person = Person.query.filter(Person.id == person_id)[0]
    return jsonify({'person':person.to_deliverable(), 'new_account':new_account})


@app.route('/api/known_tags', methods=['POST'])
def find_known_tags():
    data = request.get_json() or {}
    (account_id, person_id) = get_account_and_person(data['token'])
    user_tags = Tag.query.filter(Tag.originator==person_id or Tag.publicity=='public').all()
    tags = list(map(lambda tag: tag.to_deliverable(), user_tags))
    return jsonify(tags)


@app.route('/api/known_persons', methods=['POST'])
def find_known_persons():
    data = request.get_json() or {}
    (account_id, person_id) = get_account_and_person(data['token'])
    user_tags = Tag.query.filter(Tag.originator==person_id).all()
    ids = set(map(lambda tag:tag.subject, user_tags))
    ids.add(person_id) # make sure people know about themselves
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
