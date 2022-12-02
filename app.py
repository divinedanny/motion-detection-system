# import beepy
import datetime
import os
import sys
import time
from threading import Thread

import cv2 as cv
import numpy as np
from flask import Flask, Response, flash, redirect, render_template, request,url_for
from flask_login import LoginManager, UserMixin, current_user, login_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from forms import LoginForm, RegistrationForm

detect=False
alarm = False
alarm_mode = False
alarm_counter = 0
camera = cv.VideoCapture(0)

camera.set(cv.CAP_PROP_FRAME_WIDTH, 1040)
camera.set(cv.CAP_PROP_FRAME_HEIGHT, 780)


_, start_frame = camera.read()
start_frame = cv.cvtColor(start_frame, cv.COLOR_BGR2GRAY)
start_frame = cv.GaussianBlur(start_frame, (21, 21), 0)


alarm = False
alarm_mode = False
alarm_counter = 0
counter=1
capture=0

app = Flask(__name__, template_folder='./templates')


day_time = input("is it morning: ")

if day_time == "yes":
    sensitivity = 20000000
else:
    sensitivity = 2000000
if not os.path.exists('data'):
        os.makedirs('data')



def beep_alarm():
    global alarm,counter
    for _ in range(10):
        if not alarm_mode:
            break
        print(f'ALARM {counter}')
        file = 'beep-04.mp3'
        os.system("afplay "+file)
        name = './data/frame' + str(counter) + '.jpg'
        print('Creating...' + name)
        # writing the extracted images
        cv.imwrite(name, frame_bw)
        counter+=1       
        
    alarm = False
    
def detect_movement():
    global alarm,alarm_counter,alarm_mode,camera,start_frame,threshold,frame_bw,counter,day_time,sensitivity
    while True:
        _,frame = camera.read()
        cv.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (30, 40), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        
        if alarm_mode:
            frame_bw = cv.cvtColor(frame,cv.COLOR_BGR2GRAY)
            frame_bw = cv.GaussianBlur(frame_bw,(5,5), 0)
                
            difference = cv.absdiff(frame_bw,start_frame)
            threshold = cv.threshold(difference,25,255, cv.THRESH_BINARY)[1]
            start_frame=frame_bw
                            
            if threshold.sum() > sensitivity:
                alarm_counter +=1
            else:
                if alarm_counter>0:
                    alarm_counter-=1
            frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            cv.imshow("Motion", frame)
                
        else:
            cv.VideoCapture(0)
                        
        if alarm_counter>20:
            if not alarm:
                alarm = True
                Thread(target=beep_alarm).start()  
                
        if (capture):
            name = './shot' + str(counter) + '.png'
            print('Creating...' + name)
            # writing the extracted images
            cv.imwrite(name, threshold)
            
        try:
            _, buffer = cv.imencode('.jpg',frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            pass
        else:
            pass
                    
def gen_frames():
    global alarm,alarm_counter,alarm_mode,camera,start_frame,threshold,frame_bw,detect
    while True:
        _,frame = camera.read()
        cv.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (30, 40), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
       
        try:
            _, buffer = cv.imencode('.jpg',frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            pass
        else:
            pass
          
func = gen_frames()
               
@app.route('/')
def index():
    return render_template("index.html")
    

@app.route('/video_feed')
def video_feed():
    return Response(func, mimetype='multipart/x-mixed-replace; boundary=frame')
   


@app.route('/requests', methods=['POST','GET'])
def tasks():
    global camera,func,alarm_mode
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture = 1
        elif request.form.get('stop') == 'Stop':
            camera.release()
            cv.destroyAllWindows()
        elif request.form.get('start') == 'Start':
            alarm_mode=False
            func = gen_frames()
        elif request.form.get('object') == "Detect":
            alarm_mode = True
            func = detect_movement()
            

            

    elif request.method == 'GET':
        return render_template('index.html')
    return render_template('index.html')
    


plain_password = "qwerty"
hashed_password = generate_password_hash(plain_password)
print(hashed_password)

hashed_password = generate_password_hash(plain_password)
submitted_password = "qwerty"
matching_password = check_password_hash(hashed_password,submitted_password)
print(matching_password)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY


login_manager = LoginManager()
login_manager.init_app(app)



class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(50), index=True, unique=True)
  email = db.Column(db.String(150), unique = True, index = True)
  password_hash = db.Column(db.String(150))
  joined_at = db.Column(db.DateTime(), default = datetime.datetime.utcnow, index = True)

  def set_password(self, password):
        self.password_hash = generate_password_hash(password)

  def check_password(self,password):
      return check_password_hash(self.password_hash,password)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)






@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/register', methods = ['POST','GET'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username =form.username.data, email = form.email.data)
        user.set_password(form.password1.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('registration.html', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user)
            next = request.args.get("next")
            return redirect(next or url_for('home'))
        flash('Invalid email address or Password.')    
    return render_template('login.html', form=form)




cv.destroyAllWindows()

if __name__ == '__main__':
    app.run(debug=True)
