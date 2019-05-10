from wtforms import Form, StringField, TextAreaField, PasswordField, SelectField, validators
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from CourseBuilder import app
#Config SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:superstar007@localhost/coursebuilder'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

class Register_db(db.Model):
    __tablename__='register'
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    username = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
    is_auth = db.Column(db.Integer,default=0)
    instructor = db.Column(db.String,default=0)
    profile_image = db.Column(db.String,default="null")
    
    def __init__(self,username,email,password,is_auth,instructor,profile_image):
        self.username = username
        self.email = email
        self.password = password
        self.is_auth = is_auth
        self.instructor = instructor
        self.profile_image=profile_image

class editprofile_db(db.Model):
    __tablename__='register'
    __table_args__ = {'extend_existing': True}
    username=db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)

    def __init__(self,username,email,password):
        self.username=username
        self.email = email
        self.password = password

class login_db(db.Model):
    __tablename__='register'
    __table_args__ = {'extend_existing': True}
    username = db.Column(db.String)
    password = db.Column(db.String)
    instructor = db.Column(db.Integer,default=0)
    is_auth = db.Column(db.Integer,default=0)
    profile_image=db.Column(db.String)

    def __init__(self,username,password):
        self.username=username
        self.password=password

class enroll_courses_db(db.Model):
    __tablename__='enr_crs'
    sno = db.Column(db.Integer,primary_key=True,autoincrement=True)
    student_id = db.Column(db.String)
    courses = db.Column(db.String,default='null')

    def __init__(self,student_id,courses):
        self.student_id = student_id
        self.courses = courses