from flask import Flask, render_template, request, redirect, url_for, session
import requests
from authlib.integrations.flask_client import OAuth
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import numpy as np
from flask_mail import Mail, Message
import pandas as pd

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
            session['email'] = username
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
            cursor.execute('SELECT fl_num,tail_num,origin,dest,day_of_month,month,year,day_of_week,dep_time,arr_time FROM flightdata WHERE tail_num = %s and fl_num= %s', (tailno,flightno ))
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
            cursor.execute('SELECT fl_num,tail_num,origin,dest,day_of_month,month,year,day_of_week,dep_time,arr_time FROM flightdata WHERE dest = %s and origin= %s', (dest,src ))
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

            src = int(src)
            dest = int(dest)
            flightno = float(flightno)

            dayOfMonth = dates[8:]
            month = dates[5:7]

            dayOfMonth = float(dayOfMonth)
            month = float(month)
            weekday = float(weekday)
            deptime = float(deptime)
            arrtime = float(arrtime)

            API_KEY = "BZUJD8H61gflLqxUO5awiuhNW7LgKLJqlbPdm-hHYGrI"
            token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
            mltoken = token_response.json()["access_token"]


            data = [1580.25, 1257.75, 671.5, 1103.0, 1003.0]
            predef = [['CANCELLED', 0], ['DIVERTED', 0], ['DISTANCE', 1161.0]]

            #cent = pd.DataFrame(data)
            predef = pd.DataFrame(predef)

            DEP_CENT = data[src]
            ARR_CENT = data[dest]

            header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}
            payload_scoring = {"input_data": [{"field": [["MONTH", "DAY_OF_MONTH", "DAY_OF_WEEK", "FL_NUM", "ORIGIN", "DEST", "DEP_TIME",  "ARR_TIME", "CANCELLED", "DIVERTED", "DISTANCE", "DEP_CENT", "ARR_CENT"]],"values": [[month, dayOfMonth, weekday, flightno, src, dest, deptime, arrtime, 0, 0, 1161.0, DEP_CENT, ARR_CENT]]}]}
            #payload_scoring = {"input_data": [{"field": [["MONTH", "DAY_OF_MONTH", "DAY_OF_WEEK", "FL_NUM", "ORIGIN", "DEST", "DEP_TIME", "DEP_DEL15", "ARR_TIME", "ARR_DEL15", "CANCELLED", "DIVERTED", "DISTANCE", "DEP_CENT", "ARR_CENT", "ARR_DELAY"]], "values": [[1,5,2,1267,0,1,1834,1,2011,1,0,0,594,1580.25,1103,371.0]]}]}
            #response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/8145ab88-e889-480b-8f4d-1bcb918ff176/predictions?version=2022-11-25', json=payload_scoring,
            response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/6ac7f286-080c-4d2b-9b27-c2e8f3574556/predictions?version=2022-11-25', json=payload_scoring,
            headers={'Authorization': 'Bearer ' + mltoken})
            #headers={'Authorization': 'Bearer ' + mltoken})
            predictions  = response_scoring.json()
            print(predictions)
            predict = predictions['predictions'][0]['values'][0][0]
            print(predict)
            predict = predict/60
            email = session['email']
            print(email)
            if predict>0:
                msg2 = Message(
                'Sunwing Flights - Flight Delay Notification',
                sender ='sunwingflights@gmail.com',
                recipients = [email]
                )
            source=['ATL', 'MSP', 'JFK', 'DTW', 'SEA']
            msg2.body = 'This is to inform you that your flight '+str(flightno)+' starting from '+str(source[src])+' on '+str(dates)+' is estimated to be delayed by '+str(predict)
            print(msg2)
            mail.send(msg2)

            return render_template('result.html',data = predict)
    return render_template('predict.html')

@app.route('/result')
def result():
    return render_template('result.html')            
    
if __name__=="__main__":
    app.run(debug=True)
