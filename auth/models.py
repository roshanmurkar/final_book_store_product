from email.policy import default

from flask_sqlalchemy import SQLAlchemy
from auth.app import app
from flask_marshmallow import Marshmallow
import datetime
from sqlalchemy import Column, Integer, DateTime

db = SQLAlchemy(app)
ma = Marshmallow(app)
class InfoModel(db.Model):
    __tablename__ = 'registration'

    user_id = db.Column(db.Integer, primary_key=True)
    user_name= db.Column(db.String())
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    contact_number = db.Column(db.String())
    password = db.Column(db.String())
    email_address = db.Column(db.String())
    is_verified = db.Column(db.String())
    otp = db.Column(db.Integer)


    def __init__(self, user_name,first_name,last_name,contact_number,password,email_address):
        self.user_name = user_name
        self.first_name = first_name
        self.last_name = last_name
        self.contact_number = contact_number
        self.password = password
        self.email_address = email_address

    def __repr__(self):
        return f"{self.user_name}:{self.first_name}:{self.last_name}:{self.contact_number}:{self.password}:{self.email_address}"

class BookProduct(db.Model):
    __tablename__ = 'product'

    product_id = db.Column(db.Integer, primary_key=True)
    author= db.Column(db.String())
    title = db.Column(db.String())
    baseprice = db.Column(db.Integer())
    description = db.Column(db.String())
    quantity = db.Column(db.Integer)

    def __init__(self, author,title,baseprice,description,quantity):
        self.author = author
        self.title = title
        self.baseprice = baseprice
        self.description = description
        self.quantity =quantity

    def __repr__(self):
        return f"{self.author}:{self.title}:{self.baseprice}:{self.description}:{self.quantity}"

class BookProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = BookProduct
        load_instance = True