from app.special_labels import SPECIAL_LABELS
from app.models import Tag, Label, Person, Account
from app import app, db



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
    if  len(split_text) is 2 and len(split_text[1]) > 0 and split_text[0] in SPECIAL_LABELS:
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
