from os import path
from flask import Flask, render_template,request,jsonify,make_response,redirect, url_for,abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_migrate import Migrate
import jwt
import validators as vd
from functools import wraps
from datetime import datetime,timedelta

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/data.db'
app.config['UPLOAD_FOLDER'] = "./files"
app.config['SECRET_KEY'] = 'aecaf6bb-af75-425c-b05b-22956c140f9e'


pic = {
    "mohamedhajali45@gmail.com":None,
    "jabrikhalil869@gmail.com":None,
    "ca19ac20@gmail.com":None,
    "eljchaker474@gmail.com":path.join('static/','cheker.jpg'),
    "abdrahmen.amri@fsb.ucar.tn":path.join('static/','abdou.jpg')
}
devs = ["mohamedhajali45@gmail.com","jabrikhalil869@gmail.com","ca19ac20@gmail.com","eljchaker474@gmail.com","abdrahmen.amri@fsb.ucar.tn"]
allowed_mail = ["mohamedhajali45@gmail.com","jabrikhalil869@gmail.com","ca19ac20@gmail.com","eljchaker474@gmail.com","abdrahmen.amri@fsb.ucar.tn","test@test.com"]

db = SQLAlchemy(app)
migrate = Migrate(app, db)

@app.template_filter()
def fdate(date):
    if date:
        return date.strftime("%d-%m-%Y %H:%M:%S")
    else:
        return None

@app.template_filter()
def clr(i,d):
    if (d == "clr"):
        if i == 0 or i == None:
            return "red"
        elif i == 1:
            return "yellow"
        else : return "green"
    elif (d == "id"):
        tasks = Task.query.filter_by(sprint_id = i).all()
        is_red = False
        is_green = False
        is_yellow = False
        for task in tasks:
            if task.task_state == 0 or task.task_state == None:
                is_red = True
            elif task.task_state == 1:
                is_yellow = True
            else : is_green = True
        if is_yellow or (is_green and is_red):
            return "yellow"
        elif is_green and not is_red:
            return "green"
        else : return "red"


@app.template_filter()
def picdev(id):
    user = User.query.filter_by(id = id).first()
    if pic[user.email] != None:
        return pic[user.email]
    return path.join('static/','user.webp')

@app.template_filter()
def calc_prog(id):
    tasks = Task.query.filter_by(sprint_id = id).all()
    p = 0
    for task in tasks:
        if task.task_state == 2 :
            p = p +1
    if len(tasks) == 0:
        return round(0.0,2)*100
    return round(p/len(tasks),2)*100

class Comment(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    comment = db.Column(db.Text,index=False,nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    task_id = db.Column(db.Integer,db.ForeignKey('task.id'))
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))



class Task(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    task_name = db.Column(db.String(200), index=True,nullable=False)
    task_desc = db.Column(db.Text,nullable=False)
    task_rank = db.Column(db.Integer,nullable=False)
    task_state = db.Column(db.Integer,nullable=True,default = 0)
    task_estm = db.Column(db.Integer,nullable=False)
    task_create_at = db.Column(db.DateTime, default=datetime.utcnow)
    task_taken_at = db.Column(db.DateTime,nullable=True)
    task_done_at = db.Column(db.DateTime,nullable=True)
    sprint_id = db.Column(db.Integer,db.ForeignKey('sprint.id'))
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    comments = db.relationship('Comment',backref='task')


    def __repr__(self) -> str:
        return f'<User : {self.task_name}/t{self.task_desc}/t{self.task_rank}/t{self.task_state}/t{self.task_estm}/t{self.task_create_at}/t{self.user_id}/t{self.sprint_id}'



class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(60),index=True,nullable=False)
    email = db.Column(db.String(80),index=True,nullable=False,unique=True)
    password = db.Column(db.String(200))
    is_dev = db.Column(db.Integer,default = 0,nullable=False)
    tasks = db.relationship('Task',backref='user')
    comments = db.relationship('Comment',backref='user')

    def __repr__(self) -> str:
        return f'<User : {self.name}/t{self.email}/t{self.is_dev}'
    

class Sprint(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    sprint_name = db.Column(db.String(200), index=True,nullable=False)
    sprint_desc = db.Column(db.Text,nullable=False)
    sprint_rank = db.Column(db.Integer,nullable=False)
    sprint_estm = db.Column(db.Integer,nullable=False)
    sprint_create_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('Task',backref='tasks')


    def __repr__(self) -> str:
        return f'<User : {self.sprint_name}/t{self.sprint_desc}/t{self.sprint_rank}/t{self.sprint_estm}/t{self.sprint_create_at}'

def decodejwt(jwwt):
    return jwt.decode(jwwt,app.config['SECRET_KEY'],algorithms=['HS256'])
def is_dev():
    return jwt.decode(request.cookies.get('JWT-TOKEN'),app.config['SECRET_KEY'],algorithms=['HS256'])['email'] in devs
def is_allowed():
    return jwt.decode(request.cookies.get('JWT-TOKEN'),app.config['SECRET_KEY'],algorithms=['HS256'])['email'] in allowed_mail
def task_state(state):
    if(state == 0 or state == None):
        return "not started yet"
    elif(state == 1):
        return "started"
    elif(state == 2):
        return "finished"

def res(data,err,errcode):
    if data:
        response = make_response(
            jsonify(
                {"data": data,}
            ),
        200,
        )
    elif err and errcode:
        response = make_response(
            jsonify(
                {"error_message": str(err)}
            ),
        errcode,
    )
    response.headers["Content-Type"] = "application/json"
    return response

def token_required(f):
    @wraps(f)
    def main(*args, **kwargs):
        if not request.cookies.get('JWT-TOKEN') :
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return main

def dev_required(f):
    @wraps(f)
    def main(*args, **kwargs):
        if not request.cookies.get('JWT-TOKEN') :
            return redirect(url_for('signup'))
        data = jwt.decode(request.cookies.get('JWT-TOKEN'),app.config['SECRET_KEY'],algorithms=['HS256'])
        if data['email'] not in devs :
            return redirect(url_for('/'))
        return f(*args, **kwargs)
    return main

@app.route('/', methods=['GET'])
@token_required
def index():
    return render_template('index.html',legend = 'add sprint', isdev = is_dev(),add = "/addsprint",data_type = "sprint")

@app.route('/teams',methods = ["GET"])
@token_required
def teams():
    teams = User.query.filter_by(is_dev = 1).all()

    return render_template('index.html',teams = teams,data_type = 'user',header = 'developers')

@app.route('/teams/sprints/<id>',methods = ["GET"])
@token_required
def teamsSprints(id):
    user = User.query.filter_by(id = id).first()
    if(int(id) and user):
        sp = []
        tasks =  Task.query.filter_by(user_id =id).all()
        for task in tasks :
            if task.sprint_id not in sp:
                sp.append(task.sprint_id)
        sprints = []
        for i in sp:
            sprints.append(Sprint.query.filter_by(id = i).first())
        return render_template('index.html',data_type = 'user',sprintuser = sprints,header= user.name+' Sprints',user=user)
    else : abort(400)

@app.route('/teams/<uid>/tasks/<id>',methods = ["GET"])
@token_required
def teamsTasks(uid,id):
    user = User.query.filter_by(id = uid).first()
    if(int(id) and user):
        sp = []
        sprint = Sprint.query.filter_by(id = id).first()
        tasks =  Task.query.filter_by(user_id =uid,sprint_id = id).all()
        for task in tasks :
            if task.sprint_id not in sp:
                sp.append(task.sprint_id)
        return render_template('index.html',data_type = 'user',tasks = sp,header= user.name+' tasks',sprint = sprint,user= user,taskss = True)
    else : abort(400)


@app.route('/get-tasks/<id>/user/<uid>', methods = ["POST"])
@token_required
def getTasksByUser(id,uid):
    try:
        int(id)
        int(uid)
    except:
        abort(400)
    sprint = Sprint.query.filter_by(id = id).first()
    if not sprint :
        abort(301)
    tasks = Task.query.filter_by(sprint_id = id,user_id = uid).order_by(desc(Task.task_rank)).all()
    res = []
    if not tasks : return jsonify({'data':res}),200
    for task in tasks: 
        s = {
            "id": task.id,
            "name": task.task_name,
            "desc": task.task_desc,
            "rank": task.task_rank,
            "estm": task.task_estm,
            "color": clr(task.task_state,'clr')
        }
        res.append(s)
    response = make_response(jsonify({'data':res}),200)
    response.headers["Content-Type"] = "application/json"
    return response
    



@app.route('/addcomment/<id>', methods=['POST'])
@token_required
def add_comment(id):
    try :
        id = int(id)
    except :
        abort(400)
    task = Task.query.filter_by(id = id).first()
    comment = str(request.form['comment'])
    if task and is_allowed() and len(comment) > 0:
        new_comment = Comment(comment = comment,user_id = decodejwt(request.cookies.get('JWT-TOKEN'))['id'],task_id = id)
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({'COMMENT':'INSERTED'})
    else : return jsonify({'success':False}), 401

def canDel(uid,com):
    uid = int(uid)
    task = Task.query.filter_by(id = com.task_id).first()
    if(task and (com.user_id == uid or task.user_id == uid)):
        return True
    return False


@app.route('/delcomment/<id>', methods=['DELETE'])
@token_required
def delComment(id):
    try :
        id = int(id)
    except :
        abort(400)
    com = Comment.query.filter_by(id = id).first()
    if com :
        if not canDel(decodejwt(request.cookies.get('JWT-TOKEN'))['id'],com) :
            abort(401)
        db.session.delete(com)
        db.session.commit()
        return jsonify({'success':True}), 200
    return jsonify({'success':False}), 400


        

@app.route('/fetchcomment/<id>', methods=['POST'])
@token_required
def fetch_comment(id):
    try :
        id = int(id)
    except :
        return jsonify({'success':False}), 400
    task = Task.query.filter_by(id = id).first()
    if task:
        ts = {
            "task_id": task.id,
            "task_name": task.task_name,
            "task_desc": task.task_desc,
            "task_rank": task.task_rank,
            "task_estm": task.task_estm,
            "task_state" : {"text":task_state(task.task_state),
                            "code": 0 if task.task_state == None else task.task_state},
            "task_owner": User.query.filter_by(id = task.user_id).first().name,
            "task_created_at": fdate(task.task_create_at),
            "task_started_at": fdate(task.task_taken_at),
            "task_finished_at": fdate(task.task_done_at),
            "task_finished": True if (task.task_state == 2) else False,
            "task_started": True if task.task_state == 1 or task.task_state == 2 else False,
            "task_color": clr(task.task_state,'clr'),
            "is_owner": decodejwt(request.cookies.get('JWT-TOKEN'))['id'] == task.user_id
        }
        comments = Comment.query.filter_by(task_id = id).order_by(desc(Comment.created_at)).all()
        rslts = []
        for comment in comments:
            rslt = {}
            rslt['poster'] = User.query.filter_by(id = comment.user_id).first().name
            rslt['post_date'] = fdate(comment.created_at)
            rslt['comment'] = comment.comment
            rslt['id_comment'] = comment.id
            rslt['CanDel'] = canDel(decodejwt(request.cookies.get('JWT-TOKEN'))['id'],comment)
            rslts.append(rslt)
        return jsonify({"coma":rslts,"ts":ts})
    else : return redirect(url_for('index'))

@app.route('/get-sprints', methods = ["POST"])
@token_required
def getSprints():
    sprints = Sprint.query.order_by(desc(Sprint.sprint_rank)).all()
    res = []
    if sprints:
        for sprint in sprints:
            s = {
                "id": sprint.id,
                "name": sprint.sprint_name,
                "desc": sprint.sprint_desc,
                "rank": sprint.sprint_rank,
                "estm": sprint.sprint_estm,
                "color": clr(sprint.id,'id'),
                "progress": calc_prog(sprint.id)
            }
            res.append(s)
    response = make_response(jsonify({'data':res}),200)
    response.headers["Content-Type"] = "application/json"
    return response
    
@app.route('/get-tasks/<id>', methods = ["POST"])
@token_required
def getTasks(id):
    try:
        int(id)
    except:
        return jsonify({'success':False}), 400
    sprint = Sprint.query.filter_by(id = id).first()
    if not sprint :
        abort(301)
    tasks = Task.query.filter_by(sprint_id = id).order_by(desc(Task.task_rank)).all()
    res = []
    if not tasks : return jsonify({'data':res}),200
    for task in tasks: 
        s = {
            "id": task.id,
            "name": task.task_name,
            "desc": task.task_desc,
            "rank": task.task_rank,
            "estm": task.task_estm,
            "color": clr(task.task_state,'clr')
        }
        res.append(s)
    response = make_response(jsonify({'data':res}),200)
    response.headers["Content-Type"] = "application/json"
    return response
    


@app.route('/task/<action>/<id>', methods=['PUT','DELETE'])
@token_required
@dev_required
def task(id,action):
    try:
        id = int(id)
        action = str(action)
    except:
        return abort(400)
    task = Task.query.filter_by(id=id).first()
    if request.method == 'DELETE' and task and decodejwt(request.cookies.get('JWT-TOKEN'))['id'] == task.user_id and action == "delete":
        comments = Comment.query.filter_by(task_id = task.id).all()
        for comment in comments:
            db.session.delete(comment)
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success':True}), 200
    elif request.method == 'PUT' and task and decodejwt(request.cookies.get('JWT-TOKEN'))['id'] == task.user_id:
        if action == "done" and task.task_taken_at:
            task.task_done_at = datetime.utcnow()
            task.task_state = 2
            db.session.add(task)
            db.session.commit()
            return jsonify({'success':True}), 200
        elif action == "take":
            task.task_taken_at = datetime.utcnow()
            task.task_state = 1
            db.session.add(task)
            db.session.commit()
            return jsonify({'success':True}), 200
        else : abort(400)
    else : abort(405)




@app.route('/sprint/<id>', methods=['GET', 'POST','PUT','DELETE'])
@token_required
def sprint(id):
    if request.method == 'DELETE':
        sprint = Sprint.query.filter_by(id = id).first()
        if sprint:
            tasks = Task.query.filter_by(sprint_id = id).all()
            if tasks:
                for task in tasks:
                    comments = Comment.query.filter_by(task_id = task.id).all()
                    for comment in comments:
                        db.session.delete(comment)
                    db.session.delete(task)
            db.session.delete(sprint)
            db.session.commit()
            return make_response(jsonify({"SPRINT": "DELETED"}),200)
        else : abort(400)
    

    if(id.isdigit()):
        sprint = Sprint.query.filter_by(id = id).first()
        if sprint :
            return render_template('index.html',data_type = "task",sprint = sprint, isdev = is_dev(),legend = 'add task',add = '/addtask/{}'.format(id))
        else : abort(404)
    else : abort(400)


@app.route('/addtask/<id>', methods=['POST'])
@token_required
@dev_required
def addtask(id):
    if request.form :
        try :
            name = str(request.form['name'])
            desc = str(request.form['desc'])
            estm = int(request.form['estm'])
            rank = int(request.form['rank'])
        except:
            return make_response(jsonify({"INPUTS": "INVALID"}),400)
        if len(name) * len(desc) != 0 and rank>0 and rank <= 100:
            task = Task(task_name = name, task_desc = desc, task_rank = rank, task_estm = estm, sprint_id = id, user_id = decodejwt(request.cookies.get('JWT-TOKEN'))['id'])
            db.session.add(task)
            db.session.commit()
            response = make_response(jsonify({"TASK": "INSERTED"}),200)
            return response
        else: return make_response(jsonify({"INPUTS": "INVALID"}),400)
    else: return make_response(jsonify({"INPUTS": "INVALID"}),400)





@app.route('/addsprint', methods=['POST'])
@token_required
@dev_required
def addsprint():
    if request.form :
        try :
            name = str(request.form['name'])
            desc = str(request.form['desc'])
            estm = int(request.form['estm'])
            rank = int(request.form['rank'])
        except: return make_response(jsonify({"SUCCESS": False}),400)
        if len(name) * len(desc) == 0 or rank <1 and rank > 100: return make_response(jsonify({"SUCCESS": False}),400)
        sprint = Sprint(sprint_name = name, sprint_desc = desc, sprint_rank = rank, sprint_estm = estm)
        db.session.add(sprint)
        db.session.commit()
        return make_response(jsonify({"SUCCESS": True}),200)
    else : return make_response(jsonify({"SUCCESS": False}),400)


@app.route('/logout',methods=['POST','GET'])
@token_required
def logout():
    response = make_response(jsonify({'LOGOUT':'GRANTED'}),200)
    response.headers["access-control-expose-headers"] = "Set-Cookie"
    response.delete_cookie('JWT-TOKEN')
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == 'GET':
        return render_template('index.html',login = True,btnText = 'SIGN IN')
    if request.method == 'POST':
        if request.form :
            data = request.form
            if data['email'] and data['password']:
                email = data['email']
                password = data['password']
                if(vd.email(email) and email in allowed_mail):
                    user = User.query.filter_by(email=email,password = password).first()
                    if user :
                        jwtcode = jwt.encode({"id":user.id,"email":user.email,"is_dev":user.is_dev},app.config['SECRET_KEY'])
                        response = make_response(jsonify({"ACCESS": "ACCESS GRANTED"}),200)
                        response.headers["access-control-expose-headers"] = "Set-Cookie"
                        response.set_cookie('JWT-TOKEN', jwtcode, httponly=True,expires=timedelta(days=21) + datetime.now())
                        response.headers["Content-Type"] = "application/json"
                        return response
                    else: 
                        response = res(err="ACCESS_DENIED",errcode=401,data=None)
                        return response
                else: 
                    response = res(err="BARRA_AL3AB_B3ID",errcode=401,data=None)
                    return response
            else: 
                response = res(err="FECH_9A3D_TA3ML",errcode=401,data=None)
                return response
        else: 
            response = res(err="MCH_LHA_DARJA_BHIM",errcode=401,data=None)
            return response
    else: return ''

@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method == 'GET':
        return render_template('index.html',signup = True,btnText = 'SIGN UP')
    if request.method == 'POST':
        if request.form :
            data = request.form
            if data['name'] and data['email'] and data['password']:
                name = data['name']
                email = data['email']
                password = data['password']
                if len(name) * len(email) * len(password) == 0:
                    return res(err="7aja fergha",errcode=401,data=None)
                if all(x.isalpha() or x.isspace() for x in name):
                    if(vd.email(email) and email in allowed_mail):
                        user = User.query.filter_by(email=email).first()
                        if user and user.name == name and user.password == password :
                            jwtcode = jwt.encode({"id":user.id,"email":user.email,"is_dev":user.is_dev},app.config['SECRET_KEY'])
                            response = make_response(jsonify({"ACCESS": "ACCESS GRANTED"}),200)
                            response.headers["access-control-expose-headers"] = "Set-Cookie"
                            response.set_cookie('JWT-TOKEN', jwtcode, httponly=True,expires=timedelta(days=21) + datetime.now())
                            response.headers["Content-Type"] = "application/json"
                            return response
                        if user :
                            response = res(err="A3ML_LOGIN",errcode=401,data=None)
                            return response
                        new = User(name = name,email = email,password = password,is_dev = 1 if (email in devs) else 0)
                        db.session.add(new)
                        db.session.commit()
                        jwtcode = jwt.encode({"id":new.id,"email":new.email,"is_dev":new.is_dev},app.config['SECRET_KEY'])
                        response = make_response(jsonify({"ACCESS": "ACCESS GRANTED"}),200)
                        response.headers["access-control-expose-headers"] = "Set-Cookie"
                        response.set_cookie('JWT-TOKEN', jwtcode, httponly=True,expires=timedelta(days=21) + datetime.now())
                        response.headers["Content-Type"] = "application/json"
                        return response
                    else: 
                        response = res(err="ACCESS_DENIED",errcode=401,data=None)
                        return response
                else: 
                    response = res(err="BARRA_AL3AB_B3ID",errcode=401,data=None)
                    return response
            else: 
                response = res(err="FECH_9A3D_TA3ML",errcode=401,data=None)
                return response
        else: 
            response = res(err="MCH_LHA_DARJA_BHIM",errcode=401,data=None)
            return response



                
        return ''

if __name__ == '__main__':
    app.run(host='0.0.0.0')
 