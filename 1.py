
from flask import Flask, render_template, Response, request
import cv2 as cv
import datetime, time
import os, sys
import numpy as np
from threading import Thread


global capture,rec_frame, grey, switch, neg, rec, out
capture=0
grey=0
neg=0
face=0
switch=1
rec=0
org=0

#make shots directory to save pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass

#Load pretrained face detection model    
protext_path = 'models/MobileNetSSD_deploy.prototxt'
model_path = 'models/MobileNetSSD_deploy.caffemodel'
min_confidence = 0.2
classes = ["backgroound", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow",
    "diningtable", "dog", "dorse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]
np.random.seed(876543210)
colors = np.random.uniform(0, 255, size=(len(classes), 3))
net = cv.dnn.readNetFromCaffe(protext_path, model_path)
#instatiate flask app  
app = Flask(__name__, template_folder='./templates')

alarm = False
alarm_mode = False
alarm_counter = 0

camera = cv.VideoCapture(0)


_, start_frame = camera.read()
start_frame = cv.resize(start_frame, (500,300))
start_frame = cv.cvtColor(start_frame, cv.COLOR_BGR2GRAY)
start_frame = cv.GaussianBlur(start_frame, (21, 21), 0)


def beep_alarm():
    global alarm
    for _ in range(5):
        if not alarm_mode:
            break
        print('ALARM')
        # winsound.Beep(2500,1000)

    alarm = False

def record(out):
    global rec_frame
    while (rec):
        time.sleep(0.05)
        out.write(rec_frame)

# def orginal():
#     while True:
#         success, org_frame = camera.read()
#         frame = org_frame

    

def detect_face():
    global frame,camera,protext_path, model_path, min_confidence, classes, colors, net,alarm_counter, alarm_mode, alarm
    while True:
        success, frame = camera.read()
        if success:
            height, width = frame.shape[0], frame.shape[1]
            blob = cv.dnn.blobFromImage(cv.resize(frame, (300, 300)), 0.007, (300,300), 130)
            frequency = 2000
            duration = 1500
            net.setInput(blob)
            detected_object = net.forward()
        
            if alarm_mode:
                frame_bw = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                frame_bw = cv.GaussianBlur(frame_bw, (5, 5), 0)

                difference = cv.absdiff(frame_bw, start_frame)
                threshold = cv.threshold(
                difference, 25, 255, cv.THRESH_BINARY)[1]
                start_frame = frame_bw

            if threshold.sum() > 300:
                alarm_counter += 1
            else:
                if alarm_counter > 0:
                    alarm_counter -= 1

            cv.imshow("cam", threshold)

        else:
            cv.imshow("cam", frame)

        if alarm_counter > 20:
            if not alarm:
                alarm = True
                Thread(target=beep_alarm).start()

            
            for i in range(detected_object.shape[2]):
                confidence = detected_object[0][0][i][2]
                if confidence> min_confidence:
                    class_index = int(detected_object[0, 0, i, 1])
                    upper_left_x = int(detected_object[0, 0, i, 3] * width)
                    upper_left_y = int(detected_object[0, 0, i, 4] * height)
                    lower_right_x = int(detected_object[0, 0, i, 5] * width)
                    lower_right_y = int(detected_object[0, 0, i, 6] * height)
                    prediction_text = f"{classes[class_index]}: {confidence: .2f}%"
                    cv.rectangle(rec_frame, (upper_left_x, upper_left_y), (lower_right_x, lower_right_y), colors[class_index], 3)
                    cv.putText(rec_frame, prediction_text, (upper_left_x, upper_left_y-15 if upper_left_y>30 else upper_left_y+15), cv.FONT_HERSHEY_SIMPLEX, 0.6, colors[class_index], 2)        
                                
                else:
                    pass
            
            
            try:
                ret, buffer = cv.imencode('.jpg', cv.flip(frame, 1))
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                    pass


def gen_frames():  # generate frame by frame from camera
    global out, capture, rec_frame
    global frame,camera,protext_path, model_path, min_confidence, classes, colors, net

    while True:
        
        _, frame = camera.read()
        if _:
            rec_frame=frame
            height, width = frame.shape[0], frame.shape[1]
            blob = cv.dnn.blobFromImage(cv.resize(frame, (300, 300)), 0.007, (300,300), 130)
            net.setInput(blob)
            detected_object = net.forward()
            
            
            if (face):
                frame = detect_face()
            if (grey):
                frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            if (neg):
                frame = cv.bitwise_not(frame)
            # if (org):
            #     frame = orginal()
            if (capture):
                capture = 0
                now = datetime.datetime.now()
                p = os.path.sep.join(
                    ['shots', "shot_{}.png".format(str(now).replace(":", ''))])
                cv.imwrite(p, frame)

            if (rec):
                rec_frame = frame
                frame = cv.putText(cv.flip(
                    frame, 1), "Recording...", (0, 25), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4)
                frame = record()
                
            
            
            for i in range(detected_object.shape[2]):
                confidence = detected_object[0][0][i][2]
                if confidence> min_confidence:
                    class_index = int(detected_object[0, 0, i, 1])
                    upper_left_x = int(detected_object[0, 0, i, 3] * width)
                    upper_left_y = int(detected_object[0, 0, i, 4] * height)
                    lower_right_x = int(detected_object[0, 0, i, 5] * width)
                    lower_right_y = int(detected_object[0, 0, i, 6] * height)
                    prediction_text = f"{classes[class_index]}: {confidence: .2f}%"
                    cv.rectangle(rec_frame, (upper_left_x, upper_left_y), (lower_right_x, lower_right_y), colors[class_index], 3)
                    cv.putText(rec_frame, prediction_text, (upper_left_x, upper_left_y-15 if upper_left_y>30 else upper_left_y+15), cv.FONT_HERSHEY_SIMPLEX, 0.6, colors[class_index], 2)        

            
            
            #show date and current time
            cv.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, frame.shape[0] - 10), cv.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            
            try:
                ret, buffer = cv.imencode('.jpg')
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                 pass

        else:
            pass
        
                
                
@app.route('/')
# ‘/’ URL is bound with hello_world() function.
def index():
	return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')








@app.route('/requests', methods=['POST', 'GET'])
def tasks():
    global switch, camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture = 1
        elif request.form.get('grey') == 'Grey':
            global grey
            grey = not grey
        elif request.form.get('neg') == 'Negative':
            global neg
            neg = not neg
        elif request.form.get('Detect Object') == 'object':
            detect_face()
        # elif request.form.get('normal') == 'Original':
        #     global org
        #     org = not org
        elif request.form.get('stop') == 'Stop/Start':

            if (switch == 1):
                switch = 0
                camera.release()
                cv.destroyAllWindows()

            else:
                camera = cv.VideoCapture(0)
                switch = 1
        elif request.form.get('rec') == 'Start/Stop Recording':
            global rec, out
            rec = not rec
            if (rec):
                now = datetime.datetime.now()
                fourcc = cv.VideoWriter_fourcc(*'XVID')
                out = cv.VideoWriter('vid_{}.mp4'.format(
                    str(now).replace(":", '')), 0x7634706d, 20.0, (640, 480))
                # Start new thread for recording the video
                thread = Thread(target=record, args=[out, ])
                thread.start()
            elif (rec == False):
                out.release()

    elif request.method == 'GET':
        return render_template('index.html')
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
