from datetime import datetime
from app import db
from flask_login import UserMixin


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

class Account(BaseModel, UserMixin, db.Model):
    __tablename__ = 'account'
    account_id = db.Column(db.Integer, primary_key=True)
    firebase_user_id = db.Column(db.String(), unique=True)
    email = db.Column(db.String(), unique=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    name = db.Column(db.String())
    photo_url = db.Column(db.String())
    person = db.Column(db.Integer, db.ForeignKey('person.id'))


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

    def to_deliverable(self):
        deliverable = {}
        deliverable['last_name'] = self.last_name
        deliverable['first_name'] = self.first_name
        deliverable['slug'] = self.slug
        return deliverable


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
    type = db.Column(db.String())
    publicity = db.Column(db.String())
    created = db.Column(db.DateTime(), default=datetime.utcnow)
    updated = db.Column(db.DateTime(), default=datetime.utcnow)
    label = db.Column(db.Integer, db.ForeignKey('label.id'))

    def to_deliverable(self):
        deliverable = {}
        deliverable['subject'] = self.subject_slug
        deliverable['originator'] = self.originator_slug
        deliverable['type'] = self.type
        deliverable['text'] = self.text
        deliverable['slug'] = self.slug
        return deliverable


class Label(BaseModel, db.Model):
    __tablename__ = 'label'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(), unique=True)
    text = db.Column(db.String(), unique=True)
