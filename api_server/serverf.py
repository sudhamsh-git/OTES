import os
from flask import Flask, request, Response, jsonify, render_template
import cv2
from FaceAction import FaceAction
from PIL import Image
import numpy
import time
app = Flask(__name__)
mydict = {}
rooms = {}


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE,OPTIONS')
    return response


@app.route('/')
def index():
    return Response(open('./static/local.html').read(), mimetype="text/html")


def last5secAverage(prevc, newc, prevavg, newavg):
    return (newavg*newc-prevavg*prevc)/(newc-prevc)


import matplotlib.pyplot as plt
from io import BytesIO

def save_screenshot(room, student):
    if room in rooms and student in rooms[room]:
        # Create a figure for the plots
        fig, axs = plt.subplots(2, 2, figsize=(10, 10))
        
        # Plot the data (you can customize these plots)
        axs[0, 0].pie([rooms[room][student]['avgdrow'], 1 - rooms[room][student]['avgdrow']], labels=['Drowsy', 'Not Drowsy'])
        axs[0, 1].pie([rooms[room][student]['avgyawn'], 1 - rooms[room][student]['avgyawn']], labels=['Yawning', 'Not Yawning'])
        axs[1, 0].pie([rooms[room][student]['avgpos'], 1 - rooms[room][student]['avgpos']], labels=['Positive', 'Not Positive'])
        axs[1, 1].pie([rooms[room][student]['avgdocopen'], 1 - rooms[room][student]['avgdocopen']], labels=['Doc Open', 'Doc Closed'])

        # Save the figure to a BytesIO object
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # Save to file
        with open(f"{student}_{room}_summary.png", "wb") as f:
            f.write(buf.read())
        
        plt.close(fig)

'''
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email(to_email, subject, body, filename):
    from_email = "example@gmail.com"
    from_password = "password"
    
    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach the file
    attachment = open(filename, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    msg.attach(part)
    
    # Send the email
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, from_password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()
'''

@app.route('/image', methods=['POST', 'OPTIONS'])
def image():

    image_file = request.files['image']
    name = request.form['name']
    room = request.form['room']
    docopen = request.form['docopen']
    teacher = request.form['teacher']
    end = request.form['end']
    print(end)
    image_object = numpy.array(Image.open(image_file).convert('RGB'))
    image_object = image_object[:, :, ::-1].copy()
    drow, yawn, pos, number = FaceAction().run_frame(image_object)
    drow_val = drow
    if (drow < 0.2):
        drow = 1
    else:
        drow = 0
    if (yawn > 0.3):
        yawn = 1
    else:
        yawn = 0
    if(docopen == "false"):
        docopen = 0
    else:
        docopen = 1
    # print(docopen)
    if room in rooms:
        if name in rooms[room]:
            if (end == '1'):
                rooms[room]['class&']['ClassEndTime'] = time.time()
            #print("I am here")
            rooms[room][name]['drow'] = drow
            rooms[room][name]['yawn'] = yawn
            rooms[room][name]['pos'] = pos
            rooms[room][name]['number'] = number
            rooms[room][name]['docopen'] = docopen
            if (rooms[room][name]['drow_val'] == drow_val):
                rooms[room][name]['paused'] = 1
            else:
                rooms[room][name]['paused'] = 0

            #rooms[room][name]['drow_val'] = drow_val
            rooms[room][name]['avgdrow'] = (rooms[room][name]['avgdrow'] *
                                            rooms[room][name]['count']+rooms[room][name]['drow']) / \
                (rooms[room][name]['count'] + 1)
            rooms[room][name]['avgyawn'] = (rooms[room][name]['avgyawn'] *
                                            rooms[room][name]['count']+rooms[room][name]['yawn']) / \
                (rooms[room][name]['count'] + 1)
            rooms[room][name]['avgpos'] = (rooms[room][name]['avgpos'] *
                                           rooms[room][name]['count']+rooms[room][name]['pos']) / \
                (rooms[room][name]['count'] + 1)
            rooms[room][name]['avgdocopen'] = (rooms[room][name]['avgdocopen'] *
                                               rooms[room][name]['count']+rooms[room][name]['docopen']) / \
                (rooms[room][name]['count']+1)
            rooms[room][name]['count'] += 1
            # Dont update if Not going in if condition
            rooms[room][name]['update'] = 0
            nowtime = time.time()
            #print((nowtime - rooms[room][name]['last5']))
            if ((nowtime - rooms[room][name]['last5']) >= 5):
                # print("I am here")
                rooms[room][name]['lastavgdrow'] = last5secAverage(
                    rooms[room][name]['pcount'], rooms[room][name]['count'], rooms[room][name]['pavgdrow'], rooms[room][name]['avgdrow'])
                rooms[room][name]['lastavgyawn'] = last5secAverage(
                    rooms[room][name]['pcount'], rooms[room][name]['count'], rooms[room][name]['pavgyawn'], rooms[room][name]['avgyawn'])
                rooms[room][name]['lastavgpos'] = last5secAverage(
                    rooms[room][name]['pcount'], rooms[room][name]['count'], rooms[room][name]['pavgpos'], rooms[room][name]['avgpos'])
                rooms[room][name]['lastavgdocopen'] = last5secAverage(
                    rooms[room][name]['pcount'], rooms[room][name]['count'], rooms[room][name]['pavgdocopen'], rooms[room][name]['avgdocopen'])
                rooms[room][name]['update'] = 1  # Update Graph if here
                # print(rooms[room][name]['lastavgdocopen'])
                # print(rooms[room][name]['pcount'])
                # print(rooms[room][name]['count'])
                # print(rooms[room][name]['pavgdocopen'])
                # print(rooms[room][name]['avgdocopen'])
                rooms[room][name]['drow_val'] = drow_val
                # Now change prev values to current values
                rooms[room][name]['last5'] = nowtime
                rooms[room][name]['pavgdrow'] = rooms[room][name]['avgdrow']
                rooms[room][name]['pavgyawn'] = rooms[room][name]['avgyawn']
                rooms[room][name]['pavgpos'] = rooms[room][name]['avgpos']
                rooms[room][name]['pavgdocopen'] = rooms[room][name]['avgdocopen']
                rooms[room][name]['pcount'] = rooms[room][name]['count']

                # We have to update Class Avg only when req is coming from teacher
                if (teacher == "true"):
                    avg_drow = 0
                    avg_yawn = 0
                    avg_pos = 0
                    avg_docopen = 0
                    ccc = 0
                    for x in rooms[room]:
                        if (x != 'class&'):
                            # print(x)
                            # print(rooms[room][x]['lastavgyawn'])

                            avg_drow += rooms[room][x]['lastavgdrow']
                            avg_yawn += rooms[room][x]['lastavgyawn']
                            avg_pos += rooms[room][x]['lastavgpos']
                            avg_docopen += rooms[room][x]['lastavgdocopen']
                            ccc += 1
                    rooms[room]['class&']['Cdrow'] = avg_drow / ccc
                    rooms[room]['class&']['Cyawn'] = avg_yawn / ccc
                    rooms[room]['class&']['Cpos'] = avg_pos / ccc
                    rooms[room]['class&']['Cdocopen'] = avg_docopen / ccc

        else:
            rooms[room][name] = {}
            rooms[room][name]['drow'] = drow
            rooms[room][name]['yawn'] = yawn
            rooms[room][name]['pos'] = pos
            rooms[room][name]['number'] = number
            rooms[room][name]['docopen'] = docopen
            # When particular student joined the room
            rooms[room][name]['SessionStart'] = time.time()
            rooms[room][name]['avgdrow'] = rooms[room][name]['drow']
            # Current Average
            rooms[room][name]['avgyawn'] = rooms[room][name]['yawn']
            rooms[room][name]['avgpos'] = rooms[room][name]['pos']
            rooms[room][name]['avgdocopen'] = rooms[room][name]['docopen']
            rooms[room][name]['lastavgdrow'] = 0
            rooms[room][name]['lastavgyawn'] = 0
            rooms[room][name]['lastavgpos'] = 0  # Last 5 second average
            rooms[room][name]['lastavgdocopen'] = 0
            rooms[room][name]['update'] = 1  # Tells js to update values
            rooms[room][name]['last5'] = time.time()
            rooms[room][name]['count'] = 1
            rooms[room][name]['drow_val'] = drow_val
            rooms[room][name]['paused'] = 0
            rooms[room][name]['pavgdrow'] = rooms[room][name]['avgdrow']
            rooms[room][name]['pavgyawn'] = rooms[room][name]['avgyawn']
            rooms[room][name]['pavgpos'] = rooms[room][name]['avgpos']
            # Will be used to calculate last5 second average
            rooms[room][name]['pavgdocopen'] = rooms[room][name]['avgdocopen']
            rooms[room][name]['pcount'] = rooms[room][name]['count']
    else:
        rooms[room] = {}
        rooms[room][name] = {}
        rooms[room]['class&'] = {}
        # For Average of Class
        rooms[room]['class&']['Cdrow'] = 0
        rooms[room]['class&']['Cyawn'] = 0
        rooms[room]['class&']['Cpos'] = 0  # Initially everything is zero
        rooms[room]['class&']['Cdocopen'] = 0
        # time in seconds when room was made
        rooms[room]['class&']['ClassStartTime'] = time.time()
        rooms[room]['class&']['ClassEndTime'] = 0
        # For Room Mader ->Teacher
        rooms[room][name]['drow'] = drow
        rooms[room][name]['yawn'] = yawn
        rooms[room][name]['pos'] = pos
        rooms[room][name]['number'] = number
        rooms[room][name]['docopen'] = docopen
        rooms[room][name]['avgdrow'] = rooms[room][name]['drow']
        # Current Average
        rooms[room][name]['avgyawn'] = rooms[room][name]['yawn']
        rooms[room][name]['avgpos'] = rooms[room][name]['pos']
        rooms[room][name]['avgdocopen'] = rooms[room][name]['docopen']
        rooms[room][name]['lastavgdrow'] = 0
        rooms[room][name]['lastavgyawn'] = 0
        rooms[room][name]['lastavgpos'] = 0  # Last 5 second average
        rooms[room][name]['lastavgdocopen'] = 0
        rooms[room][name]['drow_val'] = drow_val
        rooms[room][name]['paused'] = 0
        rooms[room][name]['update'] = 1  # Tells js to update values
        rooms[room][name]['last5'] = time.time()
        rooms[room][name]['count'] = 1
        rooms[room][name]['pavgdrow'] = rooms[room][name]['avgdrow']
        rooms[room][name]['pavgyawn'] = rooms[room][name]['avgyawn']
        rooms[room][name]['pavgpos'] = rooms[room][name]['avgpos']
        # Will be used to calculate last5 second average
        rooms[room][name]['pavgdocopen'] = rooms[room][name]['avgdocopen']
        rooms[room][name]['pcount'] = rooms[room][name]['count']

    d = {"Dictionary": rooms}
    # print(room)
        # Save screenshot and send email when class ends
    if (end == '1'):
        save_screenshot(room, name)
        '''        send_email('teacher-email@example.com', f"Summary for {name} in {room}",
                   f"Attached is the summary for {name} in the class {room}.",
                   f"{name}_{room}_summary.png")
        '''

    return jsonify(d)






if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
