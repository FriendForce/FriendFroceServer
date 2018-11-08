from app.special_labels import SPECIAL_LABELS
from app.models import Tag, Label, Person, Account
from app import app, db
import boto3, urllib.request, os, io, pdb



def condition_label_text(text):
    chunks = text.split(":")
    for i, chunk in enumerate(chunks):
        chunks[i] = chunk.strip().title()
    return ":".join(chunks)

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

    if tag_pre in map(lambda label:"".join(label.lower().split(" ")), SPECIAL_LABELS):
        tag_types.add("special")
    #Other Special Things
    if tag_pre == "datemetfb":
        tag_types.add("metadata")
    if tag_pre == "loc":
        tag_types.add("location")
    if tag_pre == "lookingfor" or tag_pre == "lookingfor":
        tag_types.add("seeking")
    if tag_pre == "has":
        tag_types.add("has")
    if tag_pre.find("met") >= 0:
        tag_types.add("meeting")
    if tag_pre.find("date")  >= 0:
        tag_types.add("date")
    if tag_pre.find("via")  >= 0:
        tag_types.add("how_known")
        tag_types.add("personal")
    if tag_pre.find("email") >= 0:
        tag_types.add("contact_info")
        tag_types.add("email")
        tag_types.add("unique")
    if tag_pre == "todo":
        tag_types.add("todo")
        tag_types.add("personal")
    if tag_pre == "nickname":
        tag_types.add("alias")
        tag_types.add("unique")
    if tag_pre == "alias":
        tag_types.add("alias")
        tag_types.add("unique")
    if tag_pre == "website":
        tag_types.add("website")
        tag_types.add("unique")
    if tag_pre == "relationship":
        tag_types.add("relationship")
        tag_types.add("personal")
    if tag_pre == "marriedto":
        tag_types.add("relationship")
        tag_types.add("unique")
    if tag_pre == "engagedto":
        tag_types.add("relationship")
        tag_types.add("unique")
    if tag_pre == "talkabout":
        tag_types.add("relationship")
        tag_types.add("personal")
    #TODO: if you detect an email or phone number in the thing, label it
    # Maybe do this on the front end
    #TODO: detect websites and automatically label it.
    # User verification is important!
    return encode_tag_types(tag_types)

def create_labels_from_text(text, publicity="public"):
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
    if  len(split_text) is 2 and len(split_text[1]) > 0 and split_text[0] in SPECIAL_LABELS:
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

#TODO Create Person
def create_person(first_name, last_name, full_name, originator_id, photo_url=''):
    matching_persons = Person.query.filter(Person.name==full_name)
        #assume we found a dumplicate person
    if matching_persons.count() > 0:
        #pdb.set_trace()
        person = matching_persons[0]
        tag = Tag()
        tag.initialize('possible duplicate', originator_id, person.id, type="metadata", publicity="private")
        if Tag.query.filter(Tag.slug==tag.slug).count() == 0:
            db.session.add(tag)
        if photo_url and not person.photo_url:
            person.photo_url = photo_url
            db.session.add(person)
        print("creating a tag to mark %s as a possible duplicate"%person.slug);
    else:
        person = Person()
        person.name = full_name
        person.first_name = first_name
        person.last_name = last_name
        person.slug = person.create_slug()
        db.session.add(person)
        tag = Tag()
        tag.initialize('added', originator_id, person.id, subject_slug=person.slug, type="metadata", publicity="private")
        db.session.add(tag)
        print("adding person %s"%person.slug)
    db.session.commit()
    return person

def update_tag(tag_id, text, publicity="public", types=[]):
    tag = Tag.query.filter(Tag.id==tag_id)[0]
    tag.text = condition_label_text(text)
    tag.type = find_tag_type(text)
    for type in types:
        tag.type = ','.join([tag.type, type])
    tag.publicity = publicity
    tag = do_tag_logic(tag)
    labels = create_labels_from_tag(tag)
    if len(labels) > 0:
        #TODO: Return the label in the response as well.
        tag.label = labels[0]

    tag.slug = tag.create_slug()
    db.session.add(tag)
    db.session.commit()
    return tag_id

def create_tag(originator_id, subject_id, text, publicity="public", types=[]):
    #should check if tag exists
    tag = Tag()
    tag.originator = originator_id
    tag.originator_slug = Person.query.filter(Person.id==originator_id)[0].slug
    tag.subject = subject_id
    tag.subject_slug = Person.query.filter(Person.id==subject_id)[0].slug
    tag.text = condition_label_text(text)
    tag.type = find_tag_type(text)
    for type in types:
        tag.type = ','.join([tag.type, type])
    tag.publicity = publicity
    tag = do_tag_logic(tag)
    labels = create_labels_from_tag(tag)
    if len(labels) > 0:
        #TODO: Return the label in the response as well.
        tag.label = labels[0]

    tag.slug = tag.create_slug()
    # check if tag exists
    existing_tags = Tag.query.filter(Tag.slug==tag.slug)
    if existing_tags.count() > 0:
        print("updating tag %s"%tag.slug)
        return update_tag(existing_tags[0].id, text, publicity=publicity)
    else:
        print("creating new tag %s"%tag.slug)
        db.session.add(tag)
        db.session.commit()
        return tag.id


def upload(url, name='', sub_folder=''):
    try:
        s3 = boto3.client(
           "s3",
           aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
           aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )
        bucket_name = os.environ.get('AWS_BUCKET_NAME')

        file_object = urllib.request.urlopen(url)           # 'Like' a file object

        fp = io.BytesIO(file_object.read())
        #with open('/tmp/%s'%name, 'rw') as f:
        #    f.write(file_object)   # Wrap object
        if not name:
            name = url.split('/')[::-1][0]
        #pdb.set_trace()

        if sub_folder:
            s3_location = '/'.join(['https://s3-us-west-1.amazonaws.com',bucket_name,sub_folder])
            s3_target = '/'.join([sub_folder,name])
        else:
            s3_location = '/'.join(['https://s3-us-west-1.amazonaws.com',bucket_name])
            s3_target = name
        s3.upload_fileobj(
            fp,
            bucket_name,
            s3_target,
            ExtraArgs={'ACL': 'public-read',
                       'ContentType':'image'}
        )

        return "{}/{}".format(s3_location, name.replace(" ", "+"))
    except Exception as error:
        return error

def parse_fb_person(fb_person, creating_account_id):
    if fb_person['type'] != 'user':
        create_tag(creating_account_id, creating_account_id, fb_person['text'])
        print("note a person: ")
        print(fb_person)
        return None
    # Try to find Person
    #pdb.set_trace()
    photo = fb_person['photo']
    #If the photo is legit, add it to the person
    photo_name = photo.split('?')[0].split('/')[::-1][0]
    photo_url = upload(photo, name=photo_name, sub_folder='profile_photos')
    person = create_person(fb_person['firstname'],fb_person['lastname'],fb_person['text'], creating_account_id, photo_url=photo_url)
    #create a uid tag
    fb_uid = fb_person['uid']
    create_tag(person.id, person.id, 'fb_uid', publicity='private', types=['unique', 'metadata'])
    create_tag(creating_account_id, person.id, 'Added from facebook', types=['metadata'])
    #Ideally should process these
    if 'non_title_tokens' in fb_person:
        fb_non_title_tokens = fb_person['non_title_tokens']
        create_tag(person.id, person.id, 'fb_non_title_tokens:%s'%fb_non_title_tokens, publicity='private', types=['metadata'])
        create_tag(person.id, person.id, fb_non_title_tokens, types=['uncertain'])
    return person.id
