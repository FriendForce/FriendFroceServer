from datetime import datetime
from app import db
from flask_login import UserMixin
import slugify
import random


class BaseModel(db.Model):
    """Base data model for all objects"""
    __abstract__ = True

    def __repr__(self):
        """Define a base way to print models"""
        return '%s(%s)' % (self.__class__.__name__, {
            column: value
            for column, value in self.__dict__.items() if column is not '_sa_instance_state'
        })

    def json(self):
        """
                Define a base way to jsonify models, dealing with datetime objects
        """
        return {
            column: value
            for column, value in self.__dict__.items() if column is not '_sa_instance_state'
        }

#Work from here

class Account(BaseModel, db.Model):
    __tablename__ = 'account'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    firebase_user_id = db.Column(db.String(), unique=True)
    email = db.Column(db.String(), unique=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    name = db.Column(db.String())
    photo_url = db.Column(db.String())
    person = db.Column(db.Integer, db.ForeignKey('person.id'))
    created = db.Column(db.DateTime(), default=datetime.utcnow)
    updated = db.Column(db.DateTime(), default=datetime.utcnow)
    connected_facebook = db.Column(db.Boolean(), default=False)
    connected_gmail = db.Column(db.Boolean(), default=False)
    connected_linkedin = db.Column(db.Boolean(), default=False)

    def from_firebase_token(self, token):
        self.firebase_user_id = token['uid']
        self.email = token['email']
        self.email_verified = token['email_verified']
        self.name = token['name']
        self.photo_url = token['picture']
        self.updated = datetime.now()

    def add_person(self, person_id):
        self.person = person_id
        self.updated = datetime.now()

    def to_deliverable(self):
        deliverable = {}
        deliverable['name'] = self.name
        deliverable['connected_facebook'] = self.connected_facebook
        deliverable['connected_linkedin'] = self.connected_linkedin
        deliverable['connected_gmail'] = self.connected_gmail
        return deliverable



class Person(BaseModel, db.Model):
    __tablename__ = 'person'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    slug = db.Column(db.String(), unique=True)
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    created = db.Column(db.DateTime(), default=datetime.utcnow)
    updated = db.Column(db.DateTime(), default=datetime.utcnow)
    is_user = db.Column(db.Boolean(), default=False)
    photo_url = db.Column(db.String())

    def to_deliverable(self):
        deliverable = {}
        deliverable['last_name'] = self.last_name
        deliverable['first_name'] = self.first_name
        deliverable['slug'] = self.slug
        deliverable['photo_url'] = self.photo_url
        return deliverable

    def create_slug(self):
        pre_slug = "%s %s %d"%(self.first_name.lower(), self.last_name.lower(),random.randint(0,10000000))
        return slugify.slugify(pre_slug)


class Tag(BaseModel, db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.Text, unique=True)
    text = db.Column(db.String())
    originator = db.Column(db.Integer, db.ForeignKey('person.id'))
    subject = db.Column(db.Integer, db.ForeignKey('person.id'))
    # Should this be here - don't want to hit db when sending out info
    originator_slug = db.Column(db.String())
    subject_slug = db.Column(db.String())
    type = db.Column(db.String(), default="generic")
    publicity = db.Column(db.String(), default="public")
    created = db.Column(db.DateTime(), default=datetime.utcnow)
    updated = db.Column(db.DateTime(), default=datetime.utcnow)
    label = db.Column(db.Integer, db.ForeignKey('label.id'))

    def initialize(self, text, originator_id, subject_id, originator_slug=None, subject_slug=None, type="generic", publicity="public"):
        self.text = text
        self.originator = originator_id
        self.subject = subject_id
        if originator_slug is None:
            self.originator_slug = Person.query.filter(Person.id == originator_id)[0].slug
        else:
            self.originator_slug = originator_slug
        if subject_slug is None:
            self.subject_slug = Person.query.filter(Person.id == subject_id)[0].slug
        else:
            self.subject_slug = subject_slug
        self.type = type
        self.publicity = publicity
        self.slug = self.create_slug()
        return self

    def to_deliverable(self):
        deliverable = {}
        deliverable['subject'] = self.subject_slug
        deliverable['originator'] = self.originator_slug
        deliverable['type'] = self.type
        deliverable['text'] = self.text
        deliverable['slug'] = self.slug
        deliverable['publicity'] = self.publicity
        return deliverable

    def create_slug(self):
        return slugify.slugify("%s %s %s"%(self.originator_slug, self.subject_slug, self.text))


class Label(BaseModel, db.Model):
    __tablename__ = 'label'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(), unique=True)
    text = db.Column(db.String(), unique=True)
    publicity = db.Column(db.String(), default="public")
    type = db.Column(db.String(), default="generic")

    def set_text(self, text):
        self.text = text.title()
        self.slug = slugify.slugify(self.text.lower())
