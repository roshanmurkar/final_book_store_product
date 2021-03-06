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

@app.route('/add_book_in_cart', methods=['POST'])
def add_book_in_cart():
    try:
        # First decoding the token
        auth = request.headers.get('authorization')
        id = jwt.decode(auth, "secret", algorithms=["HS256"])
        print(id)
        user = InfoModel.query.filter_by(user_id=id['user_id']).first()
        # Taking book id and book quantity as a input
        request_data = request.get_json()
        # Finding user entered book is present or not in over product table
        book_details = BookProduct.query.filter_by(product_id=request_data['book_id']).first()
        if book_details is None:
            return jsonify({"message": f"No Book is present with book_id {request_data['book_id']}"})

        # checking cart is already created for that user.
        cart = Carts.query.filter_by(user_id=user.user_id, status='not ordered').first()
        print(cart, "cart")
        if cart is None:
            # If cart is not created it will create new cart for that user
            new_cart = Carts(user.user_id)
            db.session.add(new_cart)
            db.session.commit()
            print("cart created")

        cart = Carts.query.filter_by(user_id=user.user_id, status='not ordered').first()
        book_in_cart = CartItems.query.filter_by(cart_id=cart.cart_id, book_id=request_data['book_id']).first()
        print(book_in_cart)
        if book_in_cart is not None:
            book_in_cart.quantity = int(book_in_cart.quantity) + int(request_data['book_quantity'])
            db.session.commit()
            return jsonify({"message": "Book Quantity is updated"})

        # cart is already created so new book is add in existing cart.
        cart_book = CartItems(cart.cart_id, book_details.product_id, request_data['book_quantity'])
        db.session.add(cart_book)
        db.session.commit()
        return jsonify({"message": "Your book is added in your cart"})
    except Exception as e:
        return jsonify({"message": str(e)})

@app.route('/particular_cart_details', methods=['GET'])
def particular_cart_details_data():
    try:
        request_data = request.get_json()
        if not request_data['cart_id'].isnumeric:
            raise InvalidNumericData
        cart_data = CartItems.query.filter_by(cart_id=request_data['cart_id']).all()
        if cart_data is None:
            return jsonify({"message": "Cart is not found"})

        cart_item_schema = CartItemsSchema(many=True)
        json_data = cart_item_schema.dump(cart_data)
        # print(json_data)
        cart_details = []
        for data in json_data:
            book = BookProduct.query.join(CartItems).with_entities\
                (BookProduct.author, BookProduct.title,BookProduct.baseprice, CartItems.quantity).\
                filter_by(product_id=data['id']).first()
            book_product_schema = BookProductSchema()
            cart_details.append(book_product_schema.dump(book))
        # print(cart_details)
        return jsonify({"message": "successful", "data": cart_details})

    except InvalidNumericData:
        log.warning("Cart_id should be numeric data")
        return jsonify({"message": "Cart_id should be numeric data"})
    except Exception as e:
        log.warning(e.__str__())
        return jsonify({"message": "Something is wrong"})


@app.route('/buy_book',methods=['POST'])
def buy_book():
    try:
        print("a")
        auth = request.headers.get('authorization')
        id = jwt.decode(auth, "secret", algorithms=["HS256"])
        user = InfoModel.query.filter_by(user_id=id['user_id']).first()
        if user is None:
            raise InvalidToken

        request_data = request.get_json()
        cart_check = Carts.query.filter_by(cart_id=request_data['cart_id']).first()
        if cart_check is None:
            return jsonify({"message": "Cart is not found"})

        order = Orders(cart_check.user_id)
        db.session.add(order)
        db.session.commit()
        cart_check.status = 'Ordered'
        db.session.commit()
        order = Orders.query.filter_by(user_id=user.user_id, status='in queue').first()
        cart_books = CartItems.query.filter_by(cart_id=request_data['cart_id']).all()
        for book in cart_books:
            print("inside book in cart_books")
            order_items = OrderItems(order.order_id, book.book_id,book.quantity)
            db.session.add(order_items)
            db.session.commit()

        # order= Orders.query.filter_by(user_id=user.user_id, status='in queue').first()
        items = OrderItems.query.filter_by(order_id=order.order_id).all()
        order_items_list = []
        for order_item in items:
            data = BookProduct.query.join(OrderItems).with_entities(
                BookProduct.title,BookProduct.baseprice,OrderItems.quantity).filter_by(product_id=order_item.book_id).first()
            book_product_schema = BookProductSchema()
            order_items_list.append(book_product_schema.dump(data))

        order.status = 'confirm'
        db.session.commit()
        billing_list = []
        for entry in order_items_list:
            billing_list.append(entry['baseprice'] * entry['quantity'])

        total_bill = sum(billing_list)
        header = order_items_list[0].keys()
        rows = [x.values() for x in order_items_list]
        data_in_table_form = tabulate(rows, header, tablefmt='grid')
        user_email = user.email_address
        message = Message('Your Order', sender=params['gmail_user'], recipients=[user_email])
        message.body = f"your books order details are \n" \
                       f"{data_in_table_form} \n" \
                       f"and total bill is -> {total_bill}"
        mail.send(message)

        return jsonify({"message": "Ordered Successful. Please check mail for order details. Thank You :)","data":order_items_list})
    except InvalidToken:
        log.warning("Token is invalid")
        return jsonify({"message":"Token is invalid"})
    except Exception as e:
        log.warning(e.__str__())
        return jsonify({"message":"something is wrong"})



if __name__ == '__main__':
    app.run(debug=True)
