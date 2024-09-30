
# shebang line that tells OS to run script using the Python interpreter located at flask/bin/python
# !flask/bin/python       

# imports sys and os to access variables used or maintained by Python interpretor
import sys, os

# allows to import modules from utils directory by appending it to Python path
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))

# import the variables from env module (AWS creds and the S3 bucket configurable and dynamodb table details)
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION, PHOTOGALLERY_S3_BUCKET_NAME, DYNAMODB_TABLE

# flask is a web framework for Python, and these modules and functions can be used to create web applications
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect

# Python modules, working with time, reading EXIF data from images, working with JSON data, generating UUIDs, and interacting with AWS services using the Boto3 library.
import time
import exifread
import json   #data interchange format, transmit data between server and web application
import uuid   #generate unique username? 
import boto3  #interacting with the AWS services

# imports used to construct conditions to query dynamodb tables
from boto3.dynamodb.conditions import Key, Attr

# cursor objects to interact with MySQL databased in the python library 
import pymysql.cursors

# used to work with dates, times, and time zones in Python
from datetime import datetime
import pytz

"""
    INSERT NEW LIBRARIES HERE (IF NEEDED)
"""

import bcrypt
from itsdangerous import URLSafeTimedSerializer

from botocore.exceptions import ClientError

from flask import Flask, session, redirect, url_for, request
from datetime import timedelta



secret_key = 'SECRETKEY'
secret_salt = 'SECRETSALT'


#password encrypt
def password_encrypt(password):
    salt = bcrypt.gensalt()
    encrypted = bcrypt.hashpw(password = password.encode("utf-8"), salt = salt)
    return encrypted

# create a uuid and a confirmation token 
def generate_token(email):
    serializer = URLSafeTimedSerializer(secret_key)
    token = serializer.dumps(email, secret_salt)
    return token

# confirm the token
def confirm_token(token):
    try:
        serializer = URLSafeTimedSerializer(secret_key)
        email = serializer.loads(token, salt = secret_salt, max_age = 600)
        return email

    except Exception as e:
        return False   
    

name = "Mythri Muralikannan"
email = "mmuralikannan3@gatech.edu"
password = "ABC"

token = generate_token(email)

        
        
link = "http://ec2-3-84-224-151.compute-1.amazonaws.com:5000/confirm_email?token=abc123"
sender = 'mythri.muralikannan@gmail.com'


# create ses resource to send emails
ses = boto3.client('ses',
                   region_name = AWS_REGION,
                   aws_access_key_id = AWS_ACCESS_KEY,
                   aws_secret_access_key = AWS_SECRET_ACCESS_KEY)


try: 
    response = ses.send_email(
        Destination={
            'ToAddresses': [email],
        },
        Message={
            'Body': {
                'Text': {
                    'Data': 'Confirm email id to create account: \n' + link,
                },
            },
            'Subject': {
                'Data': 'Confirm email'
            },
        },
        Source=sender
    ) 

except ClientError as e:
    print(e.response['Error']['Message'])  
