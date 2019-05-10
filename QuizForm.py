from wtforms import Form, StringField, TextAreaField, PasswordField, SelectField, validators
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
import app
#Config SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:superstar007@localhost/coursebuilder'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

class QuizForm(Form):
    """description of class"""
    course_select = SelectField('course_select')
    question = TextAreaField('', [validators.Length(min=4, max=450)])
    title = TextAreaField('title', [validators.Length(min=4, max=450)])
    option_1 = StringField('option_1',[validators.Length(min=4, max=250)])
    option_2 = StringField('option_2',[validators.Length(min=4, max=250)])
    option_3 = StringField('option_3',[validators.Length(min=4, max=250)])
    option_4 = StringField('option_4',[validators.Length(min=4, max=250)])
    correct = StringField('correct',[validators.Length(min=4, max=250)])

class quiz_db(db.Model):
    __tablename__='quiz'
    question_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    course_id = db.Column(db.String)
    question = db.Column(db.String)
    opt1 = db.Column(db.String)
    opt2 = db.Column(db.String)
    opt3 = db.Column(db.String)
    opt4 = db.Column(db.String)
    correct = db.Column(db.String)
    title = db.Column(db.String)
    def __init__(self,course_id,question,opt1,opt2,opt3,opt4,correct,title):
        self.question = question
        self.course_id=course_id
        self.opt1=opt1
        self.opt2=opt2
        self.opt3=opt3
        self.opt4=opt4
        self.correct=correct
        self.title=title

class quiz_results(db.Model):
    __tablename__='quiz_results'
    sno = db.Column(db.Integer,primary_key=True,autoincrement=True)
    stud_id = db.Column(db.Integer)
    score = db.Column(db.Integer,default=0)
    title = db.Column(db.String)

    def __init__(self,stud_id,score,title):
        self.stud_id=stud_id
        self.score=score
        self.title=title

class quiz_display_db(db.Model):
    __tablename__='quiz_display'
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    student_name = db.Column(db.String)
    course = db.Column(db.String)
    question = db.Column(db.String)
    correct = db.Column(db.String)
    given = db.Column(db.String)

    def __init__(self,student_name,course,question,correct,given):
        self.student_name=student_name
        self.course = course
        self.question=question
        self.correct=correct
        self.given=given
