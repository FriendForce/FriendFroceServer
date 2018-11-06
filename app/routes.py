from flask import jsonify, request, url_for, send_from_directory, render_template, Response
from app import app, db
from app.models import Person, Tag, Label, Account
import json
import slugify
import random
import firebase_admin
from firebase_admin import credentials, auth
from datetime import datetime
import pdb
import os
from sqlalchemy import or_, and_
import requests
from app.special_labels import SPECIAL_LABELS


cred = credentials.Certificate(app.config['FIREBASE_CREDENTIALS'])
firebase_admin.initialize_app(cred)

def condition_label_text(text):
    chunks = text.split(":")
    for i, chunk in enumerate(chunks):
        chunks[i] = chunk.strip().title()
    return ":".join(chunks)

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
    print("account %d from token:" % account.id)
    print(token)
    return account

def associate_account_with_person(account_id):
    account = Account.query.filter(Account.id==account_id)[0]
    if account.person is not None:
        return account.person
    #For now do naive thing and assume we won't have name collisions
    names = account.name.split(' ')
    name_matches = Person.query.filter(Person.first_name==names[0], Person.last_name==names[-1], Person.is_user==False)
    person_id = -1
    if name_matches.count() == 0:
        # Create a person
        print("creating a person for the account")
        person = Person()
        person.first_name = names[0]
        person.last_name = names[-1]
        person.name = account.name
        person.slug = person.create_slug()
        person.photo_url = account.photo_url
        person.is_user = True
        db.session.add(person)
        db.session.commit()
        person_id = person.id
        account.add_person(person_id)
        db.session.add(account)
        db.session.commit()

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
        db.session.commit()
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
        if person_id is None or person_id == -1:
            person_id = associate_account_with_person(account_id)
        print("account: %d"%account_id)
        print("person:%d"%(person_id))
    return (account_id, person_id)

def create_account_and_person(undecoded_token):

    decoded_token = auth.verify_id_token(undecoded_token)
    account = create_account_from_token(decoded_token)
    print("creating account from token")
    print(decoded_token)
    account_id = account.id
    person_id = associate_account_with_person(account_id)
    return (account_id, person_id)

def do_tag_logic(tag):

    '''
    Need large string of logic based on tag type
    - If it's a special tag, generall you want to create the label with the prefix
    - If it has_person - only keep label with specific tag
    - Default to private if it's a meeting
    - Default to private if it's a know_person
    - Default to private if it's a todo
    - If it's contact info, default to private
    - If a tag goes from public to private, delete the label
    - If someone deletes a tag on themselves, make it go to private
    - Is there any reason to have prefixes be the same? Should probably remove spaces from slugs
    - If someone searches by labels associated with types (like "todo:") - show them all of them
    - All specific labels should be private but autosuggest them
    '''
    tag_types = decode_tag_types(tag.type)
    if "personal" in tag_types or "unique" in tag_types:
        tag.publicity = "private"
    return tag

def encode_tag_types(tag_types):
    sep_char = ","
    return sep_char.join(tag_types)

def decode_tag_types(tag_type_string):
    #note this needs to be coordinated with find_tag_type function for now
    sep_char = ","
    return tag_type_string.split(sep_char)


def find_tag_type(tag_text):
    tag_types = set([])
    compound_tag = False
    if tag_text == "had convo":
        tag_types.add("repeatable")
    if tag_text == "+1":
        tag_types.add("repeatable")
    if tag_text == "-1":
        tag_types.add("repeatable")
    if len(tag_text.split(":")) > 1:
        tag_types.add("potential-special")
        tag_pre = "".join(tag_text.split(":")[0].split(" ")).lower()
        tag_post = ":".join(tag_text.split(":")[1:]).lower()
        compound_tag = True
    if "http" in tag_text.lower():
        tag_types.add("website")
        tag_types.add("unique")

    if len(tag_types) is 0:
        tag_types.add("generic")
    if compound_tag is False:
        return encode_tag_types(tag_types)

    if tag_pre in map(lambda label:"".join(label.lower().split(" ")), SPECIAL_LABELS.keys()):
        tag_types.add("special")
        tag_types.add(tag_pre)
        #TODO need to match against non exact matches
        for type in SPECIAL_LABELS[tag_text.split(":")[0]]['types']:
            tag_types.add(type)
    #Other Special Things
    if tag_pre == "datemetfb":
        tag_types.add("metadata")

    #TODO: if you detect an email or phone number in the thing, label it
    # Maybe do this on the front end
    #TODO: detect websites and automatically label it.
    # User verification is important!
    return encode_tag_types(tag_types)





@app.route('/', defaults={'path':''})
@app.route('/<path:path>')
def serve(path):
    print("serving!")
    print(path)
    if path[0:3] != "api":
        return send_from_directory('./react_app/build/','index.html')
    else:
        return "foo"

@app.route('/api/index')
def index():
    return "Hello, UPDATED World!"

@app.route('/api/create_person/<person_name>')
def create_new_person(person_name):
    person = Person(name=person_name)
    db.session.add(person)
    db.session.commit()
    return "Added %s to db"%(person_name)

@app.route('/api/person', methods=['POST'])
def create_person():
    data = request.get_json() or {}
    (account_id, originator_id) = get_account_and_person(data['token'])
    person = Person()
    #handle an updated person
    if 'id' in data:
        q = Person.query.filter(Person.slug == data['id'])
        if q.count() > 0:
            person = q[0]
            person.updated = datetime.datetime.now()
    if 'first_name' not in data and 'last_name' not in data and 'name' not in data:
        return "ERROR: missing required field"
    if 'name' in data:
        name = data['name'].strip().title()
        first_name = name.split(' ')[0]
        if len(name.split(' ')) > 1:
            last_name = ' '.join(name.split(' ')[1:])
        else:
            last_name=''

    else:
        first_name = data['first_name'].strip().title()
        last_name = data['last_name'].strip().title()
        name = ' '.join(first_name, last_name)

    # For now names will be singular and we'll just note possible duplicates
    matching_persons = Person.query.filter(Person.name==name)
        #assume we found a dumplicate person
    if matching_persons.count() > 0:
        #pdb.set_trace()
        person = matching_persons[0]
        tag = Tag()
        tag.initialize('possible duplicate', originator_id, person.id, type="metadata", publicity="private")
        if Tag.query.filter(Tag.slug==tag.slug).count() == 0:
            db.session.add(tag)
        print("creating a tag to mark %s as a possible duplicate"%person.slug);
    else:
        person = Person()
        person.name = name
        person.first_name = first_name
        person.last_name = last_name
        person.slug = person.create_slug()
        db.session.add(person)
        tag = Tag()
        tag.initialize('added', originator_id, person.id, subject_slug=person.slug, type="metadata", publicity="private")
        db.session.add(tag)
        print("adding person %s"%person.slug)
    response = jsonify(person.to_deliverable())
    db.session.commit()
    return response

def create_labels_from_text(text, publicity="public"):
    print("creating a label from: " + text)
    labels = []
    label = Label()
    label.set_text(text)
    label.type = "generic"
    label.publicity = publicity
    label_slug = label.create_slug()
    existing_label = Label.query.filter_by(slug=label_slug)
    if existing_label.count() > 0:
        label = existing_label[0]
    else:
        label.slug = label_slug
        db.session.add(label)
        db.session.flush()
    labels.append(label.id)

    split_text = text.split(":")
    if  len(split_text) is 2 and len(split_text[1]) > 0 and split_text[0] in SPECIAL_LABELS.keys():
        print("Compound label")
        modifier_label = Label()
        modifier_label.set_text(split_text[1])
        modifier_label.type = split_text[0]
        modifier_label.publicity = publicity
        modifier_label_slug = modifier_label.create_slug()
        existing_modifier_label = Label.query.filter_by(slug=modifier_label_slug)
        if existing_modifier_label.count() > 0:
            modifier_label = existing_modifier_label[0]
        else:
            modifier_label.slug = modifier_label_slug
            db.session.add(modifier_label)
            db.session.flush()
        labels.append(modifier_label.id)
    db.session.commit()
    return labels


def create_labels_from_tag(tag):
    #TODO: more sophisticated things for example
    # Loc: should be a type of label
    labels = []
    tag_types = decode_tag_types(tag.type)
    # Policy for now, people can't create new pre's organically
    if "metadata" in tag_types or "unique" in tag_types:
        return labels
    publicity = "public"
    if "personal" in tag_types:
        #If it's a personal thing, you want to create the label for just that person
        #And grab the prefix
        publicity = "private"
    if tag.publicity == "private":
        publicity = "private"
    labels = create_labels_from_text(tag.text, publicity=publicity)
    return labels


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

@app.route('/api/account', methods=['POST'])
def update_account():
    data = request.get_json() or {}
    (account_id, person_id) = get_account_and_person(data['token'])
    account = Account.query.filter(Account.id==account_id)
    account.update(data['params'])
    db.session.commit()
    return(jsonify(account[0].to_deliverable()))

@app.route('/api/tag', methods=['POST'])
def create_tag_request():
    data = request.get_json() or {}
    (account_id, person_id) = get_account_and_person(data['token'])
    # Check if tag already exists - this check should be more elaborate
    tag = Tag()
    tag.originator = person_id
    tag.originator_slug = Person.query.filter(Person.id==person_id)[0].slug
    new = True
    # Update tag
    if 'id' in data:
        q = Tag.query.filter(Tag.slug == data['id'])
        if q.count() > 0:
            print("updating tag %s"%data['id'])
            tag = q[0]
            new = False
    # Someone is creating the same tag
    subject = -1
    if 'subject' in data:
        subject = Person.query.filter(Person.slug==data['subject'])[0]
        tag.subject = subject.id
        tag.subject_slug = subject.slug
    else:
        print("Error could not create tag becasue no subject")
        return -1
    text = ""
    if 'text' or 'label' in data:
        if 'label' in data:
            text = data['label']
        else:
            text = data['text']
        tag.text = condition_label_text(text)
        tag.type = find_tag_type(text)
    else:
        print("Error could not create tag becasue no text")
        return -1
    publicity = "public"
    if 'publicity' in data:
        publicity = data['publicity']
    tag.publicity = publicity
    tag = do_tag_logic(tag)
    labels = create_labels_from_tag(tag)
    if len(labels) > 0:
        #TODO: Return the label in the response as well.
        tag.label = labels[0]
    tag.slug = tag.create_slug()
    if ("repeatable" in decode_tag_types(tag.type)):
        tag.slug = tag.slug+"-".join(str(datetime.utcnow()).split(" "))
    if Tag.query.filter(Tag.slug == tag.slug).count() > 0:
        new = False
    if new:
        print("Created tag %s"%tag.slug)
        db.session.add(tag)
    else:
        print("Updated Tag %s"%tag.slug)
    response = jsonify(tag.to_deliverable())
    db.session.commit()
    return response

@app.route('/api/fb', methods=['POST'])
def process_facebook_data():
    data = request.get_json()
    print(data)
    resp = Response("ok", status=200, mimetype='application/json')
    return resp


@app.route('/api/labels', methods=['POST'])
def get_labels():
    data = request.get_json() or {}
    (account_id, person_id) = get_account_and_person(data['token'])

    public_labels = Label.query.filter(and_(Label.publicity=="public",
                                            Label.type=="generic"))
    public_label_text = list(map(lambda label:label.text, public_labels))
    if person_id == -1:
        return jsonify(public_label_text)
    #find private labels
    private_useful_tags = Tag.query.filter(and_(Tag.originator == person_id,
                                            Tag.publicity == "private",
                                            ~Tag.type.contains("unique"),
                                            ~Tag.type.contains("metadata")))
    private_label_text = list(map(lambda tag: tag.text, private_useful_tags))
    labels_out = public_label_text+private_label_text
    # Special label logic
    special = {}
    normal = set([])
    for label in SPECIAL_LABELS.keys():
        special[label] = set([])
        if "person" in SPECIAL_LABELS[label]["types"]:
            special[label].add("person")
        normal.add(label+":")
    for label in labels_out:
        split_text = label.split(":")
        if (len(split_text) > 1 and len(split_text[1]) > 0) and split_text[0] in SPECIAL_LABELS and "person" not in SPECIAL_LABELS[split_text[0]]["types"]:
          special[split_text[0]].add(split_text[1])
        else:
          normal.add(label)
    structured_labels_out = {"normal":list(normal), "special":{}}
    for key in special:
        structured_labels_out["special"][key] = list(special[key])
    return jsonify(structured_labels_out)


@app.route('/api/login', methods=['POST'])
def login():
    print("login triggered")
    data = request.get_json() or {}
    (account_id, person_id) = get_account_and_person(data['token'])
    print("account id %d, person_id %d"%(account_id, person_id))
    new_account = False
    if account_id is -1:
        print("Creating new account")
        (account_id, person_id) = create_account_and_person(data['token'])
        new_account = True
    if person_id is None or person_id is -1:
        print ("Account %d does not have person. Creating one."%account_id)
        person_id = associate_account_with_person(account_id)
    print("got account %d and person %d"%(account_id, person_id))
    person = Person.query.filter(Person.id == person_id)[0]
    account = Account.query.filter(Account.id == account_id)[0]
    return jsonify({'person':person.to_deliverable(),
                    'account':account.to_deliverable(),
                    'new_account':new_account})


@app.route('/api/known_tags', methods=['POST'])
def find_known_tags():
    data = request.get_json() or {}
    (account_id, person_id) = get_account_and_person(data['token'])
    user_tags = Tag.query.filter(or_(Tag.originator==person_id,
        Tag.publicity=='public')).all()
    filtered_tags = []
    # This is an absurd hack - need to change how this works
    for tag in user_tags:
        if "metadata" not in decode_tag_types(tag.type):
            filtered_tags.append(tag)
    tags = list(map(lambda tag: tag.to_deliverable(), filtered_tags))
    return jsonify(tags)

@app.route('/api/mail', methods=['POST'])
def process_mail():
    print(request.form.get("from"))
    print(request.form.get("subject"))
    print(request.form.get("body-plain"))
    resp = Response("ok", status=200, mimetype='application/json')
    return resp


@app.route('/api/feedback', methods=['POST'])
def get_feedback():
    data = request.get_json() or {}
    (account_id, person_id) = get_account_and_person(data['token'])
    feedback = data['feedback']
    result = requests.post("https://api.mailgun.net/v3/%s/messages"%app.config['MAILGUN_DOMAIN_NAME'],
            auth=("api", app.config['MAILGUN_API_KEY']),
            data={"from": "FriendForce <mailgun@%s>"%app.config['MAILGUN_DOMAIN_NAME'],
                  "to": ["bzreinhardt@gmail.com"],
                  "subject": "Friendforce Feedback",
                   "text": "Feedback from account %d:\n%s"%(account_id, feedback)})
    return("feedback received. thanks!")

@app.route('/api/known_persons', methods=['POST'])
def find_known_persons():
    data = request.get_json() or {}
    (account_id, person_id) = get_account_and_person(data['token'])
    persons = []
    if account_id > 0:
        #user_tags = Tag.query.filter(Tag.originator==person_id).all()
        #ids = set(map(lambda tag:tag.subject, user_tags))
        #ids.add(person_id) # make sure people know about themselves
        persons = list(map(lambda person:person.to_deliverable(), Person.query.all()))
    response = jsonify(persons)
    return response


@app.route('/api/show_all_persons')
def show_all_persons():
    q = Person.query.all()
    persons = list(map(lambda person: person.json(), q))
    return jsonify(persons)

@app.route('/api/show_all_tags')
def show_all_tags():
    q = Tag.query.all()
    tags = list(map(lambda tag: tag.json(), q))
    return jsonify(tags)

@app.route('/api/show_all_labels')
def show_all_labels():
    q = Label.query.all()
    labels = list(map(lambda label: label.json(), q))
    return jsonify(labels)

@app.route('/api/delete_all_labels', methods=['GET', 'POST'])
def delete_all_labels():
    tags = Tag.query.all()
    for tag in tags:
        tag.label = None
        db.session.add(tag)
    db.session.commit()
    labels = Label.query.all()
    for label in labels:
        Label.query.filter(Label.id==label.id).delete()

    db.session.commit()
    return "All labels deleted"


@app.route('/api/update_db', methods=['GET','POST'])
def update_db():
    # TODO: change privacy levels on tags
    # TODO: make label slugs
    # TODO: upper label text
    # TODO: connect tags to labels
    '''
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
    '''
    generic_tags = Tag.query.filter(Tag.type != "metadata")
    for tag in generic_tags:
        tag.type = find_tag_type(tag.text)
        tag.text = condition_label_text(tag.text)
        if tag.subject == None:
            tag.subject = Person.query.filter(Person.slug==tag.subject_slug)[0].id
        if tag.label == None:
            tag.text = tag.text.title()
            labels = create_labels_from_tag(tag)
            if len(labels) > 0:
                tag.label = labels[0]
        db.session.add(tag)
    db.session.commit()

    response = jsonify('db updated!')
    return response




@app.route('/upload_firebase')
def upload_firebase():
    with open(app.config['FIREBASE_DUMP']) as f:
        firebase = json.loads(f.read())

    for (person_id, person) in firebase['persons']['data'].items():
        if 'name' not in person:
            continue
        new_person = Person()
        new_person.first_name = person['name'].split(' ')[0].title()
        if len(person['name'].split(' ')) > 1:
            new_person.last_name = ' '.join(person['name'].split(' ')[1:]).title()
        else:
            new_person.last_name = ' '
        new_person.name = person['name']
        new_person.slug = new_person.create_slug()
        #if new_person.first_name == "David":
        #    pdb.set_trace()
        if Person.query.filter(Person.first_name==new_person.first_name,
            Person.last_name==new_person.last_name).count() is 0:
            print ("adding person %s"%new_person.slug)
            db.session.add(new_person)
            new_tag = Tag()
            new_tag = new_tag.initialize("Created from firebase", new_person.id,
                new_person.id, subject_slug=new_person.slug, originator_slug=new_person.slug, type="metadata", publicity="private")
            db.session.add(new_tag)
            firebase['persons']['data'][person_id]['id'] = new_person.id
            firebase['persons']['data'][person_id]['slug'] = new_person.slug
        else:
            firebase['persons']['data'][person_id]['id'] = Person.query.filter(Person.first_name==new_person.first_name,
                Person.last_name==new_person.last_name)[0].id
            firebase['persons']['data'][person_id]['slug'] = Person.query.filter(Person.first_name==new_person.first_name,
                Person.last_name==new_person.last_name)[0].slug
    for (tag_id, tag) in firebase['tags']['data'].items():
         if 'subject' not in tag or tag['subject'] in ['Climbing_Person7','Climbing_person8', '0','1','2', '3']:
             continue
         if tag['subject'] == 'Rachel_Zucker3':
             tag['subject'] = 'Rachel_Zucker1'
         if tag['subject'] == 'Seth_Berman16':
             tag['subject'] = 'Seth_Berman10'
         if tag['subject'] == 'Natalie_Dillon_14':
             tag['subject'] = 'Natalie_Dillon11'
         if tag['subject'] == 'Sasha_Sheng':
             tag['subject'] = 'Sasha_Sheng12'
         if tag['subject'] == 'Adrienne_Tran':
             tag['subject'] = 'Adrienne_Tran0'
         if tag['subject'] == 'Micah_Catlin':
             tag['subject'] = 'Micah_Catlin14'
         if tag['subject'] == 'Leo_Polovets9':
             tag['subject'] = 'Leo_Polovets2'
         new_tag = Tag()
         publicity = tag['publicity']
         type = find_tag_type(tag['label'])
         originator_id = Person.query.filter(Person.first_name=="Benjamin",
                                             Person.last_name=="Reinhardt")[0].id

         subject_id = firebase['persons']['data'][tag['subject']]['id']
         subject_slug = firebase['persons']['data'][tag['subject']]['slug']
         new_tag = new_tag.initialize(tag['label'], originator_id, subject_id, subject_slug=subject_slug, publicity=publicity, type=type)
         print(new_tag.to_deliverable())
         if publicity == "public" and "metadata" not in decode_tag_types(type) and Label.query.filter(Label.text==tag['label']).count() == 0:
             print("Creating new label %s" %tag['label'])
             new_label = Label()
             new_label.text = tag['label']
             db.session.add(new_label)
             new_tag.label = new_label.id
         if Tag.query.filter(Tag.slug==new_tag.slug).count() == 0:
             print("adding tag %s"%new_tag.slug)
             db.session.add(new_tag)
         else:
             slug = Tag.query.filter(Tag.slug==new_tag.slug)[0].slug
             print("tag %s already exists"%slug)

    db.session.commit()

    return jsonify(firebase)
