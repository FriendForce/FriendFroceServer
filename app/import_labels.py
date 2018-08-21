import json 
from models import Label
from app import db

def import_labels(filename):
  with open(filename) as f:
    all_labels = json.loads(f.read())
  labels = all_labels["labels"]
  for name, value in labels.items():
    label = Label(value["label"], name)
    db.session.add(label)
  db.session.commit()

