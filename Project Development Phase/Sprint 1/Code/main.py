import re
from flask import Flask, redirect, render_template, request, session, url_for, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)

app.secret_key = 'your secret key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ibm'

mysql = MySQL(app)

@app.route("/")
def home():
    return render_template("home.html")
@app.route("/login", methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        username = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM login WHERE email = % s AND pwd = % s', (username, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['email']
            session['username'] = account['name']
            return render_template('search.html')
        else:
            error = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)

@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return redirect(url_for('home'))

@app.route("/register", methods=['POST'])
def register():
    if 'name' in request.form and 'age' in request.form and 'country' in request.form and 'phone' in request.form and 'email' in request.form and 'password' in request.form:
        n = request.form['name']
        a = request.form['age']
        c = request.form['country']
        ph = request.form['phone']
        e = request.form['email']
        p = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO login VALUES (% s, % s, % s, % s, % s, % s)', (n, a, c, ph, e, p,))
        mysql.connection.commit()
        return render_template('search.html')
    

@app.route("/search")
def search():
    return render_template("search.html")

if __name__=="__main__":
    app.run(debug=True)