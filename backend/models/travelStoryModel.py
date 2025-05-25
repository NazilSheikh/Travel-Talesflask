from mongoengine import Document, StringField, BooleanField, ListField, ReferenceField, DateTimeField, ObjectIdField
from datetime import datetime

class Travelstory(Document):
    title = StringField(required=True)
    story = StringField(required=True)
    visitedLocation = ListField(StringField(), default=[])
    isFavorite = BooleanField(default=False)
    userid = ObjectIdField(required=True)  # you can also use ReferenceField('User') if you want references
    createdOn = DateTimeField(default=datetime.utcnow)
    imageUrl = StringField(required=True)
    visitedDate = DateTimeField(required=True)
    name = StringField(required=True)
    email = StringField(required=True)
