#!python3

import pyrealsense2 as rs
import numpy as np
import cv2
import os
import json
import time
import platform
import asyncio

import multiprocessing
from multiprocessing import Process

from flask import Flask, Response, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from realsense_rtmp_stream import RealsenseCapture

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

streams = []

app = Flask(__name__, 
    static_folder='web', 
    static_url_path='')
socketio = SocketIO(app)

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
    print('start ' + url)

    if len(streams) == 0:
        # Control parameters
        # =======================
        dir_path = os.path.dirname(os.path.realpath(__file__))
        json_file = dir_path + "/" + "MidResHighDensityPreset.json" # MidResHighDensityPreset.json / custom / MidResHighAccuracyPreset

        stream = RealsenseCapture( url, json_file, 640, 480 )
        playing = True        
        stream.start()
        streams.append(stream)

@socketio.on('stop')
def handle_stop():
    print('Stop')
    playing = False
    if len(streams) > 0:
        streams[0].terminate()
        streams[0].join()

@app.route('/')
def root():
    print('route')  
    return app.send_static_file('index.html')

def main():
    try:
        socketio.run(app)
    finally:
        if len(streams) > 0:
            playing = False
            print('shutdown')  

            streams[0].shutdown()
            print('join')  
            streams[0].join()

            print('done')  

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    main()

