import os
import sqlite3
from flask import Flask, render_template, g, request, session, escape, redirect, flash, url_for, redirect
from werkzeug.security import generate_password_hash, check_password_hash

app=Flask(__name__)
app.secret_key = 'br\xcb\xa2\x81\xa4\xf4\xda\xdd\xb3\xa0\x92\x11\xa5\xe6\xb7R}\x11zHP\x9b\xbbz'

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

def connect_db():
	rv = sqlite3.connect(app.config['DATABASE'])
	rv.row_factory = sqlite3.Row
	return rv

def query_db(query, args=(), one=False):
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	cur.close()
	if one: return (rv[0] if rv else None)
	else: return rv
	
def query_insert(query, args=()):
	db = get_db()
	db.execute(query, args)
	db.commit()

#it doesnt work for some reason i'll find out later instead sqlite3 bla.db < schema.sql
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = sqlite3.connect('downupchunk.db')
		db.row_factory = make_dicts
	return db

def list_users():
	people = ""
	for user in query_db('select username from users'):
		people += user['username'] + '<br />'
	return people

@app.teardown_appcontext
def close_db(error):
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()

#edit later
def check_errors(username_field, password_field):
	if username_field=="" and password_field=="":
		return "Please enter username and password"
	if username_field=="":
		return "Please enter username"
	if password_field=="":
		return "Please enter password"
	return None

@app.route('/')
def index():
	return render_template('layout.html')

@app.route('/user/<username>')
def username():
	return 'User %s' % username

@app.route('/post/<int:post_id>')
def post_id():	
	return 'Post %s' % post_id

@app.route('/entries')
def show_entries():
	db = get_db()
	cur = db.execute('select title,text from entries order by id desc')
	entries = cur.fetchall()
	return render_template('entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
	if not session.get('logged_in'):
		abort(401)
	db = get_db()
	db.execute('insert into entries (title, text) values (?,?)', [request.form['title'], request.form['text']])
	db.commit()
	flash('new entry was successfully posted!')
	return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		error = check_errors(username, password)
		if error is None:
			user = query_db('select username, password from users where username=?', [username], one=True)
			if user is None: error='No such user'
			else: 
				isit = check_password_hash(user['password'], password)
				if isit: 
					session['username'] = user['username']
					session['logged_in'] = True
					flash('You logged in')
					return redirect(url_for('show_entries'))
				else: return 'no'
	return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

@app.route("/register/", methods=['POST', 'GET'])
def register():
	error = None
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		email = request.form['email']
		error = check_errors(username, password)
		if error is None:
			user = query_db('select username from users where username=?', [username], one=True)
			if user is not None: error='This username already exists :('
			else: 
				pw_hash = generate_password_hash(password, method='pbkdf2:sha512')
				query_insert('insert into users (username, password, email) values (?, ?, ?)', [username, pw_hash, email])
				return 'Registered!'
	return render_template('register.html', error=error)

if __name__ == '__main__':
	app.run(debug=True)

