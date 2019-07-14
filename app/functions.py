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
# need to split out into fuzzy search for person
# need to start making first and last name primary objects
# need to create fuzzy-match function
def create_person(first_name, last_name, full_name, originator_id, photo_url=''):
    matching_persons = Person.query.filter(Person.name==full_name)
        #assume we found a dumplicate person
    if matching_persons.count() > 0:
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
        db.session.commit()
        tag = Tag()
        tag.initialize('added', originator_id, person.id, subject_slug=person.slug, type="metadata", publicity="private")
        db.session.add(tag)
        db.session.commit()
        print("adding person %s"%person.slug)
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

def parse_linkedin_location(location_string):
    '''
    Parses a location string from linkedin
    '''
    return "loc:" + location_string

def parse_linkedin_separation(separation_string):
    '''
    Parses a separation string from linkedin
    '''
    separation_degrees = 0
    if separation_string is '1st':
        separation_degrees = 1
    if separation_string is '2nd':
        separation_degrees = 2
    if separation_string is '3rd':
        separation_degrees = 3
    return separation_degrees

def parse_linkedin_image(image_string):
    '''
    Parses a image string from linkedin
    '''
    if len(image_string) > 0:
        return image_string.split("\"")[1]
    else:
        return ''

def parse_linkedin_education(education):
    '''
    Parses an education json object from LinkedIn into tags
    '''
    tags = []
    # Do you ever have an education without a school name?4
    if 'schoolName' in education:
        school = education['schoolName']
        tags.append({'label':school, 'publicity':'public', 'types':['school']})
    else:
        return []
    if 'degree' in education:
        degree_type = education['degree'].split("Degree Name")[1]
        publicity = 'private'
        if degree_type.lower() == 'phd' or degree_type.lower() == 'mba':
            publicity = 'public'
        tags.append({'label':degree_type, 'publicity':publicity, 'types':['degree']})
    if 'fieldOfStudy' in education:
        field_string = education['fieldOfStudy'].split("Field Of Study")[1]
        fields = field_string.split(",")
        for field in fields:
            tags.append({'label':field, 'publicity':'public', 'types':['discipline']})
    if 'extraDetails' in education:
        tags.append({'label':"Details about %s: %s"%(degree_type , education['extraDetails']), 'publicity':'private', 'types':['needs processing']})
    if 'dateRange' in education:
        tags.append({'label':"At %s from %s"%(school, education['dateRange']), 'publicity':'private', 'types':['date']})
    return tags

def parse_linkedin_experience(experience):
    '''
    Parses an education json object from LinkedIn into tags
    returns a list of objects to turn into tags with fields private
    and public
    '''
    tags = []
    if 'company' in experience:
        company = experience['company']
    else:
        return []
    current = False
    if experience['locationCurrent'] is True:
        current = True
        tags.append({'label':company, 'publicity':'public', 'types':[]})
    else:
        tags.append({'label':"ex-"+company, 'publicity':'public', 'types':[]})
        #TODO:add ex locations for experiences
    if 'title' in experience:
        tags.append({'label':experience['title'], 'publicity':'public', 'types':[]})
    if 'dateRange' in experience:
        tags.append({'label':"At %s from %s"%(company, experience['dateRange']), 'publicity':'private', 'types':['date']})

    return tags




def parse_linkedin_person(linkedin_person, creating_account_id):
    name = ''
    if 'name' in linkedin_person:
        # Do we need to do something fancier here?
        name = linkedin_person['name'].strip()
    else:
        #If there's not a name you can't do much else
        return 0
    image_url = ''
    if 'image' in linkedin_person:
        photo_url = parse_linkedin_image(linkedin_person['image'])
    person = create_person(name.split(" ")[0], " ".join(name.split(" ")[1:]), name, creating_account_id, photo_url=photo_url)
    if 'contactInfo' in linkedin_person:
        contact_info_tag_id = create_tag(creating_account_id, person.id, linkedin_person['contactInfo'], publicity="private", types=['metadata'])
    if 'location' in linkedin_person:
        loc = parse_linkedin_location(linkedin_person['location'])
        loc_tag_id = create_tag(creating_account_id, person.id, loc, publicity="public", types=['location'])
    if 'separation' in linkedin_person:
        separation = parse_linkedin_separation(linkedin_person['separation'])
        if separation > 1:
            sep_tag_id = create_tag(creating_account_id, person.id, 'connection degree:%d'%separation, publicity="private",types=['separation'])
    if 'education' in linkedin_person:
        for education in linkedin_person['education']:
            tags = parse_linkedin_education(education)
            for tag in tags:
                create_tag(creating_account_id, person.id, tag['label'],publicity=tag['publicity'],types=tag['types'])
    if 'experience' in linkedin_person:
        for experience in linkedin_person['experience']:
            tags = parse_linkedin_experience(experience)
            for tag in tags:
                create_tag(creating_account_id, person.id, tag['label'],publicity=tag['publicity'],types=tag['types'])
    return person.id


def parse_fb_person(fb_person, creating_account_id):
    if fb_person['type'] != 'user':
        create_tag(creating_account_id, creating_account_id, fb_person['text'])
        print("note a person: ")
        print(fb_person)
        return None
    # Try to find Person
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

def parse_from(from_string):
    name = from_string.split("<")[0]
    name = name.strip('\"')
    name = name.strip('From\:')
    name = name.strip()
    email_address = from_string.split("<")[1].split(">")[0]
    return name, email_address

def parse_email_tag_string(tag_string):
    tags = tag_string.split(";")
    tags = [tag.strip() for tag in tags]
    return tags

def parse_forwarded_message(mailgun_body):
    email_lines = mailgun_body.split("\n")
    forwarded_email_indices = [i for i, s in enumerate(email_lines) if 'orwarded' in s]
    from_name = None
    from_email = None
    tags = []
    if len(forwarded_email_indices) > 0:
        forwarded_email_index = forward_email_indices[0]
        #for now only do first forwarded email
        from_name, from_email = parse_from(email_lines[forwarded_email_index+1])
        tags = parse_email_tag_string(email_lines[0])
    return from_name, from_email, tags


def parse_mailgun_email(mailgun_from, mailgun_subject, mailgun_body):
    print("got email from mailgun")
    print(mailgun_from)
    print(mailgun_subject)
    print(mailgun_body)
    name, email = parse_from(mailgun_from)
    from_name, from_email, tags = parse_forwarded_message(mailgun_body)
    if not from_name:
        return "Email not forwarded"
    # Want to save the email for posterity
    # Find user who sent email
    account = Account.query.filter(Account.email==email)
    if account.count() is not 1:
        return "Account not found"
    person = create_person(from_name.split(" ")[0], from_name.split(" ")[-1], from_name, account[0].id)
    create_tag(account[0].id, person.id, "email:"+from_email)
    for tag in tags:
        create_tag(account[0].id, person.id, tag)
    # Find person who is referred to
    return None
