from flask import Flask, render_template, redirect, url_for, request, flash,session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta,date
import calendar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sqlalchemy.sql import func
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy()
db.init_app(app)

base_dir=os.path.dirname(os.path.abspath(__file__))
static_dir=os.path.join(base_dir,'static')

class User(db.Model):
    __tablename__ = 'user'
    u_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email=db.Column(db.String(30),unique=True, nullable=False)
    password=db.Column(db.String(15),unique=True,nullable=False)
    std=db.Column(db.Integer,nullable=False)
    dob=db.Column(db.Date,nullable=False)
    admin=db.Column(db.Boolean, nullable=False, default=False)
    scores = db.relationship("Score", backref='user', lazy=True)


class Subject(db.Model):
    __tablename__ = 'subject'
    sub_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    sub_name = db.Column(db.String(20), unique=True, nullable=False)
    desc = db.Column(db.String(50))
    chapters = db.relationship("Chapter", backref='subject', lazy=True, cascade="all, delete")

class Chapter(db.Model):
    __tablename__ = 'chapter'
    chap_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    chap_name = db.Column(db.String(20), unique=True, nullable=False)
    desc = db.Column(db.String(50))
    sub_id = db.Column(db.Integer, db.ForeignKey("subject.sub_id", ondelete="CASCADE"), nullable=False)
    quizzes = db.relationship("Quiz", backref='chapter', lazy=True, cascade="all, delete")

class Quiz(db.Model):
    __tablename__ = 'quiz'
    quiz_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String(20), unique=True, nullable=False)
    date_quiz=db.Column(db.Date, nullable=False)
    time_dur=db.Column(db.Time, nullable=False)
    remarks = db.Column(db.String(50), nullable=False)
    chap_id = db.Column(db.Integer, db.ForeignKey("chapter.chap_id", ondelete="CASCADE"), nullable=False)    
    questions = db.relationship("Question", backref='quiz', lazy=True, cascade="all, delete")

class Question(db.Model):
    __tablename__ = 'question'
    q_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    q_title=db.Column(db.String(50),nullable=False)
    q_statement = db.Column(db.String(100), unique=True, nullable=False)
    opt_1 = db.Column(db.String(50),nullable=False)
    opt_2 = db.Column(db.String(50),nullable=False)
    opt_3 = db.Column(db.String(50),nullable=False)
    opt_4 = db.Column(db.String(50),nullable=False)
    c_opt = db.Column(db.Integer,nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.quiz_id", ondelete="CASCADE"), nullable=False)


class Score(db.Model):
    __tablename__ = 'score'
    s_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    date_taken=db.Column(db.Date, nullable=False)
    dur=db.Column(db.Time, nullable=False)
    score=db.Column(db.Integer, nullable=False)
    u_id = db.Column(db.Integer, db.ForeignKey("user.u_id", ondelete="CASCADE"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.quiz_id", ondelete="CASCADE"), nullable=False)
    c_q_ids = db.Column(db.Text, nullable=True)
    i_q_ids = db.Column(db.Text, nullable=True)
    u_ans = db.Column(db.Text, nullable=True) 

def plot_graph1():
    x=[name[0] for name in db.session.query(Subject.sub_name).all()]
    tot_q = db.session.query(
    Question.quiz_id,
    func.count(Question.q_id).label("count")
    ).group_by(Question.quiz_id).subquery()
    y=[db.session.query(func.max((Score.score * 100) / func.coalesce(tot_q.c.count, 1)))
       .join(Quiz, Score.quiz_id == Quiz.quiz_id)
       .join(tot_q, Quiz.quiz_id == tot_q.c.quiz_id)
        .join(Chapter, Quiz.chap_id == Chapter.chap_id)
        .join(Subject, Chapter.sub_id == Subject.sub_id)
        .filter(Subject.sub_name == x[i])
        .scalar() or 0
        for i in range(len(x))]
    
    plt.figure(figsize=(15,10))
    plt.bar(x,y,color='red')
    plt.xlabel("Subjects", fontsize=16, fontweight='bold')
    plt.ylabel("Maximum Score Percentage", fontsize=16, fontweight='bold')
    plt.title("Subject wise top scores", fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, fontsize=14, fontweight='bold')
    plt.yticks(fontsize=14, fontweight='bold')
    plt.savefig(os.path.join(static_dir, 'bar1.png'), dpi=300, bbox_inches='tight')
    plt.close()
    return 

def plot_graph2():
    subjc = (
        db.session.query(Subject.sub_name, func.count(func.distinct(Score.u_id)))
        .join(Chapter, Subject.sub_id == Chapter.sub_id)
        .join(Quiz, Chapter.chap_id == Quiz.chap_id)
        .join(Score, Quiz.quiz_id == Score.quiz_id)
        .group_by(Subject.sub_name)
        .all()
    )
    x = [name[0] for name in subjc]
    y= [name[1] for name in subjc]
    plt.figure(figsize=(10,10))
    plt.pie(y,labels=x,autopct='%1.1f%%',colors=plt.cm.Paired.colors,startangle=140, textprops={'fontsize': 14, 'fontweight': 'bold'})
    plt.title("Subject wise user attempts", fontsize=16, fontweight='bold')
    plt.axis('equal')
    plt.savefig(os.path.join(static_dir, 'pie1.png'), dpi=300, bbox_inches='tight')
    plt.close()
    return

def plot_graph3(user_id):
    graph1=(
        db.session.query(Subject.sub_name,func.count(Score.quiz_id))
                         .join(Chapter, Subject.sub_id==Chapter.sub_id)
                         .join(Quiz, Chapter.chap_id==Quiz.chap_id)
                         .join(Score, Quiz.quiz_id==Score.quiz_id)
                         .join(User, Score.u_id==User.u_id)
                         .filter(User.u_id==user_id)
                         .group_by(Subject.sub_name)
                        .all()
    )
    if not graph1:
        flash("User did not attempt any quiz!","warning")
        if os.path.exists(os.path.join(static_dir, 'bar2.png')):
            os.remove(os.path.join(static_dir, 'bar2.png'))
        return
    x=[name[0] for name in graph1]
    y=[name[1] for name in graph1]
    plt.figure(figsize=(10,10))
    plt.bar(x,y,color='skyblue')
    plt.xlabel("Subjects", fontsize=16, fontweight='bold')
    plt.ylabel("Quiz attempts", fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, fontsize=14, fontweight='bold')
    plt.yticks(fontsize=14, fontweight='bold')
    plt.title("Subject wise no. of quizzes", fontsize=16, fontweight='bold')
    plt.savefig(os.path.join(static_dir, 'bar2.png'), dpi=300, bbox_inches='tight')
    plt.close()
    return 

def plot_graph4(user_id):
    gr2=(db.session.query(func.extract('month',Score.date_taken),func.count(Score.quiz_id))
         .join(User,Score.u_id==User.u_id)
         .filter(User.u_id==user_id)
         .group_by(func.extract('month',Score.date_taken))
         .all()
         )
    if not gr2:
        if os.path.exists(os.path.join(static_dir, 'pie2.png')):
            os.remove(os.path.join(static_dir, 'pie2.png'))
        return
    x=[calendar.month_abbr[name[0]] for name in gr2]
    y=[name[1] for name in gr2]
    plt.figure(figsize=(10,10))
    plt.pie(y,labels=x,autopct='%1.1f%%',colors=plt.cm.Paired.colors,startangle=140, textprops={'fontsize': 14, 'fontweight': 'bold'})
    plt.title("Month wise no. of quizzes attempted", fontsize=16, fontweight='bold')
    plt.axis('equal')
    plt.savefig(os.path.join(static_dir, 'pie2.png'), dpi=300, bbox_inches='tight')
    plt.close()
    return

@app.before_request
def create_tables():
    db.create_all()
    if not User.query.filter_by(email="Admin12@gmail.com").first():
        admin=User(name="Admin", email="Admin12@gmail.com", password=generate_password_hash("Silvia06@10"), std=0, dob=datetime.strptime("2006-06-01", "%Y-%m-%d").date(),admin=True)
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def start():
    return render_template('login.html')

@app.route('/clear_flash_messages', methods=['POST'])
def clear_flash_messages():
    session.pop('_flashes', None) 
    return '', 204 

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method=='POST':
        n=request.form.get('name')
        e=request.form.get('email')
        p=request.form.get('password')
        s=request.form.get('std')
        dat=request.form.get('dob')
        if not e or not p or not n or not s or not dat:
            flash("All fields are required!", "danger")
        else:
            e_user=User.query.filter_by(email=e).first()
            if e_user:
                flash("User already registered!","warning")
                return redirect(url_for('register'))
            else:
                h_pwd=generate_password_hash(p)
                d_date=datetime.strptime(dat,"%Y-%m-%d").date()

                new=User(name=n, email=e, password=h_pwd,std=s, dob=d_date, admin=False)
                try:
                    db.session.add(new)
                    db.session.commit()
                    flash("Registered successfully!","success")
                    return redirect(url_for('login'))
                except Exception as e:
                    db.session.rollback()
                    flash(f"{str(e)}")
    return render_template('registration.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        e=request.form.get('email')
        p=request.form.get('password')
        if not e or not p:
            flash("All fields are required!", "danger")
        else:
            user= User.query.filter_by(email=e).first()
            if user and check_password_hash(user.password,p):
                session['u_id'] = user.u_id
                flash("Login successful","success")

                if user.admin:
                    return redirect(url_for('admin_Dashboard'))
                else:
                    return redirect(url_for('user_Dashboard'))
            else:
                flash("Invalid password or login!","warning")
    return render_template('login.html')

@app.route('/logout')
def logout():
    u_id=session.get('u_id')
    admin_or_not=User.query.get(u_id).admin
    return render_template('logout.html', admin=admin_or_not)

@app.route('/admin_Dashboard')
def admin_Dashboard():
    sub=Subject.query.all()
    return render_template('adminDashboard.html',sub=sub)

@app.route('/quiz_Management')
def quiz_Management():
    quiz=Quiz.query.all()
    return render_template('quizManagement.html',quiz=quiz)

@app.route("/addSubject", methods=["GET","POST"])
def add_subject():
    if request.method=="POST":
        subn=request.form.get("sub_name")
        desc=request.form.get("desc")
        if not subn or not desc:
            flash("All fields are required!","danger")
            return redirect(url_for("add_subject"))
        else:
            esub=Subject.query.filter_by(sub_name=subn).first()
            if esub:
                flash("Subject already exists!","warning")
                return redirect(url_for("admin_Dashboard"))
            else:
                new_sub=Subject(sub_name=subn,desc=desc)
                try:
                    db.session.add(new_sub)
                    db.session.commit()
                    flash("Subject added successfully!","success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error: {str(e)}","danger")
                return redirect(url_for("admin_Dashboard"))
    return render_template("addSubject.html")

@app.route("/addQuiz", methods=["GET","POST"])
def add_quiz():
    if request.method=="POST":
        chap=request.form.get("chap_id")
        title=request.form.get("title")
        date_str = request.form.get("date_quiz")
        dat = datetime.strptime(date_str,"%Y-%m-%d").date() 
        time_str=request.form.get("time_dur")
        time = datetime.strptime(time_str, "%H:%M:%S").time()
        rem=request.form.get("remarks")

        if not chap or not title or not dat or not time or not rem:
            flash("All fields are required!","danger")
            return redirect(url_for("add_quiz"))
        else:
            chap_ex=Chapter.query.get(chap)
            if not chap_ex:
                flash("Chapter does not exist! Go and create it here","warning")
                return redirect(url_for("admin_Dashboard"))
            equiz=Quiz.query.filter_by(title=title).first()
            if equiz:
                flash("Quiz already exists!","warning")
                return redirect(url_for("quiz_Management"))
            else:

                new_quiz=Quiz(title=title,date_quiz=dat,time_dur=time,remarks=rem,chap_id=chap)
                try:
                    db.session.add(new_quiz)
                    db.session.commit()
                    flash("Quiz added successfully!","success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error: {str(e)}","danger")
                return redirect(url_for("quiz_Management"))
    return render_template("addQuiz.html")

@app.route("/editSubject/<int:sub_id>", methods=["GET", "POST"])
def edit_subject(sub_id):
    subject = Subject.query.get(sub_id)
    if request.method == "POST":
        newn = request.form.get("sub_name")
        desc = request.form.get("desc")
        
        subject.sub_name = newn
        subject.desc = desc
        try:
            db.session.commit()
            flash("Subject updated successfully!", "success")
            return redirect(url_for("admin_Dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    return render_template("editSubject.html", subject=subject)

@app.route("/deleteSubject/<int:sub_id>")
def delete_subject(sub_id):
    subject = Subject.query.get(sub_id)
    try:
        for chap in subject.chapters:
            for quiz in chap.quizzes:
                Score.query.filter_by(quiz_id=quiz.quiz_id).delete()
                Quiz.query.filter_by(quiz_id=quiz.quiz_id).delete()
            Chapter.query.filter_by(chap_id=chap.chap_id).delete()
        flash("Datas related to subject deleting....","warning")
        db.session.delete(subject)
        db.session.commit()
        flash("Subject deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for("admin_Dashboard"))

@app.route("/editQuiz/<int:quiz_id>", methods=["GET", "POST"])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if request.method == "POST":
        titl = request.form.get("title")
        date_t = request.form.get("date_t")
        d_date=datetime.strptime(date_t,"%Y-%m-%d").date()
        dur=request.form.get("dur")
        time = datetime.strptime(dur, "%H:%M:%S").time()
        rem=request.form.get("rem")
        
        quiz.title = titl
        quiz.date_quiz = d_date
        quiz.time_dur=time
        quiz.remarks=rem
        try:
            db.session.commit()
            flash("Quiz updated successfully!", "success")
            return redirect(url_for("admin_Dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    return render_template("editQuiz.html", quiz=quiz)

@app.route("/deleteQuiz/<int:quiz_id>")
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    try:
        Score.query.filter_by(quiz_id=quiz_id).delete()
        db.session.delete(quiz)
        db.session.commit()
        flash("Quiz deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for("admin_Dashboard"))


@app.route("/addChapter/<int:sub_id>", methods=["GET","POST"])
def add_chapter(sub_id):
    if request.method=="POST":
        chapn=request.form.get("chap_name")
        desc=request.form.get("desc")
        if not chapn or not desc:
            flash("All fields are required!","danger")
            return redirect(url_for("add_chapter",sub_id=sub_id))
        else:
            echap=Chapter.query.filter_by(chap_name=chapn).first()
            if echap:
                flash("Chapter already exists!","warning")
                return redirect(url_for("admin_Dashboard"))
            else:
                new_chap=Chapter(chap_name=chapn,desc=desc,sub_id=sub_id)
                try:
                    db.session.add(new_chap)
                    db.session.commit()
                    flash("Chapter added successfully!","success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error: {str(e)}","danger")
                return redirect(url_for("admin_Dashboard"))
    return render_template("addChapter.html", sub_id=sub_id)

@app.route("/addQuestion/<int:quiz_id>", methods=["GET","POST"])
def add_question(quiz_id):
    if request.method=="POST":
        chap_id=request.form.get("chapID")
        title=request.form.get("title")
        stat=request.form.get("stat")
        opt1=request.form.get("op1")
        opt2=request.form.get("op2")
        opt3=request.form.get("op3")
        opt4=request.form.get("op4")
        copt=request.form.get("copt")

        if not chap_id or not title or not stat or not opt1 or not opt2 or not opt3 or not opt4 or not copt:
            flash("All fields are required!","danger")
            return redirect(url_for("add_question",quiz_id=quiz_id))
        else:
            eQues=Question.query.filter_by(q_title=title).first()
            if eQues:
                flash("Question already exists!","warning")
                return redirect(url_for("quiz_Management"))
            else:
                new_Ques=Question(q_title=title,q_statement=stat,opt_1=opt1,opt_2=opt2,opt_3=opt3,opt_4=opt4,c_opt=copt,quiz_id=quiz_id)
                try:
                    db.session.add(new_Ques)
                    db.session.commit()
                    flash("Question added successfully!","success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error: {str(e)}","danger")
                return redirect(url_for("quiz_Management"))
    chap_id=Quiz.query.get(quiz_id).chap_id
    td=date.today()
    quiz=Quiz.query.get(quiz_id)
    if quiz:
        quiz.date_quiz=td
        db.session.commit()
    return render_template("addQuestion.html", quiz_id=quiz_id, chap_id=chap_id)

@app.route("/editChapter/<int:chap_id>", methods=["GET", "POST"])
def edit_chapter(chap_id):
    chapter = Chapter.query.get(chap_id)
    if request.method == "POST":
        newn = request.form.get("chap_name")
        desc = request.form.get("desc")
        
        chapter.chap_name = newn
        chapter.desc = desc
        try:
            db.session.commit()
            flash("Chapter updated successfully!", "success")
            return redirect(url_for("admin_Dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    return render_template("editChapter.html", chapter=chapter)

@app.route("/deleteChapter/<int:chap_id>")
def delete_chapter(chap_id):
    chapter = Chapter.query.get(chap_id)
    try:
        for quiz in chapter.quizzes:
            Score.query.filter_by(quiz_id=quiz.quiz_id).delete()
            Quiz.query.filter_by(quiz_id=quiz.quiz_id).delete()
        flash("All datas related to chapter deleting....","warning")
        db.session.delete(chapter)
        db.session.commit()
        flash("Chapter deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for("admin_Dashboard"))

@app.route("/editQuestion/<int:q_id>", methods=["GET", "POST"])
def edit_question(q_id):
    ques = Question.query.get(q_id)
    if request.method == "POST":
        chap_id=request.form.get("chapID")
        title=request.form.get("title")
        stat=request.form.get("stat")
        opt1=request.form.get("op1")
        opt2=request.form.get("op2")
        opt3=request.form.get("op3")
        opt4=request.form.get("op4")
        copt=request.form.get("copt")

        old_copt=ques.c_opt
        
        ques.q_title = title
        ques.q_statement = stat
        ques.opt_1 = opt1
        ques.opt_2 = opt2
        ques.opt_3 = opt3
        ques.opt_4 = opt4
        ques.c_opt = copt
        ques.chap_id = chap_id

        try:
            db.session.commit()
            flash("Question updated successfully!", "success")
            if copt != old_copt:
                strqid = str(q_id)
                scores = Score.query.filter_by(quiz_id=ques.quiz_id).all()
                q_ids = [str(q.q_id) for q in Question.query.filter_by(quiz_id=ques.quiz_id).order_by(Question.q_id).all()]
                for sc in scores:
                    c_qid = sc.c_q_ids.split(",") if sc.c_q_ids else []
                    i_qid = sc.i_q_ids.split(",") if sc.i_q_ids else []
                    user_answers = sc.u_ans.split(",") if sc.u_ans else []
                    
                    if strqid in q_ids:
                        index = q_ids.index(strqid)
                        u_prevans = user_answers[index] if index < len(user_answers) else None
                    if u_prevans and u_prevans.isdigit():
                            u_prevans = int(u_prevans)
                        
                    if u_prevans == int(old_copt) and strqid in c_qid:
                        sc.score-=1
                        c_qid.remove(strqid)
                        i_qid.append(strqid)
                    elif u_prevans == int(copt) and strqid in i_qid:
                        sc.score+=1
                        i_qid.remove(strqid)
                        c_qid.append(strqid)
                    sc.c_q_ids = ",".join(c_qid) if c_qid else None
                    sc.i_q_ids = ",".join(i_qid) if i_qid else None
                db.session.commit()  
            return redirect(url_for("quiz_Management"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    return render_template("editQuestion.html", question=ques)

@app.route("/deleteQuestion/<int:q_id>")
def delete_question(q_id):
    ques = Question.query.get(q_id)
    try:
        qz_id=ques.quiz_id
        score=Score.query.filter_by(quiz_id=qz_id).all()
        for sc in score:
            c_qid=sc.c_q_ids.split(",") if sc.c_q_ids else []
            i_qid=sc.i_q_ids.split(",") if sc.i_q_ids else []

            strqid=str(q_id)
            if strqid in c_qid:
                sc.score-=1
                c_qid.remove(strqid)
            
            if strqid in i_qid:
                i_qid.remove(strqid)
            
            sc.c_q_ids = ",".join(c_qid) if c_qid else None
            sc.i_q_ids = ",".join(i_qid) if i_qid else None
        
        db.session.commit()
        db.session.delete(ques)
        db.session.commit()
        rem_q=Question.query.filter_by(quiz_id=qz_id).count()
        if rem_q==0:
            scor1=Score.query.filter_by(quiz_id=qz_id).all()
            for sc1 in scor1:
                db.session.delete(sc1)
            db.session.commit()
            flash("All questions deleted. Score records for this quiz have been removed for all the users who took it.", "warning")     
        else:
            flash("Question deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for("quiz_Management"))

@app.route("/summary")
def sumamry():
    plot_graph1()
    plot_graph2()
    return render_template("summary.html")

@app.route('/user_Dashboard')
def user_Dashboard():
    u_id=session.get('u_id')
    td=date.today()
    takenquiz=Quiz.query.join(Score,Quiz.quiz_id==Score.quiz_id).filter(Score.u_id==u_id).all()
    retake=Quiz.query.join(Score,Score.quiz_id==Quiz.quiz_id).filter(Score.u_id==u_id,Score.date_taken<Quiz.date_quiz).all()
    out_scores = Score.query.join(Quiz, Score.quiz_id == Quiz.quiz_id).filter(Score.u_id == u_id, Score.date_taken < Quiz.date_quiz).all()
    for score in out_scores:
        db.session.delete(score)
    db.session.commit()
    takenquizid=[quiz.quiz_id for quiz in takenquiz ]
    not_taken=Quiz.query.filter(~Quiz.quiz_id.in_(takenquizid)).all()
    quizzes=not_taken+retake
    for quiz in quizzes:
        if len(quiz.questions)==0:
            quizzes.remove(quiz)
    return render_template('userDashboard.html',quizzes=quizzes,td=td)

@app.route('/viewQuiz/<int:quiz_id>')
def view_quiz(quiz_id):
    u_id=session.get('u_id')
    admin_or_not=User.query.get(u_id).admin
    quiz=Quiz.query.get(quiz_id)
    if not quiz:
        flash("Quiz not found!","danger")
    return render_template('viewQuiz.html',quiz=quiz, admin=admin_or_not)

@app.route('/startQuiz/<int:quiz_id>',methods=['GET','POST'])
def start_quiz(quiz_id):
    quiz=Quiz.query.get(quiz_id)
    quiz_dur = quiz.time_dur.hour * 3600 + quiz.time_dur.minute * 60 + quiz.time_dur.second
    end_t = datetime.utcnow() + timedelta(seconds=quiz_dur)
    questions=Question.query.filter_by(quiz_id=quiz_id).all()
    totq=len(questions)
    session['end_t']=end_t.isoformat()
    session['score']=0
    session['user_answers'] = [None] * totq
    session['c_q_ids'] = []
    session['i_q_ids'] = [] 
    return redirect(url_for('start_quizQuestions', quiz_id=quiz_id, q_index=1))

@app.route('/startQuiz/<int:quiz_id>/<int:q_index>', methods=['GET','POST'])
def start_quizQuestions(quiz_id,q_index):
    quiz=Quiz.query.get(quiz_id)
    questions=Question.query.filter_by(quiz_id=quiz_id).all()
    totq=len(questions)
    if q_index>totq:
        flash("Quiz completed!","success")
        return redirect(url_for('quiz_result',quiz_id=quiz_id))
    
    c_q=questions[q_index-1]
    end_t=datetime.fromisoformat(session.get('end_t'))
    t_rem=(end_t-datetime.utcnow()).total_seconds()
    if t_rem<=0:
        flash("Time is up! Quiz auto submiting...","warning")
        return redirect(url_for('quiz_result',quiz_id=quiz_id))
    if request.method=='POST':
        u_ans=request.form.get('ans') 
        try:
            ans = int(u_ans)
        except (ValueError, TypeError):
            ans = None
        
        user_answers=session.get('user_answers',[None] * totq)
        user_answers[q_index-1]=ans
        session['user_answers']= user_answers
        session.modified=True
        c_q_ids = session.get('c_q_ids', [])
        i_q_ids = session.get('i_q_ids', [])
        if ans is not None and ans == c_q.c_opt:
            session['score']+=1
            c_q_ids.append(str(c_q.q_id))
        else:
                i_q_ids.append(str(c_q.q_id))
        session['c_q_ids'] = c_q_ids
        session['i_q_ids'] = i_q_ids
        act=request.form.get('action')
        if act=='submit':
            q_dur = quiz.time_dur.hour * 3600 + quiz.time_dur.minute * 60 + quiz.time_dur.second
            t_end = q_dur - t_rem
            flash("Quiz submiited successfully!","success")
            return redirect(url_for('quiz_result',quiz_id=quiz_id, t_end=t_end))
        elif act=='next':
            return redirect(url_for('start_quizQuestions',quiz_id=quiz_id,q_index=q_index+1))
    return render_template('startQuiz.html',quiz=quiz,questions=c_q,q_index=q_index,t_rem=int(t_rem))

@app.route('/quiz_result/<int:quiz_id>/<int:t_end>', methods=['GET','POST'])
def quiz_result(quiz_id,t_end):
    quiz=Quiz.query.get(quiz_id)
    questions=Question.query.filter_by(quiz_id=quiz_id).all()
    totq=len(questions)
    score=session['score']
    u_id=session['u_id']
    dur_t = (datetime.min + timedelta(seconds=t_end)).time()
    user_answers = session.get('user_answers', [None]*totq)
    c_q_ids = session.get('c_q_ids', [])
    i_q_ids = session.get('i_q_ids', [])
    c_csv = ",".join(c_q_ids)
    i_csv = ",".join(i_q_ids)
    u_csv = ",".join(map(str, user_answers)) if user_answers else None
    new_score=Score(date_taken=datetime.now().date(),dur=dur_t,score=score,u_id=u_id,quiz_id=quiz_id,c_q_ids=c_csv,i_q_ids=i_csv, u_ans=u_csv)
    try:
        db.session.add(new_score)
        db.session.commit()
        flash("Score saved successfully!","success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}","danger")
    return render_template('quizResult.html',quiz=quiz,score=score, user_answers=user_answers)

@app.route('/viewScores', methods=['GET','POST'])
def view_scores():
    u_id=session.get('u_id')
    scores=Score.query.filter_by(u_id=u_id).all()
    for sc in scores:
        sc.tot_q=len(Question.query.filter_by(quiz_id=sc.quiz_id).all())  
 
    return render_template('viewScores.html',scores=scores)

@app.route('/results', methods=['GET','POST'])
def results():
    user_id=session.get('u_id')
    plot_graph3(user_id)
    plot_graph4(user_id)
    return render_template('resultsummary.html')

@app.route('/search1', methods=['GET'])
def admin_search():
    quer=request.args.get('query').strip().lower()
    if not quer:
        flash("Enter a valid query!","warning")
        return redirect(url_for('admin_Dashboard'))
    
    user=User.query.filter(User.name.ilike(f'%{quer}%')).all()
    sub=Subject.query.filter(Subject.sub_name.ilike(f'%{quer}%')).all()
    quiz=Quiz.query.filter(Quiz.title.ilike(f'%{quer}%')).all()

    if not user and not sub and not quiz:
        flash("No matching results found!","warning")
        return redirect(url_for('admin_Dashboard'))
    
    return render_template('searchadminresult.html',quer=quer, user=user, sub=sub, quiz=quiz)

@app.route('/search2',methods=['GET'])
def user_search():
    quer=request.args.get('query').strip().lower()
    quiz=[]
    sc=[]
    sub=[]
    if not quer:
        flash("Enter a valid query!","warning")
        return redirect(url_for('user_Dashboard'))
    
    try:
        q_date=datetime.strptime(quer,"%Y-%m-%d").date()
        quiz=Quiz.query.filter(Quiz.date_quiz==q_date).all()
    except ValueError:
        q_date=None
        quiz=[]
    if quer.isdigit():
        score=int(quer)
        u_id=session.get('u_id')
        sc=Score.query.filter(Score.score==score, Score.u_id==u_id).all()

    if not quiz and not sc:
        sub=Subject.query.filter(Subject.sub_name.ilike(f'%{quer}%')).all()


    if not sc and not sub and not quiz:
        flash("No matching results found!","warning")
        return redirect(url_for('user_Dashboard'))    
    return render_template('searchuserresult.html',quer=quer, sc=sc, sub=sub, quiz=quiz)

@app.route('/viewUsers')
def view_users():
    users=User.query.all()
    return render_template('viewUsers.html',users=users)

if __name__ == '__main__':
   app.run(debug=True)