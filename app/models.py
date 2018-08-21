from datetime import datetime
from app import db


class BaseModel(db.Model):
    """Base data model for all objects"""
    __abstract__ = True

    def __repr__(self):
        """Define a base way to print models"""
        return '%s(%s)' % (self.__class__.__name__, {
            column: value
            for column, value in self.__dict__.items()
        })

    def json(self):
        """
                Define a base way to jsonify models, dealing with datetime objects
        """
        return {
            column: value if not isinstance(value, datetime.date) else value.strftime('%Y-%m-%d')
            for column, value in self._to_dict().items()
        }

#Work from here

class Person(BaseModel, db.Model):
    __tablename__ = 'person'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    slug = db.Column(db.String())
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    created = db.Column(db.DateTime(), default=datetime.utcnow)
    updated = db.Column(db.DateTime(), default=datetime.utcnow)
    is_user = db.Column(db.Boolean(), default=False)


class Tag(BaseModel, db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String())
    text = db.Column(db.String())
    originator = db.Column(db.Integer, db.ForeignKey('person.id'))
    subject = db.Column(db.Integer, db.ForeignKey('person.id'))
    type = db.Column(db.String())
    publicity = db.Column(db.String())
    created = db.Column(db.DateTime(), default=datetime.utcnow)
    updated = db.Column(db.DateTime(), default=datetime.utcnow)

class Label(BaseModel, db.Model):
    __tablename__ = 'label'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String())
    text = db.Column(db.String())
