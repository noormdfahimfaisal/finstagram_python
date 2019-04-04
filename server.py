#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='password',
                       db='finstagram_db',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
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
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
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
        cursor.execute(ins, (username, password, fname, lname))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT timestamp, filePath, caption FROM Photo WHERE photoOwner = %s ORDER BY timestamp DESC'
    cursor.execute(query, (user))
    data = cursor.fetchall()
    queryName ='SELECT fname, lname FROM Person WHERE username = %s'
    cursor.execute(queryName, (user))
    name = cursor.fetchall()
    queryBio = 'select bio from Person where username = %s'
    cursor.execute(queryBio,(user))
    bio = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, posts=data, name = name, bio = bio)

@app.route('/post_bio', methods=['POST'])
def postBio():
    username = session['username']
    cursor = conn.cursor();
    bio = request.form['postBio']
    query = 'UPDATE Person SET bio = %s WHERE username = %s'
    cursor.execute(query, (bio, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor();
    filePath = request.form['filePath']
    caption = request.form['caption']
    query = 'INSERT INTO Photo (photoOwner, filePath, caption, allFollowers) VALUES(%s, %s, %s, true)'
    cursor.execute(query, (username, filePath, caption))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/select_user')
def select_user():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM Person'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_user.html', user_list=data)

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor();
    query = 'SELECT timestamp, filePath, caption FROM Photo WHERE photoOwner = %s ORDER BY timestamp DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    queryBio = 'select bio from Person where username = %s'
    cursor.execute(queryBio, (poster))
    bio =cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data, bio=bio)

#@app.route('/follow')
#def follow():
#    follower = session['username']
#    followee = request.args(followee)
#    cursor = conn.cursor();
#    if follower != followee:
#        query = 'INSERT INTO Follow values (%s, %s, false)'
#        cursor.execute(query, (follower, followee))
#    return render_template('request_follow, ', )

@app.route("/uploadImage", methods=["POST"])
def upload_image():
    if request.files:
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename
        filepath = os.path.join(IMAGES_DIR, image_name)
        image_file.save(filepath)
        query = "INSERT INTO Photo (timestamp, filePath) VALUES (%s, %s)"
        with connection.cursor() as cursor:
            cursor.execute(query, (time.strftime('%Y-%m-%d %H:%M:%S'), image_name))
        message = "Image has been successfully uploaded."
        return render_template("upload.html", message=message)
    else:
        message = "Failed to upload image."
        return render_template("upload.html", message=message)
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('localhost', 5000, debug = True)