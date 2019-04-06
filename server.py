#Import Flask Library
import os
from flask import Flask, render_template, request, session, url_for, redirect, send_file
import hashlib
import pymysql.cursors
from functools import wraps

#Initialize the app from Flask
app = Flask(__name__)
app.secret_key = 'some key that you will never guess'
IMAGES_DIR = os.path.join(os.getcwd(), "images")

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user ='root',
                       password = None,
                       db='finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor,
                       autocommit=True)

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec

@app.route('/')
def hello():
    if "username" in session:
        return redirect(url_for("home"))
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    plaintextPasword = request.form["password"]
    hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hashedPassword))
    #stores the results in a variable
    data = cursor.fetchone()
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid password or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    plaintextPasword = request.form["password"]
    hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()
    fname = request.form['fname']
    lname = request.form['lname']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s, "", "", false)'
        cursor.execute(ins, (username, hashedPassword, fname, lname))
        cursor.close()
        return render_template('index.html')


@app.route('/home') #get posts, name, and bio
@login_required
def home():
    user = session['username']
    cursor = conn.cursor();
    queryName ='SELECT fname, lname FROM Person WHERE username = %s'
    cursor.execute(queryName, (user))
    name = cursor.fetchone()
    queryBio = 'select bio from Person where username = %s'
    cursor.execute(queryBio,(user))
    bio = cursor.fetchone()
    cursor.close()
    return render_template('home.html', username=user, name = name, bio = bio)

@app.route("/follow", methods=['GET'])
@login_required
def follow():
    return render_template("follow.html")

@app.route('/followAuth', methods=['GET', 'POST'])
def followAuth():
    username = session['username']
    cursor = conn.cursor();
    followee = request.form['followee']
    query = 'select * from Person where username = %s'
    cursor.execute(query, (followee))
    checker = cursor.fetchone()
    if (checker):
        queryFollow = 'select * from Follow where followerUsername = %s and followeeUsername = %s'
        cursor.execute(queryFollow, (username, followee))
        isFollowed = cursor.fetchone()
        if (isFollowed):
            cursor.close()
            return render_template('follow.html', error = "You have already requested to follow this person!")
        else:
            queryWillFollow = "insert into Follow values (%s, %s, false)"
            cursor.execute(queryWillFollow, (username, followee))
            cursor.close()
            return render_template('follow.html', message = "You have requested a Follow.")
    else:
        return render_template('follow.html', error = "This person does not exist!")

@app.route("/view_followee")
@login_required
def viewFollowees():
    username = session['username']
    cursor = conn.cursor()
    query = "select * from Follow where followerUsername = %s"
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    return render_template("view_followee.html", data = data)

@app.route("/followers")
@login_required
def followers():
    username = session['username']
    cursor = conn.cursor()
    query = "select * from Follow where followeeUsername = %s AND acceptedfollow = 1"
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    return render_template("followers.html", data = data)

@app.route("/follow_requests")
@login_required
def followRequests():
    username = session['username']
    cursor = conn.cursor()
    query = "select * from Follow where followeeUsername = %s AND acceptedfollow = false"
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    return render_template("follow_requests.html", data = data)

@app.route("/accept_follow/<string:id>", methods=['GET', 'POST'])
@login_required
def acceptFollow(id):
    username = session['username']
    follower = id
    cursor = conn.cursor()
    query = "update Follow set acceptedfollow = true where followerUsername = %s and followeeUsername = %s"
    cursor.execute(query, (follower, username))
    cursor.close()
    return render_template("accepted_follow.html", data = follower)

@app.route("/reject_follow/<string:id>", methods=['GET', 'POST'])
@login_required
def rejectFollow(id):
    username = session['username']
    follower = id
    cursor = conn.cursor()
    query = "delete from Follow where followerUsername = %s and followeeUsername = %s"
    cursor.execute(query, (follower, username))
    cursor.close()
    return render_template("reject_follow.html", data = follower)

@app.route('/post_bio', methods=['POST']) #change bio
@login_required
def postBio():
    username = session['username']
    cursor = conn.cursor()
    bio = request.form['postBio']
    query = 'UPDATE Person SET bio = %s WHERE username = %s'
    cursor.execute(query, (bio, username))
    cursor.close()
    return redirect(url_for('home'))

@app.route("/upload", methods=["GET"])
@login_required
def upload():
    return render_template("upload.html")

@app.route("/images", methods=["GET"])
@login_required
def images():
    username = session['username']
    query = "SELECT * FROM photo WHERE photoOwner = %s ORDER BY timestamp DESC"
    with conn.cursor() as cursor:
        cursor.execute(query, username)
    data = cursor.fetchall()
    return render_template("images.html", images=data)

@app.route("/image/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")
    
@app.route("/uploadImage", methods=["POST"])
@login_required
def upload_image():
    username = session['username']
    if request.files:
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename
        filepath = os.path.join(IMAGES_DIR, image_name)
        image_file.save(filepath)
        shareWith = request.form['share']
        if shareWith == "yes":
            query = 'INSERT INTO Photo (photoOwner, filePath, caption, allFollowers) VALUES(%s, %s, %s, true)'
        else:
            query = 'INSERT INTO Photo (photoOwner, filePath, caption, allFollowers) VALUES(%s, %s, %s, false)'
        caption = request.form['caption']
        cursor = conn.cursor()
        cursor.execute(query, (username, image_name, caption))    
        cursor.close()
        message = "Image has been successfully uploaded."
        return render_template("upload.html", message=message)
    else:
        message = "Failed to upload image."
        return render_template("upload.html", message=message)


@app.route('/select_user') #look at a user
@login_required
def select_user():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT followeeUsername FROM Follow WHERE followerUsername = %s AND acceptedfollow = 1'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_user.html', user_list=data)

@app.route('/show_posts', methods=["GET"]) #show posts and bio of user
@login_required
def show_posts():
    username = session['username']
    poster = request.args['poster']
    cursor = conn.cursor()
    query = 'SELECT * FROM Photo WHERE photoOwner = %s ORDER BY timestamp DESC'
    cursor.execute(query, (poster))
    data = cursor.fetchall()
    queryName ='SELECT fname, lname FROM Person WHERE username = %s'
    cursor.execute(queryName, (poster))
    name = cursor.fetchone()
    cursor.close()
    return render_template('show_posts.html', posts=data, name = name)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run('192.168.0.11', 8000, debug = True)
