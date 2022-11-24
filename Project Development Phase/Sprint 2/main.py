from flask import Flask, render_template, request, redirect, url_for, session
import requests
from authlib.integrations.flask_client import OAuth
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import numpy as np
from flask_mail import Mail, Message

app = Flask(__name__)

app.secret_key = 'IBM_PROJECT'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ibm'

app.config['SERVER_NAME'] = 'localhost:5000'
oauth = OAuth(app)


mysql = MySQL(app)

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'sunwingflights@gmail.com'
app.config['MAIL_PASSWORD'] = 'nbbxnzeipbugermm'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)
@app.route('/')
def main():
    return render_template("main.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM logindata WHERE email = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg=msg)

@app.route('/google/')
def google():
	GOOGLE_CLIENT_ID = "680220998929-iu5kid06dbqfha3v7bjne83ln6evt548.apps.googleusercontent.com"
	GOOGLE_CLIENT_SECRET = "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"    
	
	CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
	oauth.register(
		name='google',
		client_id=GOOGLE_CLIENT_ID,
		client_secret=GOOGLE_CLIENT_SECRET,
		server_metadata_url=CONF_URL,
		client_kwargs={
			'scope': 'openid email profile'
		}
	)

	redirect_uri = url_for('google_auth', _external=True)
	return oauth.google.authorize_redirect(redirect_uri)

@app.route('/google/auth/')
def google_auth():
    token = oauth.google.authorize_access_token()
    user = oauth.google.parse_id_token(token, nonce=None)
    print(" Google User ", user)
    session['loggedin'] = True
    session['email'] = user['email']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id FROM logindata WHERE email = %s', (user['email'], ))
    a = cursor.fetchone()
    cursor.execute('SELECT username FROM logindata WHERE email = %s', (user['email'], ))
    b = cursor.fetchone()
    session['id'] = a['id']
    session['username'] = b['username']
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return redirect(url_for('main'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        age = request.form['age']
        country = request.form['country']
        phone = request.form['phone']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM logindata WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO logindata VALUES (NULL, %s, %s, %s, %s, %s, %s)', (username, password, email, age, country, phone))
            mysql.connection.commit()
            msg = 'You have successfully registered!'

            msg1 = Message(
                'Confirmation Mail - Sunwing Flights',
                sender ='sunwingflights@gmail.com',
                recipients = [email]
                )
            msg1.body = 'This mail is to inform you that your account has been sucessfully registered\n\nUsername: ' + username + '\nPassword: ' + password + '\nEmail: '+email+'\nAge: '+age+'\nCountry: '+country+'\nPhone: '+phone
            print(msg1)
            mail.send(msg1)
    elif request.method == 'POST':
        msg = 'Please fill out the form!'

    return render_template('register.html', msg=msg)

@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM logindata WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        return render_template('profile.html', account=account)
    return redirect(url_for('login'))

@app.route('/searchflight', methods=['GET', 'POST'])
def searchflight():
    return render_template('searchflight.html')

@app.route('/display', methods=['GET', 'POST'])
def display():
    msg=''
    if request.method == 'POST':
        if 'flightno' in request.form and 'tailno' in request.form:
            flightno = request.form['flightno']
            tailno = request.form['tailno']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT fl_num,tail_num,origin,dest,day_of_month,month,year,day_of_week,dep_time,arr_time FROM flightdata__1___1_ WHERE tail_num = %s and fl_num= %s', (tailno,flightno ))
            r = cursor.fetchall()
    return render_template('display.html',data = r)            
            
            
@app.route('/searchsd', methods=['GET', 'POST'])
def searchsd():
    return render_template('searchsd.html')

@app.route('/display2', methods=['GET', 'POST'])
def display2():
    if request.method == 'POST':
        if 'src' in request.form and 'dest' in request.form:
            src = request.form['src']
            dest = request.form['dest']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            print(src,dest)
            cursor.execute('SELECT fl_num,tail_num,origin,dest,day_of_month,month,year,day_of_week,dep_time,arr_time FROM flightdata__1___1_ WHERE dest = %s and origin= %s', (dest,src ))
            r = cursor.fetchall()
    return render_template('display.html',data = r)  

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        if 'flightno' in request.form and 'src' in request.form and 'dest' in request.form and 'dates' in request.form and 'weekday' in request.form and 'deptime' in request.form and 'arrtime' in request.form and 'tailno' in request.form:
            flightno = request.form['flightno']
            tailno = request.form['tailno']
            src = request.form['src']
            dest = request.form['dest']
            dates = request.form['dates']
            weekday = request.form['weekday']
            deptime = request.form['deptime']
            arrtime = request.form['arrtime']
            dayOfMonth = dates[8:]
            month = dates[5:7]
            #return "The searched flight details are : FN:"+flightno+" DOM:"+dayOfMonth+" Month:"+month+" Weekday:"+weekday+" Departure Time:"+deptime+" Arrival Time:"+arrtime+" Date:"+dates+" Tail No:"+tailno

            API_KEY = "BZUJD8H61gflLqxUO5awiuhNW7LgKLJqlbPdm-hHYGrI"
            token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
            mltoken = token_response.json()["access_token"]

            header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}
            payload_scoring = {"input_data": [{"field": [["MONTH", "DAY_OF_MONTH", "DAY_OF_WEEK", "TAIL_NUM", "FL_NUM", "ORIGIN", "DEST", "DEP_TIME", "DEP_DEL15", "ARR_TIME", "ARR_DEL15", "CANCELLED", "DIVERTED", "DISTANCE", "DEP_CENT", "ARR_CENT", "ARR_DELAY"]], "values": [[month, dayOfMonth, weekday, tailno, flightno, src, dest, deptime, 0.0, arrtime, 0.0, 0.0, 0.0, 2182.0, 1580.25, 1003.00, -41.0]]}]}
            response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/ad92830b-9762-40e3-96ae-185b7fddce67/predictions?version=2022-11-18', json=payload_scoring, 
            
            headers={'Authorization': 'Bearer ' + mltoken})
            print("Scoring response")
            predictions  = response_scoring.json()
            predict = predictions['predictions'][0]['values'][0][0]
            print(predict)

    return render_template('predict.html')
    
if __name__=="__main__":
    app.run(debug=True)
