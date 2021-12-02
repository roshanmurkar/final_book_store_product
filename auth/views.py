import datetime
import json
from builtins import print
import pandas as pd
import jwt
import re
import pyotp
from flask import jsonify, request
from flask_mail import *
from auth.exceptions import *
from auth.app import app, mail
from auth.models import *
import logging
from io import TextIOWrapper
from tabulate import tabulate

logging.basicConfig(filename="bookstore_otp.log", filemode="w", datefmt='%Y-%m-%d,%H:%M:%S:%f')
log = logging.getLogger()

# registration= Blueprint("registration",__name__)
with open('config.json', 'r') as f:
    params = json.load(f)['host_mail']



@app.route('/registration', methods=['POST'])
def register():
    """
    This function will take all require fields for user registration
    :return: Status of User Registration
    """
    user_data = request.get_json()
    user_name = user_data['user_name']
    first_name = user_data['first_name']
    last_name = user_data['last_name']
    contact_number = user_data['contact_number']
    password = user_data['password']
    email_address = user_data['email_address']

    try:
        special_symbol = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
        email_pattern = re.compile('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        if len(user_name) == 0 or len(first_name) == 0 or len(last_name) == 0 or \
                len(contact_number) == 0 or len(password) == 0 or len(email_address) == 0:
            raise EmptyData
        elif not contact_number.isnumeric():
            raise InvalidNumericData
        elif first_name.isdigit() or last_name.isdigit():
            raise InvalidStringData
        elif not special_symbol.search(first_name) is None or not special_symbol.search(last_name) is None:
            raise SpecialCharacterError
        elif email_pattern.search(email_address) is None:
            raise InvalidEmailAddress
        user = InfoModel.query.filter_by(user_name=user_data['user_name']).first()
        if user is None:
            new_user = InfoModel(user_name, first_name, last_name, contact_number, password, email_address)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"message": "New User registration successful", "data": user_data})
        else:
            return jsonify({"message": "UserName is already Registered", "Data": user_data})
    except EmptyData:
        return jsonify({"message": "Empty data is not allowed", "Data": user_data})
    except InvalidNumericData:
        return jsonify({"message": "Contact number should be in numeric", "Data": contact_number})
    except InvalidStringData:
        return jsonify({"message": "FirstName and LastName should be in String", "Data": user_data})
    except SpecialCharacterError:
        return jsonify({"message": "Don't use Special letters in FirstName and LastName", "Data": user_data})
    except InvalidEmailAddress:
        return jsonify({"message": "Invalid Email address", "Data": email_address})
    except Exception as e:
        return jsonify({"message": str(e)})



@app.route('/verify', methods=['POST', 'GET'])
def verify():
    """
    This function will take user email as a input for email verification
    and after that it will send OTP to that email address for validation purpose
    :return: It will send message and Email of user
    """
    email = request.get_json()
    try:
        if len(email['email']) == 0:
            raise EmptyData
        user = InfoModel.query.filter_by(email_address=email['email']).first()
        if user.is_verified == 'YES':
            return jsonify({"message": "This User mail is already verified", "Data": email})

        otp = pyotp.TOTP('base32secret3232')
        system_otp = otp.now()
        print(system_otp)
        time.sleep(1)
        log.warning(f"{system_otp} OTP is created for user {user.user_name} with {user.email_address} "
                    f"email address at {datetime.datetime.now()}")
        user.otp = system_otp
        db.session.commit()
        message = Message('OTP for verification', sender=params['gmail_user'], recipients=[email['email']])
        message.body = f"Enter this - {str(system_otp)} - OTP for your EMAIL verification ! THANK YOU :)"
        mail.send(message)
        return jsonify({"message": "OTP is send on given mail address", "data": email})
    except EmptyData:
        return jsonify({"message": "Empty data is not allowed", "Data": email})
    except Exception as e:
        return jsonify({"message": str(e)})


@app.route('/verify/validate', methods=['POST'])
def validate():
    """
    This function will take user email and verification OTP as a input
    and then it will match user OTP and system OTP if the match is found
    then it will return verified email address with user id token
    :return: whether the email is verified por not if the email is verified
            then it send user token also.
    """
    user_data = request.get_json()
    try:
        if len(user_data['otp']) != 6:
            raise InvalidSize
        elif not user_data['otp'].isnumeric():
            raise InvalidNumericData
        user = InfoModel.query.filter_by(email_address=user_data['email']).first()
        if user.otp == int(user_data['otp']):
            # user = InfoModel.query.filter_by(emailaddress=user_data['email']).first()
            user.is_verified = 'YES'
            user.otp = 0
            db.session.commit()
            encoded_jwt = jwt.encode({"user_id": user.user_id}, "secret", algorithm="HS256")
            return jsonify({"message": "Email verification successfully", "token": encoded_jwt})
        return jsonify({"message": "Due to Invalid OTP , Email verification is unsuccessful"})
    except InvalidSize:
        return jsonify({"message": "OTP size is Invalid", "Data": user_data})
    except InvalidNumericData:
        return jsonify({"message": "OTP should be in numeric", "Data": user_data})
    except Exception as e:
        return jsonify({"message": str(e)})

@app.route('/login', methods=['POST'])
def login():
    """
    This function will take username and password as a input from user
    and it will compare with database all entries
    if the match is found then it will return login successful or unsuccessful
    :return: message of login successful or unsuccessful with user data
    """
    user_data = request.get_json()
    try:
        if len(user_data['user_name']) == 0 or len(user_data['password']) == 0:
            raise EmptyData
        user = InfoModel.query.filter_by(user_name=user_data['user_name'],
                                            password=user_data['password']).first()
        if user.is_verified == 'YES':
            if user.password == str(user_data['password']):
                encoded_jwt = jwt.encode({"user_id": user.user_id}, "secret", algorithm="HS256")
                return jsonify({"message": f"User Login Successful... Welcome {user.user_name}", "token": encoded_jwt})
        else:
            return jsonify({"message": "User Email is Not Verified", "Data": user.email_address})
    except EmptyData:
        return jsonify({"message": "Empty data is not allowed", "Data": user_data})
    except Exception as e:
        return jsonify({"message": str(e)})


@app.route('/add_books', methods=['POST'])
def add_books():
    try:
        request_data = request.get_json()
        if request_data['author_name'].isnumeric or request_data['title'].isnumeric:
            raise InvalidStringData
        book = BookProduct.query.filter_by(author=request_data['author_name'], title=request_data['title']).first()
        if book is not None:
            book.quantity = int(book.quantity) + int(request_data['quantity'])
            db.session.commit()
            return jsonify({"message": "Book Quantity is updated"})

        new_book = BookProduct(request_data['author_name'], request_data['title'], request_data['baseprice'],
                               request_data['description'], request_data['quantity'])
        db.session.add(new_book)
        db.session.commit()
        return jsonify({"message": "New book is added."})

    except InvalidStringData:
        log.warning("Invalid String data")
        return jsonify({"message": "Invalid Data"})
    except Exception as e:
        log.warning(e.__str__())
        return jsonify({"message": "Something is wrong"})
    

@app.route('/books', methods=['GET'])
def details():
    try:
        book_product = BookProduct.query.all()
        book_product_schema = BookProductSchema(many=True)
        output = book_product_schema.dump(book_product)
        return jsonify({"message": "All Books Details", "details": output})
    except Exception as e:
        log.warning(e.__str__())
        return jsonify({"message": "Something is wrong"})


if __name__ == '__main__':
    app.run(debug=True)
