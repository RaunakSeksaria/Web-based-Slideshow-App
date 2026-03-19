'''
This is the main file of the application. 
It contains all the routes and functions to run the application. 
It uses Flask as the web framework and psycopg2 to connect to the PostgreSQL database. 
It also uses moviepy to create the video from the images uploaded by the user. 
The application has a login and signup system.
The users can create an account and upload their images. 
The users can also select transitions and audio for their video. 
The admin can see all the users and all their data(its a prototype). 
The application also has a logout functionality.
'''

import os
import hashlib
import shutil
import base64
from datetime import datetime, timezone,timedelta
import jwt
from flask import Flask, render_template, request, redirect, session
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
import psycopg2
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# constants to use in the application
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_COOKIE_PERMANENT'] = True
app.config['TRANSITION'] = 'NONE'
app.config['AUDIO'] = 'NONE'
salt = os.getenv('PASSWORD_SALT') # salt to hash the password
DATABASE_URL = os.getenv('DATABASE_URL')

if not app.config['SECRET_KEY']:
    raise RuntimeError('SECRET_KEY is not set')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL is not set')


def get_db_connection():
    '''Function to connect to the database using the DATABASE_URL from the environment variable'''
    return psycopg2.connect(DATABASE_URL)

# make the folder that stores the timeline images
UPLOAD_FOLDER = 'timeline'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def generate_jwt_token(username):
    '''Function to generate jwt token'''
    payload = {
        'username': username,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=30)  # Token expires in 30 minutes
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'],
                        algorithm='HS256')  # Use encode function from jwt module
    return token

def verify_jwt_token(token):
    '''Function to verify jwt token'''
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'],
                             algorithms=['HS256'])  # Use decode function from jwt module
        return payload['username']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def create_video():
    '''Function to create the video'''
    # Get all the images from the timeline folder in alphabetical order
    # Creates the video thereby
    clips = []
    image_folder = 'timeline'
    for f in os.listdir(image_folder):
        if os.path.isfile(os.path.join(image_folder, f)):
            clips.append(ImageClip(os.path.join(image_folder, f)).set_duration(2))

    # apply the transitions
    if app.config['TRANSITION'] == "fade-out":
        for i in range(len(clips) - 1):
            clips[i] = clips[i].crossfadeout(2)
    elif app.config['TRANSITION'] == "fade-in":
        for i in range(len(clips) - 1):
            clips[i] = clips[i].crossfadein(2)

    # apply the audio
    if app.config['AUDIO'] == "audio-1":
        audio = AudioFileClip("static/audio/audio-1.mp3")
        audio = audio.subclip(0, 2 * (len(clips)))
        clips[0] = clips[0].set_audio(audio)

    elif app.config['AUDIO'] == "audio-2":
        audio = AudioFileClip("static/audio/audio-2.mp3")
        audio = audio.subclip(0, 2 * (len(clips)))
        clips[0] = clips[0].set_audio(audio)

    elif app.config['AUDIO'] == "audio-3":
        audio = AudioFileClip("static/audio/audio-3.mp3")
        audio = audio.subclip(0, 2 * (len(clips)))
        clips[0] = clips[0].set_audio(audio)

    # Concatenate clips with transitions
    video_clip = concatenate_videoclips(clips, method="compose")
    # save the video file
    video_clip.write_videofile("static/finalVideo/output_video.mp4",
                               codec="libx264", fps=24, remove_temp=True)
    # remove all the images from the timeline folder and remake the folder
    shutil.rmtree('timeline')
    os.makedirs('timeline')



@app.route('/', methods=['GET', 'POST'])
def index():
    '''Function to handle the landing page'''
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''Function to handle the login page'''
    if request.method == 'POST':
        # connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # retrieve data from the form
        name = request.form['name']
        password = request.form['password']
        # print it on the terminal(for debugging)
        print(name, password)

        # check if the user is admin or not
        if name == "mukta" and password == "ihateiss":
            return redirect("/admin")

        # hash the password
        hashed_password = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

        # check if the user is correct by running the query,
        # if the user is valid then go to the user index page else show an alert
        query = "SELECT username, password FROM users where" \
            " username= '"+name+"' and password='"+hashed_password+"' "
        cursor.execute(query)
        results = cursor.fetchall()

        if len(results) == 0: # if the user is not found
            return render_template('login.html', error = True)
        # implicit else
        # if found go to the home page and store the token in the session
        session['token'] = generate_jwt_token(name)
        return redirect("/home")

    return render_template('login.html') # if method is not post then show the login page

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    '''Function to handle the signup page'''
    if request.method == 'POST':
        # connect to the server
        connection = get_db_connection()
        cursor = connection.cursor()

        # get data from the html form
        firstname = request.form['firstn']
        lastname = request.form['lastn']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        #hash the password before storing
        password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

        #print the data in terminal for debugging
        print(firstname, lastname, username, email, password_hash)

        # insert the data into the database
        query = " INSERT INTO users VALUES " \
        "('"+firstname+"' , '"+lastname+"' , '"+username+"', '"+email+"', '"+password_hash+"') "
        cursor.execute(query)
        connection.commit()
        session['token'] = generate_jwt_token(username)

        return redirect("/home") # go to the home page after signup

    return render_template('signup.html') # if method is not post then show the signup page

@app.route("/upload",methods=["POST","GET"])
def upload():
    '''Function to handle the upload page'''
    # check if the user is logged in or not
    token = session.get('token')
    if not token: # if not logged in then go to the login page
        return redirect('/login')
    username = verify_jwt_token(token)
    if not username: # if not logged in then go to the login page
        return redirect('/login')

    if request.method == 'POST':

        # connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # get the images from the form
        files = request.files.getlist('images[]')

        # store the images into sql database
        for file in files:
            image_file = file.read()
            filename = file.filename

            myname = username
            query = "INSERT INTO images (username, image, imagename) VALUES (%s, %s, %s)"
            cursor.execute(query, (myname, psycopg2.Binary(image_file), filename))

        connection.commit() # commit the changes and redirect to the home page
        return redirect("/home")

    return render_template('/upload.html')

@app.route("/home", methods=["POST", "GET"])
def home():
    '''Function to handle the home page'''
    # check if the user is logged in or not
    token = session.get('token')
    if not token: # if not logged in then go to the login page
        return redirect('/login')
    username = verify_jwt_token(token)
    if not username: # if not logged in then go to the login page
        return redirect('/login')

    # connect to the database
    connection = get_db_connection()
    cursor = connection.cursor()

    # get the user data from the database
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user_data = cursor.fetchall()[0]
    # get the imagenames
    cursor.execute("SELECT imagename FROM images WHERE username = %s", (username,))
    imagenames = cursor.fetchall()
    # get the images
    cursor.execute("SELECT image FROM images WHERE username = %s", (username,))
    images = cursor.fetchall()
    connection.close()

    print(user_data) # print the data for debugging

    # get the name and other data from the list
    name = user_data[0][0]
    lastname = user_data[0][1]
    email = user_data[0][3]

    # convert the images to base64 format to display on the html page
    images_base64 = []
    for image in images:
        image = image[0]
        image_base64 = base64.b64encode(image).decode('utf-8')
        images_base64.append((image_base64))

    # get the image names
    image_names = []
    for image_name in imagenames:
        image_names.append(image_name[0])

    # render the home page with the data
    return render_template("home.html", username = name,
                            lastname = lastname, email = email,
                              images_data = images_base64, image_names = image_names,
                                total_images = len(images_base64))

@app.route('/audio', methods=["POST", "GET"])
def audio_fn():
    '''Function to handle the audio and transitions page'''
    if request.method == "POST": # store the audio and transitioin selected by the user
        app.config['TRANSITION'] = request.form['transition']
        app.config['AUDIO'] = request.form['audio']

    # render the audio page
    return render_template("trans_aud.html")


@app.route('/admin')
def admin():
    '''Function to handle the admin page'''
    # connect to the database
    connection = get_db_connection()
    cursor = connection.cursor()

    # get the userdata from the database
    query = "SELECT * FROM users"
    cursor.execute(query)
    users = cursor.fetchall()
    connection.close()

    print(users[0][0]) # print the data for debugging

    # render the admin page with the data
    return render_template('admin.html', user_data = users)

@app.route('/video', methods=["POST","GET"])
def video():
    '''Function to handle the video preview page'''
    return render_template('video.html')


@app.route('/edit',methods=["POST","GET"])
def edit():
    '''Function to handle the editor page'''
    # check if the user is logged in or not
    token = session.get('token')
    if not token: # if not logged in then go to the login page
        return redirect('/login')
    username = verify_jwt_token(token)
    if not username: # if not logged in then go to the login page
        return redirect('/login')

    # connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # get the images from the database
    cursor.execute("SELECT image FROM images WHERE username='"+username+"'")
    image_data = cursor.fetchall()
    conn.close()

    # convert the images to base64 format to display on the html page
    images_base64 = []
    for image in image_data:
        image = image[0]
        image_base64 = base64.b64encode(image).decode('utf-8')
        images_base64.append((image_base64))

    if request.method == 'POST':
        # get the timeline images from the html page
        if 'files[]' not in request.files:
            return 'No file part'
        files = request.files.getlist('files[]')

        # list of names to store the images in the timeline folder in alphabetical order
        names_list = ['aa', 'ab', 'ac', 'ad', 'ae', 'af', 'ag', 'ah',
                       'ai', 'aj', 'ak', 'al', 'am', 'an', 'ao', 'ap', 
                       'aq', 'ar', 'as', 'at', 'au', 'av', 'aw', 'ax', 
                       'ay', 'az','ba', 'bb', 'bc', 'bd', 'be', 'bf', 
                       'bg', 'bh', 'bi', 'bj', 'bk', 'bl', 'bm', 'bn', 
                       'bo', 'bp', 'bq', 'br', 'bs', 'bt', 'bu', 'bv', 
                       'bw', 'bx', 'by', 'bz']
        curr_index = 0
        for file in files:
            # give the image name from the list
            res = ''.join(str(names_list[curr_index]))
            curr_index += 1

            if file.filename == '':
                return 'No selected file'

            # save the image in the timeline folder
            if file:
                filename = str(res) + ".png"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # create the video and show the preview
        create_video()
        print("video is succesfully made")
        return redirect('/video')

    # if not post return the editor page with the user data
    return render_template('editor.html', images = images_base64)

@app.route('/logout')
def logout():
    '''Function to handle the logout functionality'''
    session.pop('token', None) # pop the user token on logout
    shutil.rmtree('static/finalVideo') # remove the video from the finalVideo folder
    os.makedirs('static/finalVideo')
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
