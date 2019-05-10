"""
Routes and views for the flask application.
"""
#from RegisterForm import RegisterForm, Register_db,editprofile_db, login_db, enroll_courses_db
#from Edit_Profile import Edit_Profile
#from QuizForm import QuizForm,quiz_db,quiz_results,quiz_display_db
from datetime import datetime, timedelta
from flask_wtf import Form
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from wtforms import Form, StringField, TextAreaField, PasswordField, SelectField, validators
from flask_wtf.file import FileField, FileAllowed, FileRequired
from passlib.hash import sha256_crypt
from functools import wraps
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging,flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from flask_uploads import UploadSet, configure_uploads, IMAGES
from werkzeug import secure_filename
from sqlalchemy import *
import os, smtplib, json,csv
from os import environ
app = Flask(__name__)
#Config SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:superstar007@localhost/coursebuilder'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

app.no_of_chance = 4
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = '../CourseBuilder/CourseBuilder/static/profile_pictures'
configure_uploads(app, photos)

UPLOAD_FOLDER = 'static\\file_uploads\\'
FILE_UPLOAD_FOLDER = '../CourseBuilder/CourseBuilder/static/file_uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
db = SQLAlchemy(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FILE_UPLOAD_FOLDER']=FILE_UPLOAD_FOLDER
list_courses=[]

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template('index.html') 

@app.route('/instructor')
@login_required
def instructor(): 
    engine = create_engine('mysql://root:superstar007@localhost/coursebuilder')
    connection = engine.raw_connection()
    stud = Register_db.query.all()
    crs = addlesson_db.query.all()
    lect=lesson_db.query.all()
    count=0
    act=0
    for crss in crs:
        count = count+1
    try:
        cursor = connection.cursor()
        cursor.callproc("GET_REGISTERED_USERS")
        results = cursor.fetchall()
        cursor.close()
        connection.commit()
        
    finally:
        connection.close()

    return render_template('instructor.html',results=results,stud = stud,crs=crs,count=count,act=act,lect=lect)

@app.route('/logout')
@login_required
def logout():
    """Renders the home page."""
    username = session['username']
    data=login_db.query.filter_by(username=username).first()
    if session.get('logged_in'):
        session.pop('username')
        session['logged_in']=False
        data.is_auth=0
        db.session.commit()
        current_user=False
        logout_user()
        session.clear()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    engine = create_engine('mysql://root:superstar007@localhost/coursebuilder')
    connection = engine.raw_connection()
    if request.method=="GET" and current_user==False:
        return redirect(url_for('login'))
    username = session['username']
    data=login_db.query.filter_by(username=username).first()
    anno = announcement_db.query.all()
    if current_user.is_active:
        global list_courses
        id = data.id
        courses = addlesson_db.query.all()
        for course in courses:
            if course.availability==1:
                list_courses.append(course.name)
        enrolled = enroll_courses_db.query.filter_by(student_id=id).all()
        try:
            cursor = connection.cursor()
            cursor.callproc("GET_WORD_USAGE")
            words = cursor.fetchone()
            cursor.close()
            cursor = connection.cursor()
            cursor.callproc("GET_QUOTES")
            quotes=cursor.fetchone()
            cursor.close()
            cursor = connection.cursor()
            cursor.callproc("GET_QUIZ")
            quiz=cursor.fetchall()
            cursor.close()
            cursor = connection.cursor()
            cursor.callproc('DID_YOU_KNOW')
            dyk = cursor.fetchone()
            cursor.close()
            connection.commit()
        finally:
            connection.close()
        return render_template('dashboard.html',current_user=True,list_courses=list_courses,courses=courses,instructor=data.instructor,img=data.profile_image,name=data.username,words=words,quotes=quotes,enrolled=enrolled,quiz=quiz,dyk=dyk,anno=anno)
    else:
        return redirect(url_for('login'))

class AddLessonForm(Form):
    Title = StringField('Title', [validators.Length(min=4, max=50)])
    Video_Url = StringField('Upload Video',[validators.Length(min=4, max=250)])
    course_select = SelectField('course_select')
    content = TextAreaField("",[validators.Length(min=30)])

@app.route('/add_lesson',methods=['POST','GET'])
@login_required
def add_lesson():
    form = AddLessonForm(request.form)
    courses = addlesson_db.query.all()
    if request.method=="POST":
        Title = form.Title.data
        Video_Url = form.Video_Url.data

        name = form.course_select.data
        content = form.content.data
        name=str(name)
        coursess = addlesson_db.query.filter_by(name=name).first()
        addtolesson = lesson_db(name,Video_Url,Title,content)
        db.session.add(addtolesson)
        db.session.commit()
        flash(Title+" "+"Added Successfully, you can continue to add further lessons!")
        return render_template('add_lesson.html',form=form,courses=courses)
    return render_template('add_lesson.html',form=form,courses=courses)

@app.route('/register',methods=['POST','GET'])
def register():
    "Renders the registration page"
    form = RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        username = form.username.data
        email = form.email.data
        data = Register_db.query.filter_by(email=email).first()
        if data==None:
            password = sha256_crypt.encrypt(str(form.password.data))
            is_auth=0
            new_user = Register_db(username,email,password,is_auth,0,'guy-6.jpg')
            try:
                session['email']=email
                db.session.add(new_user)
                db.session.commit()
            except:
                
                return render_template('register.html')
            enroll_courses(email)
            return redirect(url_for('login'))
        else:
            flash("Email/Username already exists!")
            return render_template('register.html')
    else:
        return render_template('register.html')

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        user = login_db(username,password)
        usr = User.query.filter_by(username=username).first()
        data=login_db.query.filter_by(username=username).first()
        if data==None:
            flash("Please try again")
            return render_template('login.html')
        if sha256_crypt.verify(password,data.password):
            session['logged_in'] = True
            session['id'] = data.id
            session['username'] = username
            session['email'] = data.email
            session['password']=data.password
            session['image']=data.profile_image
            data.is_auth=1
            db.session.commit()
            current_user.authenticated = True
            login_user(usr)
            return redirect(url_for('dashboard'))
        else:
            flash("Please try again")
            return render_template('login.html')
    return render_template('login.html')


@app.route('/edit_profile',methods=['POST','GET'])
@login_required
def edit_profile():
    engine = create_engine('mysql://root:superstar007@localhost/coursebuilder')
    connection = engine.raw_connection()
    form = Edit_Profile(request.form)
    username = session['username']
    email = session['email']
    passw = session['password']

    result=editprofile_db.query.filter_by(username=username).first()
    if request.method=='POST':
        new_name=form.username.data
        new_email = form.email.data
        new_pass = form.password.data
        passwo = sha256_crypt.encrypt(new_pass)
        session['username'] = new_name

        #result.username = new_name
        #result.email = new_email
        #result.password = sha256_crypt.encrypt(new_pass)
        #db.session.commit()
        cursor = connection.cursor()
        if new_pass=="":

            cursor.execute ("UPDATE register SET username=%s, email=%s WHERE email=%s",(new_name, new_email, email))
        else:

            cursor.execute ("UPDATE register SET username=%s, email=%s, password=%s WHERE email=%s",(new_name, new_email,passwo, email))
        cursor.close()
        connection.commit()
        return redirect(url_for('dashboard'))
    else:
        form.username.data = result.username
        form.email.data = result.email
        form.password.data = passw
        return render_template('edit_profile.html',form=form)

@app.route('/mycourses/<int:cid>')
@login_required
def mycourse(cid):
    stud_id = session['id']
    cs = addlesson_db.query.filter_by(course_id=cid).first()
    cname = cs.name
    ers = enroll_courses_db.query.filter_by(student_id=stud_id).all()
    enrolled = []
    for e in ers:
        enrolled.append(e.courses)
    if cname in enrolled:

        return redirect(url_for('mycourses'))
    else:
        add_ers = enroll_courses_db(stud_id,cname)

        db.session.add(add_ers)
        db.session.commit()
        return redirect(url_for('mycourses'))

@app.route('/mycourses')
@login_required
def mycourses():
    if request.method=="GET" and not current_user.is_authenticated:
        return redirect(url_for('login'))
    stud_id = session['id']

    courses = addlesson_db.query.all()
    enrolled = enroll_courses_db.query.filter_by(student_id=stud_id).all()

    list_crs = []
    for crs in enrolled:
        if crs.courses in list_crs:
            continue
        else:
            list_crs.append(crs.courses)

    return render_template('mycourses.html',data=list_crs)

@app.route('/display/<string:title>')
@login_required
def display(title):
    stud_id = session['id']
    data = lesson_db.query.filter_by(title=title).first()
    ers = enroll_courses_db.query.filter_by(student_id=stud_id).all()
    lessons = lesson_db.query.filter_by(course_id=data.course_id).all()
    return render_template('display.html',data=data,lessons=lessons,ers=ers)

@app.route('/addlesson',methods=['POST','GET'])
def addlesson():
    courses = addlesson_db.query.all()
    if request.method=='POST':
        return render_template('/dashboard')
    else:
        return render_template('add_lesson.html',courses=courses)

class addlesson_db(db.Model):
    __tablename__='courses'
    course_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    name = db.Column(db.String)
    overview = db.Column(db.String)
    prerequisites = db.Column(db.String)
    files = db.Column(db.String)
    availability = db.Column(db.Integer,default=0)

    def __init__(self,name,overview,prerequisites,files,availability):
        self.name = name
        self.overview = overview
        self.prerequisites=prerequisites
        self.files=files
        self.availability = availability

@app.route('/takecourse/<string:c_id>')
@login_required
def takecourse(c_id):
    course_id=c_id.replace('_',' ')
    stud_id = session['id']
    lessons = lesson_db.query.filter_by(course_id=course_id).all()
    ers = enroll_courses_db.query.filter_by(student_id=stud_id).all()
    courses = addlesson_db.query.filter_by(name=c_id).first()
    crs = addlesson_db.query.all()
    interview = lesson_db.query.filter_by(title="Interview").first()
    return render_template('takecourse.html',lessons=lessons,course_id=course_id,overview=courses.overview,prerequisites=courses.prerequisites,interview=interview,courses=crs,ers=ers)

class lesson_db(db.Model):
    __tablename__='lessons'
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    course_id = db.Column(db.String)
    video_url = db.Column(db.String)
    title = db.Column(db.String)
    content = db.Column(db.String)

    def __init__(self,course_id,video_url,title,content):
        self.course_id=course_id
        self.video_url=video_url
        self.title=title
        self.content=content

#This is used to insert into enrolled_courses table
def enroll_courses(email):
    datas = Register_db.query.filter_by(email=email).first()
    enr = enroll_courses_db(email,'null')
    db.session.add(enr)
    db.session.commit()

@app.route('/lectures',methods=['GET','POST'])
def lectures():
    lect=lesson_db.query.all()
    return render_template('edit_lesson.html',lect=lect)

@app.route('/updatelessons/<int:id>',methods=['POST','GET'])
def updatelessons(id):
    dataset=lesson_db.query.filter_by(id=id).first()
    id = dataset.id
    courses = addlesson_db.query.all()
    form=AddLessonForm(request.form)
    form.course_select.data = dataset.course_id
    form.Title.data = dataset.title
    form.Video_Url.data=dataset.video_url
    form.content.data=dataset.content
    if request.method=="POST":
        Course_id = form.course_select.data
        Title = request.form['Title']
        Video_Url= request.form['Video_Url']
        Content= request.form['content']
        dataset.title=Title
        dataset.video_url=Video_Url
        dataset.content=Content
        db.session.commit()
        return redirect(url_for('instructor'))
    return render_template('update.html', form=form,id=id,courses=courses)

@app.route('/deletelesson/<string:title>', methods=['POST','GET'])
def deletelesson(title):
    data=lesson_db.query.filter_by(title=title).first()
    db.session.delete(data)
    db.session.commit()
    return redirect(url_for('lectures'))

@app.route('/ForgotPassword',methods=['POST','GET'])
def forgotpassword():
    if request.method=='POST':
        fromaddr = 'kamesh.mskr@gmail.com'
        toaddrs  = request.form['email']
        msg = 'Your password is - P@$Sw0rd, please reset it.'
        username = 'kamesh.mskr@gmail.com'
        password = '$uperSt@r007'
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(username,password)
        server.sendmail(fromaddr, toaddrs, msg)
        server.quit()
        data = Register_db.query.filter_by(email=toaddrs).first()
        data.password = sha256_crypt.encrypt("P@$Sw0rd")
        db.session.commit()
        return redirect(url_for('login'))
    else:
        return render_template('ForgotPassword.html')
   
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    try:
        engine = create_engine('mysql://root:superstar007@localhost/coursebuilder')
        connection = engine.raw_connection()
        data = Register_db.query.filter_by(id=session['id']).first()
        idman = session['id']
        if request.method == 'POST' and 'photos' in request.files:
            for f in request.files.getlist('photos'):
                f.save(os.path.join(app.config['UPLOADED_PHOTOS_DEST'], secure_filename(f.filename)))
                name = str(f.filename)
                #data.profile_image=name
                #db.session.commit()
                cursor = connection.cursor()
                cursor.execute ("UPDATE register SET profile_image=%s WHERE email=%s",(name, data.email))
                cursor.close()
                connection.commit()
                session['image']=name
            return redirect(url_for('dashboard'))
        return redirect(url_for('dashboard'))
    except:
        return render_template('index.html')

@app.route('/quiz',methods=['POST','GET'])
def quiz():
    courses = addlesson_db.query.all()
    form = QuizForm(request.form)
    if request.method=="POST":
        title = form.title.data
        course_select=form.course_select.data
        question = form.question.data
        option_1 = form.option_1.data
        option_2 = form.option_2.data
        option_3 = form.option_3.data
        option_4 = form.option_4.data
        correct = form.correct.data
        quiz = quiz_db(course_select,question,option_1,option_2,option_3,option_4,correct,title)
        db.session.add(quiz)
        db.session.commit()
        return redirect(url_for('instructor'))
    else:
        return render_template('quiz.html',form=form,courses=courses)

@app.route('/takequiz/<string:cid>',methods=['POST','GET'])
@login_required
def takequiz(cid):
    count=int(0)
    questionsdb = quiz_db.query.filter_by(title=cid).all()
    i=int(0)
    list_ques=[]
    options_list=[]
    quiz_list=[]
    correct_list={}
    questions_quiz={}
    id = session['id']
    while(i<len(questionsdb)):
        questions_quiz.update({ count : { "question" : questionsdb[i].question,"options": [questionsdb[i].opt1,questionsdb[i].opt2,questionsdb[i].opt3,questionsdb[i].opt4], "answer" : questionsdb[i].correct}})
        list_ques.append(questionsdb[i].question)
        options_list.append(questionsdb[i].opt1)
        options_list.append(questionsdb[i].opt2)
        options_list.append(questionsdb[i].opt3)
        options_list.append(questionsdb[i].opt4)
        list_ques.append(options_list)
        options_ques=[]
        correct_list[questionsdb[i].question]=questionsdb[i].correct
        i=i+1
        quiz_list.append(list_ques)
        count=count+1
    length = len(list_ques)
    attempt = quiz_results.query.filter_by(stud_id=session['id'],title=cid).first()
    if attempt==None:

        if request.method=="POST":
            quiz_results_show1=[]
            quiz_results_show2=[]
            if 'question' in session:
                entered_answer = request.form.get('answer','')

                vry = questions_quiz.get(session["question"],False)

                vvv = int(session["question"])

                if questions_quiz.get(vvv,False):

                    v = int(session["question"])
                    if entered_answer!= questions_quiz[v]["answer"]:

                        app.no_of_chance -= 1
                        #flash("Oops..Wrong Answer. Try again", "error")
                        add_into_quiz = quiz_display_db(session['username'],cid,questions_quiz[v]["question"],questions_quiz[v]["answer"],entered_answer)
                        db.session.add(add_into_quiz)
                        db.session.commit()
                        session["question"] = str(int(session["question"])+1)
                    else:
                        if app.no_of_chance == 4:
                            mark = 4
                        elif app.no_of_chance == 3:
                            mark = 2
                        else:
                            mark = 1
                        session["mark"] += mark
                        app.no_of_chance = 4
                        add_into_quiz = quiz_display_db(session['username'],cid,questions_quiz[v]["question"],questions_quiz[v]["answer"],entered_answer)
                        db.session.add(add_into_quiz)
                        db.session.commit()
                        session["question"] = str(int(session["question"])+1)
                    xxx=int(session["question"])
                    if xxx in questions_quiz:

                        return render_template("takequiz.html",question=questions_quiz[xxx]["question"],question_number=xxx,options=questions_quiz[xxx]["options"],score = session["mark"],cid=cid,count=count-1)
                    else:
                        obj = quiz_results(id,session['mark'],cid)
                        db.session.add(obj)
                        db.session.commit()
                        session.pop("question")  
                        return redirect(url_for('scoredisp',score=session['mark'],course=cid))
        if "question" not in session:

            session["question"] = "1"
            session["mark"] = 0
            sq1 = int(session["question"])
            return render_template("takequiz.html",question=questions_quiz[sq1]["question"],question_number=sq1,options=questions_quiz[sq1]["options"],score = session["mark"],cid=cid,count = count-1)
        else:

            if session["question"] not in questions_quiz:

                #return render_template("score.html",score = session["mark"])
                sq1 = int(session["question"])
            return render_template("takequiz.html",question=questions_quiz[sq1]["question"],question_number=sq1,options=questions_quiz[sq1]["options"],score = session["mark"],cid=cid)
    else: 

        if attempt.title==cid:
            return render_template("score.html", score = attempt.score)
        else:
            return render_template("takequiz.html",question=questions_quiz[sq1]["question"],question_number=sq1,options=questions_quiz[sq1]["options"],score = session["mark"],cid=cid)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/quizres')
@login_required
def quizres():
    engine = create_engine('mysql://root:superstar007@localhost/coursebuilder')
    connection = engine.raw_connection()
    cursor = connection.cursor()
    cursor.callproc("GET_QUIZ_RESULTS")
    quiz_results = cursor.fetchall()
    cursor.close()
    connection.commit()
    return render_template('quizres.html',quiz_results=quiz_results)

@app.route('/addcourse',methods=['POST','GET'])
@login_required
def addcourse():
    form = AddCourseForm(request.form)
    course = addlesson_db.query.all()
    if request.method=="POST":
        name = form.name.data
        overview = form.overview.data
        prerequisites = form.prerequisites.data
        availability = form.availability.data
        i = int(availability)
        less = addlesson_db(name,overview,prerequisites,'null',i)
        db.session.add(less)
        db.session.commit()
        return redirect(url_for('instructor'))
    return render_template('addcourse.html',form=form,course=course)

@app.route('/updatecourse',methods=['POST','GET'])
@login_required
def updatecourse():
    form = AddCourseForm(request.form)
    courses = addlesson_db.query.all()
    if request.method=="POST":
        name = request.form['course_select']
        availability = form.availability.data
        course = addlesson_db.query.filter_by(name=name).first()
        i = int(availability)
        course.availability=i
        db.session.commit()
        return redirect(url_for('instructor'))
    return render_template('updatecourse.html',form=form,courses=courses)

class AddCourseForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=25)])
    overview = TextAreaField('OverView', [validators.Length(min=6, max=50)])
    prerequisites = TextAreaField('Prerequisites',[validators.Length(min=6,max=50)])
    availability = SelectField('Availability',choices = [(1, 'YES'), (0, 'NO')])

class AddResources(Form):
    name = SelectField('Name', choices = [('WN', 'Whats New'), ('IS', 'Inspirational Story')])
    title = TextAreaField('Title', [validators.Length(min=6, max=50)])
    story = TextAreaField('Story',[validators.Length(min=6)])

@app.route('/addresources',methods=["POST","GET"])
@login_required
def addresources():
    form = AddResources(request.form)
    if request.method=="POST":
        name = form.name.data
        title = form.title.data
        story = form.story.data
        resource = Resource_db(name,title,story)
        db.session.add(resource)
        db.session.commit()
        return redirect(url_for('instructor'))
    return render_template('resources.html',form=form)

@app.route('/displayres/<string:id>',methods=["POST","GET"])
@login_required
def displayres(id):
    reso = Resource_db.query.filter_by(name=id).order_by("id desc").first()
    return render_template("display_res.html",reso =reso)
    #return redirect(url_for('dashboard'))

class Resource_db(db.Model):
    __tablename__="story"
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    name = db.Column(db.String)
    title = db.Column(db.String)
    story = db.Column(db.String)

    def __init__(self,name,title,story):
        self.name = name
        self.title = title
        self.story = story

@app.route('/scoredisp/<score>/<course>')
def scoredisp(score,course):
    quiz_results_show= quiz_display_db.query.filter_by(student_name=session["username"],course=course).all()
    print("quiz_results_show",quiz_results_show)
    return render_template("score.html",quiz_results_show=quiz_results_show, score = score)

@app.route('/uploadfiles',methods=['POST','GET'])
def uploadfiles():
    print("UPLOAD FILES")
    
    if request.method == 'POST':
        cname = request.form['course_select']
        dd = addlesson_db.query.filter_by(name=cname).first()
        # check if the post request has the file part
        print("Entered POST")
        if 'uploadfile' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['uploadfile']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            dd.files = filename
            db.session.commit()
            file.save(os.path.join(app.config['FILE_UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploadfiles',
                                    filename=filename))
    return redirect(url_for('instructor'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/downloads/<string:name>',methods=['GET','POST'])
def download(name):
    dd = addlesson_db.query.filter_by(name=name).first()
    print(dd.files)
    uploads = os.path.join(app.config['UPLOAD_FOLDER'], dd.files)
    print("UPLOADS",uploads)
    #send_from_directory(directory=uploads, filename=dd.files)
    return send_file(uploads,dd.files,as_attachment=True)

@app.route('/addadmin',methods=['POST','GET'])
def addadmin():
    engine = create_engine('mysql://root:superstar007@localhost/coursebuilder')
    connection = engine.raw_connection()
    if request.method=='POST':
        email = request.form['email']
        print('email',email)
        data = Register_db.query.filter_by(email=email).first()
        cursor = connection.cursor()
        i=1
        cursor.execute ("UPDATE register SET instructor=%s WHERE email=%s",(i, data.email))
        cursor.close()
        connection.commit()
        flash("Added Successfully!")
        return redirect(url_for('dashboard'))
    return render_template('addadmin.html')

@app.route('/announcement',methods=['POST','GET'])
def announcement():
    if request.method=='POST':
        announcement = request.form['annoucement']
        anno = announcement_db(announcement)
        db.session.add(anno)
        db.session.commit()
        flash('Posted successfully')
        return redirect(url_for('announcement'))
    return render_template('announcement.html')

class announcement_db(db.Model):
    __tablename__ = 'announcement'
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    message = db.Column(db.String)

    def __init__(self,message):
        self.message = message

class User(UserMixin, db.Model):
    __tablename__='register'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    username = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
	
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
    __table_args__ = {'extend_existing': True}
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
		
class Edit_Profile(Form):
    username=StringField('User Name',[validators.Length(min=4, max=25)])
    email = StringField('Email',[validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.DataRequired()])
		
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
		
class enroll_courses_db(db.Model):
    __tablename__='enr_crs'
    sno = db.Column(db.Integer,primary_key=True,autoincrement=True)
    student_id = db.Column(db.String)
    courses = db.Column(db.String,default='null')

    def __init__(self,student_id,courses):
        self.student_id = student_id
        self.courses = courses
	
if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    #app.debug=True
    app.secret_key='secret123'
    app.run(HOST, PORT)