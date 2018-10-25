import os
from flask_script import Manager, Command
from app.models import Tag, Label
from app import app, db
from app.functions import find_tag_type, condition_label_text, create_labels_from_tag




manager = Manager(app)

class Update(Command):
    def run(self):
        # TODO: change privacy levels on tags
        # TODO: make label slugs
        # TODO: upper label text
        # TODO: connect tags to labels
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

        print('db updated!')
        return 0

class LabelDeleter(Command):
    def run(self):
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


manager.add_command('update', Update())
manager.add_command('delete_labels',LabelDeleter())


if __name__ == '__main__':
    manager.run()
