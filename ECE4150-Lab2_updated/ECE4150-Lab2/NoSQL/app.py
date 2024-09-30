
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




"""
"""


# Sets up a Flask application instance to connect to a  dynamodb using boto3 library

# flask application instance name is current Python module, next is parameter to specify the URL prefix for static files
app = Flask(__name__, static_url_path="")
app.config['SESSION_TYPE']='filesystem'
app.config['PERMANENT_SESSION_LIFETIME']= timedelta(minutes = 5)

# creates a connection to the aws dynamodb service using boto3 library. 
# it initializes a dynamodb resource object and requires providing the security features imported from env
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)

# creates a dynamodb table using 'Table' class.
table = dynamodb.Table(DYNAMODB_TABLE)

# creates a dynamodb table using 'Table' class for the photogallery user
userTable = dynamodb.Table('PhotoGalleryUser')

# create ses resource to send emails
ses = boto3.client('ses',
                   region_name = AWS_REGION,
                   aws_access_key_id = AWS_ACCESS_KEY,
                   aws_secret_access_key = AWS_SECRET_ACCESS_KEY)


# defines variables used for upload handling in Flask application 
UPLOAD_FOLDER = os.path.join(app.root_path,'static','media')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

#session variables
app.secret_key = secret_key
app.permanent_session_lifetime = timedelta(minutes = 5)

#make the session work
@app.before_request
def before_request():
    session.permanent = True

# function to check if a filename has an allowed extension based on ALLOWED_EXTENTIONS (png, jpg, jpeg)
def allowed_file(filename):

    #checks if filename contains a dot (meaning it has an extension); \continues to next line;  
    #splits the filename at the last dot and extracts the extension part. [1] access the second part of the split and lower() to convert to lowercase 
    #returns true or false based on whether allowed 
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# reads an image file, extracts EXIF metadta, filters out irrelevant tags, returns dictionary with relevant EXIF data
def getExifData(path_name):
    f = open(path_name, 'rb') #open specified image in binary
    tags = exifread.process_file(f)  #extract tags
    ExifData={}
    for tag in tags.keys():
        if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'): #excludes all these taga
            key="%s"%(tag)
            val="%s"%(tags[tag])
            ExifData[key]=val
    return ExifData  #return EXIF data dictionary


# uploads file a s3 bucket
def s3uploading(filename, filenameWithPath, uploadType="photos"):

    #s3 client initialization with aws access key
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


    bucket = PHOTOGALLERY_S3_BUCKET_NAME   #name iported from env file
    path_filename = uploadType + "/" + filename  #photos folder

    #upload the file at the location
    s3.upload_file(filenameWithPath, bucket, path_filename)  
    s3.put_object_acl(ACL='public-read', Bucket=bucket, Key=path_filename)
    
    # returns the url where uploaded file can be accessed.
    return f'''http://{PHOTOGALLERY_S3_BUCKET_NAME}.s3.amazonaws.com/{path_filename}'''


"""
    INSERT YOUR NEW FUNCTION HERE (IF NEEDED)
"""


"""
"""

"""
    INSERT YOUR NEW ROUTE HERE (IF NEEDED)

"""

"""
# signup redirect
@app.route('/')
def signup_redirect():
    return redirect('/home')
"""





#redirect to signup page
@app.route('/')
def signup_redirect():
    return redirect('/signup')

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



#sign up method
@app.route("/signup", methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        token = generate_token(email)

        userTable.put_item(
            Item = {
                "email": email,
                "name": name,
                "password": password_encrypt(password),
                "uuid": token,
                "confirmed": "false"
            }
        )
        
        link = url_for('confirm_email', token = token, _external=True)

        sender = 'mythri.muralikannan@gmail.com'

        try: 

            reponse = ses.send_email (
                Destination = {
                    'ToAddresses': [email],
                },
                Message = {
                    'Body': {
                        'Text': {
                            'Data': 'Confirm email id to create account: \n' + link,
                        },
                    },
                    'Subject': {
                        'Data': 'Confirm email'
                    },
                },
                Source = sender
            )
            return redirect('/login')   #check


        except ClientError as e:
            
            print (e.response['Error']['Message'])  
            return redirect('/signup') 

    else:
        return render_template("signup.html")    
    
#confirm the email
@app.route("/confirm/<token>", methods = ['GET'])
def confirm_email(token):
    email = confirm_token(token)
    if (email) :
        userTable.update_item(
            Key = {
                "uuid": token
            },
                UpdateExpression='SET #confirmed = :confirmed',
                ExpressionAttributeNames = {'#confirmed' : 'confirmed'},
                ExpressionAttributeValues = {':confirmed' : "true"}
        )
        return redirect('/login')
    else:
        return redirect('/signup')


@app.route("/login", methods = ['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        response = userTable.scan(FilterExpression = Key('email').eq(email))
        results = response['Items']

        if results:
            if bcrypt.checkpw(password.encode("utf-8"), results[0]['password'].value) and results[0]['confirmed']:
                session['email'] = email
                session.permanent = True
                return redirect('/home')
        
        
        return render_template("login.html")
    else:
        return render_template("login.html")



# delete photo: from s3 and dynamodb
@app.route('/album/<string:albumID>/deletePhoto/<string:photoID>', methods=['GET', 'POST'])
def deletePhoto(albumID, photoID):
   
   response = table.query( KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq(photoID))
   results = response['Items']
   photoURL = results[0]['photoURL']


   # Check if there are items returned
   if results:
       
       #delete from s3
       s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
       bucket = PHOTOGALLERY_S3_BUCKET_NAME
       object_key = '/'.join(photoURL.split('/')[3:])
       s3.delete_object(Bucket=bucket, Key=object_key)
       
       #delete from dynamodb
       table.delete_item(
           Key = {
               "albumID": albumID,
               "photoID": photoID
            }
        )
       
   return redirect(f'''/album/{albumID}''') 



# delete album and all the photos in it
@app.route('/deleteAlbum/<string:albumID>', methods=['GET', 'POST'])
def deleteAlbum(albumID):
    response = table.query( KeyConditionExpression=Key('albumID').eq(albumID))
    results = response['Items']

    #delete from s3
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    bucket = PHOTOGALLERY_S3_BUCKET_NAME

    for i in results:

        if i.get('photoURL'):
            photoURL = i.get('photoURL')
            object_key = '/'.join(photoURL.split('/')[3:])
            s3.delete_object(Bucket=bucket, Key=object_key)


        #delete from dynamodb
        table.delete_item(
           Key = {
               "albumID": albumID,
               "photoID": i.get('photoID')
            }
        )
       
    return redirect('/home')    


# update photo
@app.route('/album/<string:albumID>/updatePhoto/<string:photoID>', methods=['GET', 'POST'])
def updatePhoto(albumID, photoID):
    if request.method == 'POST':

        title = request.form['title']
        description = request.form['description']
        tags = request.form['tags']

        updatedAtlocalTime = datetime.now().astimezone()
        updatedAtUTCTime = updatedAtlocalTime.astimezone(pytz.utc)

        table.update_item(
            Key = {
                "albumID": str(albumID),
                "photoID": str(photoID)
            },
            ExpressionAttributeValues={
                ':title': title,
                ':description': description, 
                ':tags': tags,
                ':updatedAt': updatedAtUTCTime.strftime("%Y-%m-%d %H:%M:%S")
            },
            TableName="photogallerydb",
            UpdateExpression='SET title = :title, description = :description, tags = :tags, updatedAt = :updatedAt',
        )    
        

        return redirect(f'''/album/{albumID}''')
    
    else:    
        response = table.query( KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq(photoID))
        results = response['Items']
        photoURL = results[0]['photoURL']
        
        return render_template('updatePhoto.html', albumID = albumID, photoURL = photoURL, photoID = photoID )
    

#delete user account
@app.route('/deleteAccount', methods = ['GET'])
def deleteAccount():
    response=table.scan(FilterExpression=Attr('user').eq(session["email"])) 
    results = response['Items']

    for i in results:
        deleteAlbum(i['albumID'])


    response1 = userTable.scan(FilterExpression=Attr('email').eq(session["email"]))
    uuid = response1['Items'][0]['uuid']

    userTable.delete_item(
        Key={"uuid": uuid, "email": session["email"]}
    )    

    return render_template("login.html")




"""
"""

# defines an error handler for http status code 400(Bad Request)
@app.errorhandler(400)
def bad_request(error):
    """ 400 page route.

    get:
        description: Endpoint to return a bad request 400 page.
        responses: Returns 400 object.
    """
    return make_response(jsonify({'error': 'Bad request'}), 400)


# 404 page not found error
@app.errorhandler(404)
def not_found(error):
    """ 404 page route.

    get:
        description: Endpoint to return a not found 404 page.
        responses: Returns 404 object.
    """
    return make_response(jsonify({'error': 'Not found'}), 404)

# defines a route for the home page ('/') for the flask applications
# decorator is a special type of function that is used to modify or extend behavior of other functions or methods
@app.route('/home', methods=['GET']) 
def home_page():
    """ Home page route.

    get:
        description: Endpoint to return home page.
        responses: Returns all the albums.
    """

    # queries the photogallery table using scan. filters the results to include results where photoID is thumbnail. 
    # create a list of table items that are only the thumbnails for each of the albums and not the photos in the album   
    response = table.scan(FilterExpression=Attr('photoID').eq("thumbnail"))
    results = response['Items']

    # if any items in results, create a list of the pictures, names, and when they were created.
    if len(results) > 0:
        for index, value in enumerate(results):
            createdAt = datetime.strptime(str(results[index]['createdAt']), "%Y-%m-%d %H:%M:%S")
            createdAt_UTC = pytz.timezone("UTC").localize(createdAt)
            results[index]['createdAt'] = createdAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y")

    return render_template('index.html', albums=results)


#GET: (else) when request, the function returns a form a to create a new album and renders the albumForm.html template
#POST: (if) processes the form data submitted by the user to create a new album
@app.route('/createAlbum', methods=['GET', 'POST'])
def add_album():
    """ Create new album route.

    get:
        description: Endpoint to return form to create a new album.
        responses: Returns all the fields needed to store new album.

    post:
        description: Endpoint to send new album.
        responses: Returns user to home page.
    """
    if request.method == 'POST':

        # retrieves the imagefile, album name, and description as data
        uploadedFileURL=''
        file = request.files['imagefile']
        name = request.form['name']
        description = request.form['description']


        # if the file exists and is a valid filename
        if file and allowed_file(file.filename):

            # generate a unique albumID using uiud.uuid4()
            albumID = uuid.uuid4()
            
            # save the photo in the upload folder
            filename = file.filename
            filenameWithPath = os.path.join(UPLOAD_FOLDER, filename)
            # saves the uploaded file the specified path on the server
            file.save(filenameWithPath)
            
            uploadedFileURL = s3uploading(str(albumID), filenameWithPath, "thumbnails");

            createdAtlocalTime = datetime.now().astimezone()
            createdAtUTCTime = createdAtlocalTime.astimezone(pytz.utc)

            table.put_item(
                Item={
                    "albumID": str(albumID),
                    "photoID": "thumbnail",
                    "name": name,
                    "description": description,
                    "thumbnailURL": uploadedFileURL,
                    "user": session['email'],
                    "createdAt": createdAtUTCTime.strftime("%Y-%m-%d %H:%M:%S")
                }
            )

        return redirect('/home')
    else:
        return render_template('albumForm.html')



@app.route('/album/<string:albumID>', methods=['GET'])
def view_photos(albumID):
    """ Album page route.

    get:
        description: Endpoint to return an album.
        responses: Returns all the photos of a particular album.
    """
    albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
    albumMeta = albumResponse['Items']

    response = table.scan(FilterExpression=Attr('albumID').eq(albumID) & Attr('photoID').ne('thumbnail'))
    items = response['Items']

    return render_template('viewphotos.html', photos=items, albumID=albumID, albumName=albumMeta[0]['name'])



@app.route('/album/<string:albumID>/addPhoto', methods=['GET', 'POST'])
def add_photo(albumID):
    """ Create new photo under album route.

    get:
        description: Endpoint to return form to create a new photo.
        responses: Returns all the fields needed to store a new photo.

    post:
        description: Endpoint to send new photo.
        responses: Returns user to album page.
    """
    if request.method == 'POST':    
        uploadedFileURL=''
        file = request.files['imagefile']
        title = request.form['title']
        description = request.form['description']
        tags = request.form['tags']
        if file and allowed_file(file.filename):
            photoID = uuid.uuid4()
            filename = file.filename
            filenameWithPath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filenameWithPath)            
            
            # use the s3uploading function to upload the image in the s3 bucket and return the url
            uploadedFileURL = s3uploading(filename, filenameWithPath)
            
            ExifData=getExifData(filenameWithPath)
            ExifDataStr = json.dumps(ExifData)

            createdAtlocalTime = datetime.now().astimezone()
            updatedAtlocalTime = datetime.now().astimezone()

            createdAtUTCTime = createdAtlocalTime.astimezone(pytz.utc)
            updatedAtUTCTime = updatedAtlocalTime.astimezone(pytz.utc)

            # put all the data for the picture in the table
            table.put_item(
                Item={
                    "albumID": str(albumID),
                    "photoID": str(photoID),
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "photoURL": uploadedFileURL,
                    "EXIF": ExifDataStr,
                    "createdAt": createdAtUTCTime.strftime("%Y-%m-%d %H:%M:%S"),
                    "updatedAt": updatedAtUTCTime.strftime("%Y-%m-%d %H:%M:%S")
                }
            )

        # the user is redirected to the page displaying the album that the photo belongs to.    
        return redirect(f'''/album/{albumID}''')

    else:

        albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
        albumMeta = albumResponse['Items']

        return render_template('photoForm.html', albumID=albumID, albumName=albumMeta[0]['name'])



@app.route('/album/<string:albumID>/photo/<string:photoID>', methods=['GET'])
def view_photo(albumID, photoID):
    """ photo page route.

    get:
        description: Endpoint to return a photo.
        responses: Returns a photo from a particular album.
    """ 
    albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
    albumMeta = albumResponse['Items']

    response = table.query( KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq(photoID))
    results = response['Items']

    if len(results) > 0:
        photo={}
        photo['photoID'] = results[0]['photoID']
        photo['title'] = results[0]['title']
        photo['description'] = results[0]['description']
        photo['tags'] = results[0]['tags']
        photo['photoURL'] = results[0]['photoURL']
        photo['EXIF']=json.loads(results[0]['EXIF'])

        createdAt = datetime.strptime(str(results[0]['createdAt']), "%Y-%m-%d %H:%M:%S")
        updatedAt = datetime.strptime(str(results[0]['updatedAt']), "%Y-%m-%d %H:%M:%S")

        createdAt_UTC = pytz.timezone("UTC").localize(createdAt)
        updatedAt_UTC = pytz.timezone("UTC").localize(updatedAt)

        photo['createdAt']=createdAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y")
        photo['updatedAt']=updatedAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y")
        
        tags=photo['tags'].split(',')
        exifdata=photo['EXIF']
        
        return render_template('photodetail.html', photo=photo, tags=tags, exifdata=exifdata, albumID=albumID, albumName=albumMeta[0]['name'])
    else:
        return render_template('photodetail.html', photo={}, tags=[], exifdata={}, albumID=albumID, albumName="")



@app.route('/album/search', methods=['GET'])
def search_album_page():
    """ search album page route.

    get:
        description: Endpoint to return all the matching albums.
        responses: Returns all the albums based on a particular query.
    """ 
    query = request.args.get('query', None)    

    response = table.scan(FilterExpression=Attr('name').contains(query) | Attr('description').contains(query))
    results = response['Items']

    items=[]
    for item in results:
        if item['photoID'] == 'thumbnail':
            album={}
            album['albumID'] = item['albumID']
            album['name'] = item['name']
            album['description'] = item['description']
            album['thumbnailURL'] = item['thumbnailURL']
            items.append(album)

    return render_template('searchAlbum.html', albums=items, searchquery=query)



@app.route('/album/<string:albumID>/search', methods=['GET'])
def search_photo_page(albumID):
    """ search photo page route.

    get:
        description: Endpoint to return all the matching photos.
        responses: Returns all the photos from an album based on a particular query.
    """ 
    query = request.args.get('query', None)    

    response = table.scan(FilterExpression=Attr('title').contains(query) | Attr('description').contains(query) | Attr('tags').contains(query) | Attr('EXIF').contains(query))
    results = response['Items']

    items=[]
    for item in results:
        if item['photoID'] != 'thumbnail' and item['albumID'] == albumID:
            photo={}
            photo['photoID'] = item['photoID']
            photo['albumID'] = item['albumID']
            photo['title'] = item['title']
            photo['description'] = item['description']
            photo['photoURL'] = item['photoURL']
            items.append(photo)

    return render_template('searchPhoto.html', photos=items, searchquery=query, albumID=albumID)



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
