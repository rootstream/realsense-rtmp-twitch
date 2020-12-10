#!python3

import pyrealsense2 as rs
import numpy as np
import cv2
import os
import json
import time
import platform
import asyncio
import netifaces
import cvui
import requests

from threading import Thread

import multiprocessing
from multiprocessing import Process, Queue

import flask
from flask import Flask, Response, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from realsense_rtmp_stream import RealsenseCapture

from colorama import Fore, Back, Style
from colorama import init
init()

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

streams = []
running = False
streaming = False

hostip = ""

app = Flask(__name__, 
    static_folder='web', 
    static_url_path='')
socketio = SocketIO(app, async_mode="threading")

Gst.init(None)

@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)

@socketio.on('connect')
def test_connect():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')    

@socketio.on('start')
def handle_start(url):

    global streams
    global streaming

    print('start ', url, len(streams))

    if len(streams) == 0:
        # Control parameters
        # =======================
        dir_path = os.path.dirname(os.path.realpath(__file__))
        json_file = dir_path + "/" + "MidResHighDensityPreset.json" # MidResHighDensityPreset.json / custom / MidResHighAccuracyPreset

        stream = RealsenseCapture( url, json_file, 640, 480 )
        streaming = True        
        stream.start()
        streams.append(stream)

@socketio.on('stop')
def handle_stop():
    global streams
    global streaming
    
    print('Stop')
    streaming = False
    if len(streams) > 0:
        streams[0].shutdown()
        streams.pop(streams[0])

@app.route('/')
def root():
    print('route')  
    return app.send_static_file('index.html')

#TODO: Add some kind of security step here? Anybody on the local network can shut down hardware
@socketio.on('shutdown')
def handle_shudown():
    global running
    
    print('Shutdown')  
    running = False
    try:
        socketio.stop()
    except:
        pass

    print('Shutdown Complete') 

#TODO: Add some kind of security step here? Anybody on the local network can shut down hardware
@app.route('/shutdown')
def quit():
    global running
    running = False
    try:
        socketio.stop()
    except:
        pass
    return ('', 204)

class WebSocketServer(object):
    def __init__(self):
        self.thread = None

    def start_server(self):
        socketio.run(app, port=5000, debug=False, use_reloader=False)

    def start(self):
        self.thread = socketio.start_background_task(self.start_server)

    def stop(self):
        socketio.stop()

    def send_msg(self, type, data):
        socketio.emit(type, json.dumps(data),namespace="/")

    def wait(self):
        self.thread.join()

def main():
    
    global streams
    global streaming
    global running
    
    try:

        ctx = rs.context()
        if len(ctx.devices) > 0:
            for d in ctx.devices:
                print ('Found device: ',
                    d.get_info(rs.camera_info.name), ' ',
                    d.get_info(rs.camera_info.serial_number))
        else:
            print(Fore.RED + "No Realsense devices connected" + Fore.RESET)

        print( "Default gateway: ", netifaces.gateways()['default'])
        print( "Internet interface", netifaces.gateways()['default'][netifaces.AF_INET])

        if( len(netifaces.gateways()['default'])):
            if( len( netifaces.gateways()['default'][netifaces.AF_INET])):
                iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
                if( len(netifaces.ifaddresses(iface)[netifaces.AF_INET] )):
                    hostip = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
                    print(Fore.YELLOW + "Found Host IP" , hostip , Fore.RESET)
                else:
                    print(Fore.RED + "No internet connected address [AF_INET]"+ Fore.RESET)
            else:
                print(Fore.RED + "No internet connected gatate"+ Fore.RESET)
        else:
            print(Fore.RED + "No default gateway"+ Fore.RESET)

        server = WebSocketServer()
        server.start()

        running = True

        WINDOW_NAME	= 'VPT Kit'

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, 1280, 720)
        cv2.moveWindow(WINDOW_NAME, 0, 0)
        cvui.init(WINDOW_NAME)
        
        uiframe = np.zeros((720, 1280, 3), np.uint8)
        preview = np.zeros((480, 1280, 3), np.uint8)

        while(running == True):
            uiframe[:] = (255, 50, 50)
            cvui.beginRow(uiframe, 0, 0, 1280, 720, 0)
            cvui.beginColumn(1280, 720, 0)
            #row 1
            cvui.text('Connnect to http://{0}:5000/'.format( hostip))

            #TODO: need better way to keep streams updated / monitor when the process crashes/exits
            for stream in streams:
                if( not stream.is_alive()):
                    streams.remove(stream)


            #row 2
            if len(streams) > 0:
                cvui.printf(  "framecount = %.0f", streams[0].framecount)
                newpreview = streams[0].LastPreview()
                if( newpreview is not None ):
                    preview = newpreview
                    
            cvui.image( preview)

            #row 3
            if cvui.button('&Shutdown'):
                break

            cvui.endColumn()
            cvui.endRow()
            cvui.update()

            cv2.imshow(WINDOW_NAME, uiframe) 
            
            # Check if ESC key was pressed
            if cv2.waitKey(1) == 27:
                running = False

            socketio.sleep(0.01)

    finally:
        print('shutting down')  

        if len(streams) > 0:
            streaming = False
            print('shutdown stream')  
            streams[0].shutdown()

        try:
            shutdown_server = requests.get("http://localhost:5000/shutdown", data=None)
        except:
            pass

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    main()