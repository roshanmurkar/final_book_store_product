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



if __name__ == '__main__':
    app.run(debug=True)
