# Flask
Flask is a lightweight, "micro" web framework for Python designed for building web applications and APIs quickly and easily.

## Table of Contents
1. [Routes](#basic-flask-app)
2. [Core Objects](#core-objects)  
2 [Session and Cookies](#session-and-cookies)
3. [Jinja Templates](#jinja-templates)
4. [Form Handling & Validation, Flash Messages](#form-handling-and-validation-flash-messages)
4. [Application Structure & Blueprints](#application-structure-and-blueprints)
4. [SQLite and SQLAlchemy ORM Data Management](#sqlite-and-sqlalchemy-orm-data-management)

## Running Flask App
```bash
flask run
python -m flask run
python app.py
```

## HTTP Methods
| Method     | Purpose                                      |
| ---------- | -------------------------------------------- |
| **GET**    | Request data from server (parameters in URL) |
| **POST**   | Send data to server (data in request body)   |
| **PUT**    | Update existing data                         |
| **PATCH**  | Partially update a resource                  |
| **DELETE** | Delete data                                  |

## Basic Flask App
```bash
from flask import Flask, request

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key' # Session Management, Flash Messages

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
      return "Hello World!", 200

@app.route('/greet/<str:name>') # str (default), int, float, path (accepts slashes)
def greet(name):
    return f'Hello, {name}!'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
```

## Core Objects
| Core Object | What It Does                                 | Example                                                          |
| ----------- | -------------------------------------------- | ---------------------------------------------------------------- |
| `request`   | Read what the user sends                     | `username = request.form.get('username')`                        |
| `Response`  | Send something back to the user              | `return Response('Invalid credentials.', mimetype='text/plain')` |
| `render_template`  | Render HTML template                  | `render_template('index.html', name=username)` → {{ name }} in html. index.html must be under 'templates' folder.       |
| `redirect`  | Move the user to a different page            | `return redirect(url_for('welcome'))`                            |
| `url_for`   | Build a route dynamically from function name | `url_for('logout')` → "/logout"                                  |
| `session`   | Remember user info across pages              | `session['username'] = username`, `session.get('username')`, `session.pop('username', None)`, `session.clear()`|

## Session and Cookies
HTTP is a stateless protocol, meaning each request is independent and the server does not retain information about previous interactions.
- Cookies = A cookie is small data stored in the user's browser. Limit ~4KB.
- Sessions = A session stores user data on the server, and the browser only keeps a **session ID** (usually via a cookie).

In Flask specifically **sessions are actually stored in cookies (client-side)**. But they are **signed and encrypted using secret_key**. So, user cannot modify session data easily. But technically it’s still stored in the browser.

```bash
from flask import session

app.config['SECRET_KEY'] = 'your_secret_key' # app.secret_key (required)

@app.route('/set_session')
def set_session():
    session['username'] = 'ismail'
    return "Session set"

@app.route('/get_session')
def get_session():
    # username = session.pop('username', None)
    if 'username' in session:
      username = session.get('username')
      return username
    
    session.clear() # clears all data stored in the session
```

```bash
from flask import make_response, request

@app.route('/set_cookie')
def set_cookie():
    resp = make_response('index.html', message='Cookie set') # make_response create and customize an HTTP response object before sending it to the client.
    resp.set_cookie('username', 'ismail')
    return resp

@app.route('/get_cookie')
def get_cookie():
    username = request.cookies.get('username')
    return render_template('index.html', username=username)

@app.route('/remove_cookie')
def set_cookie():
    resp = make_response('index.html', message='Cookie removed')
    resp.set_cookie('username', expires=0)
    return resp
```

## Flash Messages (flash() → redirect())
  ```bash
    # app.py
    from flask import flash

    # required for flashing (messages are stored in session temporarily)
    app.config['SECRET_KEY'] = 'your_secret_key' # app.secret_key

    flash('Your message')
    # with categories
    flash("Login successful!", "success")
    flash("Invalid credentials", "error")

    return redirect(url_for('home'))
  ```
  
  ```bash
    <!-- base.html -->
    {% with messages = get_flashed_messages() %} # get flash msg list

      {% if messages %}
        {% for msg in messages %}
          <p>{{ msg }}</p>
        {% endfor %}
      {% endif %}

    {% endwith %}
    

    # with categories
    {% with messages = get_flashed_messages(with_categories=true) %}

      {% if messages %}
        {% for category, msg in messages %}
          <p class="{{ category }}">{{ msg }}</p>
        {% endfor %}
      {% endif %}
    
    {% endwith %}
  ```

## Jinja Templates
Jinja2 templates are a way to generate dynamic HTML (or text) by mixing static content + Python-like logic.  
**Documentation:** https://jinja.palletsprojects.com/en/stable/

> All HTML templates should be in 'templates' folder.

> return render_template("index.html", name="Ismail", gender="Male")

- Variables: `{{ variable }}`
- Filters: `{{ variable|upper }} # lower, title, replace('l', 'L')`
- Dynamic URL: `<a href="{{ url_for('about') }}">About</a>`

- Conditions
  ```bash
    {% if age >= 18 %}
      Adult
    {% elif age >= 13 %}
      Teen
    {% else %}
      Child
    {% endif %}
  ```

- Loops
  ```bash
    {% for item in items %}
      {{ item }}
    {% endfor %}
  ```

- Temporary Scope Variables
  ```bash
  {% with name='ismail' %}
    <p>{{ name }}</p> # local variable
  {% endwith %}
  ```

- Includes
  ```bash
    {% include "header.html" %}
  ```

- Template Inheritance (reuse base layout across multiple pages)
  > Use **{% block block_name %}...{% endblock %}** for the elements which you want to change or extend in your base HTML file. In the derived HTML file use again same if you want to override or extend the content under these blocks.
  
  Base Template:
  ```bash
    <!-- base.html file -->
    <html>
      <head>
      {% block head %}
        <title>{% block title %}My Website{% endblock %}</title>
      {% endblock %}
      </head>
      <body>
        {% block content %}{% endblock %}
      </body>
    </html>
  ```
  Child Template:
  ```bash
    {% extends "base.html" %}

    {% block title %}
      Home Page # override the title
    {% endblock %}

    {% block title %}
      Home Page - {{ super() }} # super() add the content from base.html
    {% endblock %}

    {% block content %}
      <h2>Welcome!</h2>
      <p>This is the home page.</p>
    {% endblock %}
  ```

## Form Handling and Validation
> The **PRG (Post → Redirect → Get)** pattern is a web development technique **used to prevent duplicate form submissions**. After a user submits a form via POST, the server responds with a redirect to a new URL, and the browser performs a GET request to display the result page. This avoids issues like repeated submissions on refresh, “Confirm Form Resubmission” warnings, and messy URLs, while improving user experience. In Flask, it’s implemented by flashing messages (optional) and using `redirect(url_for(...))` after processing POST data, then rendering the template in the GET route.

- Manual Form Handling
  ```bash
    var = request.form.get('key') # safer
    # var = request.form.['key'] # not-safe, throw an error if key is missing
  ```

- File Handling
  ```bash
  import os
  import uuid # unique identifier for generating unique filenames to avoid collisions

  UPLOAD_FOLDER='static/uploads'
  app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # stores upload folder path inside Flask config. We can access like app.config['UPLOAD_FOLDER'] anywhere in the app.
  os.makedirs(UPLOAD_FOLDER, exist_ok=True) # make sure folder exists

  @app.route('/upload', methods=['POST'])
  def upload():
      file = request.files.get('file')

      if not file or file.filename == '': # no file sent or user didn't select a file
          return 'No file selected.', 400

      filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'{uuid.uuid4()}.jpeg')
      file.save(filepath)

      return f'File uploaded successfully: {file.filename}'
  ```

- JavaScript JSON Data Handling
  ```bash
  from flask import jsonify

  @app.route('/handle_post', methods=['POST'])
  def handle_post():
      # greeting = request.json.get('greeting')
      # name = request.json.get('name')

      data = request.get_json() # get the JSON data as a dictionary
      greeting = data.get('greeting')
      name = data.get('name')

      if not greeting or not name:
          return {'error': 'Missing greeting or name'}, 400

      return jsonify({'message': f'{greeting}, {name}!'})
  ```

  ```bash
  <h1>JavaScript JSON Request</h1>
  <button id="post-btn">Send POST Request</button>

  <script type="text/javascript">
      const postButton = document.getElementById('post-btn');
      const jsonData = {name:'Ismail', greeting:"AOA"}

      postButton.addEventListener('click', () => {
          fetch('{{ url_for("handle_post") }}', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json; charset=UTF-8'
              },
              body: JSON.stringify(jsonData)
          })
          .then(response => response.json())
          .then(data => {
              console.log('Response from server:', data);
          })
          .catch(error => {
              console.error('Error:', error);
          });
      });
  ```

- Flask-WTF
  Flask-WTF is a Flask extension that simplifies **web form handling** by integrating the *WTForms library*, providing validation, CSRF protection, and file upload support.
  > A CSRF token (Cross-Site Request Forgery token) is a secret, unique value added to a form to make sure the request is coming from the real user, not a malicious website.

  Install Packages: `pip install flask-wtf email_validator`

  ```bash
  # form.py
  from flask_wtf import FlaskForm
  from wtforms import StringField, PasswordField, SubmitField
  from wtforms.validators import DataRequired, Email, Length

  class RegistrationForm(FlaskForm): # Inheritance
      # Form Fields with Labels & Validators
      name = StringField('Full Name', validators=[DataRequired(message='Name is required!')]) # custom error message
      email = StringField('Email', validators=[DataRequired(), Email(message='Invalid email address!!!')])
      password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=15)])    
      submit = SubmitField('Register')
  ```

  ```bash
  # app.py
  from form import RegistrationForm

  @app.route('/register', methods=['GET', 'POST'])
  def register():
      form = RegistrationForm() # Flask-WTF form instance

      # Checks whether the form was submitted via a POST request and if all its data passes validation that we defined.
      if form.validate_on_submit():
          name = form.name.data
          email = form.email.data

          flash(f'Thanks {name}, your registration was successful!', 'success')
          return redirect(url_for('success'))
      
      # If the form is not valid (either it's a GET request or validation failed), we render the registration template with the form instance, which will include error messages if validation failed.
      return render_template('register.html', form=form) # Passed form instance so the template can access and display the form fields, data, and errors.
  ```

  ```bash
  <!-- register.html -->
  <form action="/register" method="POST">
      <!-- Render CSRF token required for form validation -->
      {{ form.hidden_tag() }}

      <p>
          {{ form.name.label }}<br>
          {{ form.name(size=30) }}<br><br> <!-- name field width size -->
          {% for error in form.name.errors %}
              <span style="color: red;">{{ error }}</span><br><br>
          {% endfor %}

          {{ form.email.label }}<br>
          {{ form.email(size=30) }}<br><br>
          {% for error in form.email.errors %}
              <span style="color: red;">{{ error }}</span><br><br>
          {% endfor %}

          {{ form.password.label }}<br>
          {{ form.password(size=30) }}<br><br>
          {% for error in form.password.errors %}
              <span style="color: red;">{{ error }}</span><br><br>
          {% endfor %}
      </p>

      <p>{{ form.submit }}</p>
  </form>
  ```

## Application Structure and Blueprints
A Blueprint in Flask is a way to organize your app into smaller parts (modules) instead of writing everything in one file.

```bash
my_flask_app/
│
├── app/
│   ├── __init__.py        # create_app() and blueprint registration
│   ├── routes/
│   │   ├── __init__.py
│   │   └── auth.py        # auth blueprint (login/signup)
│   │
│   ├── models/            # database
│   │   ├── __init__.py
│   │
│   ├── templates/
│   │   ├── base.html      # base layout (Jinja2)
│   │   └── login.html
│   │
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   │   └── images/
│
├── run.py                 # entry point
├── requirements.txt
└── README.md
```

```bash
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='templates')

    app.config['SECRET_KEY'] = 'your_secret_key' # session/flash-messages
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./blueprints.db'

    db.init_app(app)

    # IMPORT AND REGISTER ALL BLUEPRINTS
    from app.blueprints.core.routes import core
    from app.blueprints.todos.routes import todos
    from app.blueprints.people.routes import people

    app.register_blueprint(core, url_prefix='/') # the core blueprint has all the routes that don't need a prefix, so we can just use '/' as the prefix for that one
    app.register_blueprint(todos, url_prefix='/todos') # plug that module into your app, with a prefix for all routes in that blueprint
    app.register_blueprint(people, url_prefix='/people')

    migrate = Migrate(app, db)

    return app
```

```bash
# app/blueprints/todos/models.py
from app import db

class Todo(db.Model):
    __tablename__ = 'todos'

    tid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    done = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Todo {self.title}, Done: {self.done}>'

    def get_id(self):
        return self.tid
```

```bash
# app/blueprints/todos/routes.py
from flask import Flask, Blueprint, render_template, request, redirect, url_for
from app import db
from app.blueprints.todos.models import Todo

# 'todos' is the name of the blueprint, and __name__ is the import name of the blueprint package
todos = Blueprint('todos', __name__, template_folder='templates')

@todos.route('/')
def index():
    todos = Todo.query.all()
    return render_template('todos/index.html', todos=todos)

@todos.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        done = True if 'done' in request.form.keys() else False

        description = description if description != '' else None

        new_todo = Todo(title=title, description=description, done=done)
        db.session.add(new_todo)
        db.session.commit()

        return redirect(url_for('todos.index'))

    return render_template('todos/add.html')
```

```bash
# app/blueprints/todos/__init__.py
# app/blueprints/todos/templates
```

```bash
# run.py
from app import create_app

app = create_app()

# Run this file when it's executed directly, not when it's imported as a module.
if __name__ == '__main__':
    app.run(debug=True)
```

## SQLite and SQLAlchemy ORM Data Management
- **SQLite** is a lightweight, serverless RDBMS. It stores data in a single file and uses raw SQL for interactions. It is built-in in python, and used for small to medium flask app.
  ```bash
  import sqlite3

  conn = sqlite3.connect('website.db') # create or connect to a database
  cursor = conn.cursor() # create a cursor object to execute SQL commands

  # create table
  cursor.execute('''
          CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE)
  ''')

  conn.commit() # commit the changes to the database
  conn.close() # close the connection to the database
  ```
- **SQLAlchemy** is a Python library (specifically an Object-Relational Mapper or ORM) that sits on top of databases like SQLite. It allows you to interact with data using Python classes and objects instead of raw SQL strings.
  - (DB Table, Python Class), (Row, Object), (Column, Attribute), (Cursor, Session)
  - `pip install flask-sqlalchemy flask-migrate`

  Before running the app, we should run these commands to create the Database. Last two commands should be run everytime when DB shcmea changes:
  1. `python -m flask --app run.py db init`
  2. `python -m flask --app run.py db migrate -m "initial"`
  3. `python -m flask --app run.py db upgrade`

  DB Shell: `python -m sqlite3 website.db`

  IMPORT
  - App(__ init __.py) import Routes
  - Routes import Models
  - Models import db from App(__ init __.py)
  
  ```bash
  # __init__.py
  from flask import Flask
  from flask_sqlalchemy import SQLAlchemy
  from flask_migrate import Migrate

  db = SQLAlchemy()

  # Factory Pattern
  def create_app():
      app = Flask(__name__)

      app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./website.db' # Set the URI for our SQLite database
      # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Disable tracking modifications of objects and emitting signals
      db.init_app(app) # Connect SQLAlchemy db object to our Flask app

      # IMPORTS (avoid circular imports)
      from .routes import register_routes
      register_routes(app, db) # Register the routes for our Flask app

      migrate = Migrate(app, db) # Enable database migrations for our Flask app
      
      return app
  ```

  ```bash
  # models.py
  from . import db

  class Users(db.Model):
      __tablename__ = 'users' # Optional: specify the name of the database table (defaults to 'users' if not provided)
      
      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.String(40), nullable=False)
      email = db.Column(db.String(50), unique=True, nullable=False)
      job = db.Column(db.Text, nullable=True)
      
      # Relationship to Post model (one-to-many relationship)
      # posts = db.relationship('Post', backref='author', lazy=True) # backref creates automatic reverse relationship from Post to User

      # Representation method for debugging and testing purposes
      def __repr__(self):
          return f'Users(id={self.id}, name="{self.name}", email="{self.email}", job="{self.job}")'
  ```

  ```bash
  # routes.py
  from flask import render_template, request
  from .models import Users

  # This function registers the routes for the Flask application. It takes the app and db as arguments.
  def register_routes(app, db):
      @app.route('/', methods=['GET', 'POST'])
      def index():
          if request.method == 'GET':
              users = Users.query.all() # fetch all rows from the User table (SQLAlchemy)
              # return str(user)
              return render_template('index.html', users=users)
          
          elif request.method == 'POST':
              name = request.form.get('name')
              email = request.form.get('email')
              job = request.form.get('job')

              if not name or not email:
                  return 'Name and email are required fields!', 400
              
              existing_user = Users.query.filter_by(email=email).first()
              if existing_user:
                  return 'User with this email already exists!', 400

              new_user = Users(name=name, email=email, job=job) # create a new User object
              db.session.add(new_user) # add the new user to the session
              db.session.commit() # commit the session to save the new user to the database
              
              users = Users.query.all()
              return render_template('index.html', users=users)
          
      @app.route('/delete/<int:user_id>', methods=['DELETE'])
      def delete(user_id):
          Users.query.filter(Users.id == user_id).delete()
          db.session.commit()
          
          users = Users.query.all()
          return render_template('index.html', users=users)

      @app.route('/details/<int:user_id>')
      def details(user_id):
          user = Users.query.get(user_id) # fetch a single user by their primary key

          if not user:
              return 'User not found!', 404
          
          return render_template('details.html', user=user)
  ```

Auth System: `pip install flask-login flask-bcrypt`

## Remaining
- MySQL with flask
- env


```bash
# pip install python-dotenv
from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if __name__ == "__main__":
    app.run(debug=True)

# SECRET_KEY=123456
```