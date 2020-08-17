#!python3

import numpy as np
import cv2
import os
import time
import pyrealsense2 as rs

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst


import tkinter
import cv2, PySimpleGUI as sg

from VideoGet import VideoGet


Gst.init(None)


def image_file_counter(path):
    files = 0
    for _, _, filenames in os.walk(path):
        files += len(filenames)
    return files + 1



# define global variables
# ========================
# file names and paths
rgb_img_path = 'captured_images/rgb_image/'
depth_img_path = 'captured_images/depth_image/'
colored_depth_img_path = 'captured_images/coloured_depth_image/'
intrinsics = True
rotate_camera = False


if __name__ == "__main__":
    
        window = sg.Window('Broadcaster', [[sg.Image(filename='', key='image')], ], location=(0, 0), grab_anywhere=True)
        TWITCH_KEY = os.getenv("TWITCH_KEY")

        RTMP_SERVER = "rtmp://live.twitch.tv/app/" + TWITCH_KEY
        CLI='appsrc name=mysource format=TIME do-timestamp=TRUE is-live=TRUE caps="video/x-raw,format=BGR,width=1280,height=480,framerate=(fraction)30/1,pixel-aspect-ratio=(fraction)1/1" ! videoconvert ! queue max-size-buffers=4 ! omxh264enc ! h264parse ! flvmux ! rtmpsink location="'+ RTMP_SERVER +'" sync=false'

        pipe=Gst.parse_launch(CLI)

        appsrc=pipe.get_by_name("mysource")
        #appsink=pipline.get_by_name("sink")
        appsrc.set_property('emit-signals',True) #tell sink to emit signals

        pipe.set_state(Gst.State.PLAYING)

        colorizer = rs.colorizer()
        colorizer.set_option(rs.option.color_scheme, 0)
        colorizer.set_option(rs.option.visual_preset, 1)
    
        isRecording = False
        video_getter = VideoGet().start()
        
        while window(timeout=20)[0] != sg.WIN_CLOSED:
           
            depth_frame = video_getter.depth_frame
            color_frame = video_getter.color_frame
            # print the camera intrinsics just once. it is always the same
            if intrinsics:
                print("Intel Realsense D435 Camera Intrinsics: ")
                print("========================================")
                print(depth_frame.profile.as_video_stream_profile().intrinsics)
                print(color_frame.profile.as_video_stream_profile().intrinsics)
                print("")
                intrinsics = False

            # =====================================
            # 9. Apply filtering to the depth image
            # =====================================
            # Apply a spatial filter without hole_filling (i.e. holes_fill=0)
            depth_frame = spatial_filtering(depth_frame, magnitude=2, alpha=0.5, delta=10, holes_fill=1)
            # Apply hole filling filter
            # depth_frame = hole_filling(depth_frame)

            # ===========================
            # 10. colourise the depth map
            # ===========================
            depth_color_frame = colorizer.colorize(depth_frame)

            # ==================================
            # 11. Convert images to numpy arrays
            # ==================================
            depth_image = np.asanyarray(depth_frame.get_data())
            depth_color_image = np.asanyarray(depth_color_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            # ======================================================================
            # 12. Only rotate the images if the realsense camera is placed vertical.
            # Otherwise set the variable "rotate_camera = False"
            # ======================================================================
            if rotate_camera:
                depth_image = np.rot90(depth_image, 3)
                depth_color_image = np.rot90(depth_color_image, 3)
                color_image = np.rot90(color_image, 3)

            grey_color = 0
            # depth_image_3d = np.dstack((depth_image, depth_image, depth_image))

            # bg_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), grey_color, color_image)

            # Stack rgb and depth map images horizontally for visualisation only
            images = np.hstack((color_image, depth_color_image))

            # Show horizontally stacked rgb and depth map images
            # cv2.namedWindow('RGB and Depth Map Images')
            # cv2.imshow('RGB and Depth Map Images', images)

            
            # sent = out_send.write(depth_color_image)

            # print(sent)
            frame = images.tostring()
            buf = Gst.Buffer.new_allocate(None, len(frame), None)
            buf.fill(0,frame)
            if isRecording:
                appsrc.emit("push-buffer", buf)
            
            c = cv2.waitKey(1)

            # window['image'](data=cv2.imencode('.png', images)[1].tobytes())
            print("FPS: ", 1.0 / (time.time() - start_time))
            # =============================================
            # If the 's' key is pressed, we save the images
            # =============================================
            if c == ord('s'):
                img_counter = image_file_counter(rgb_img_path)

                '''create a stream folders'''
                if not os.path.exists(rgb_img_path):
                    os.makedirs(rgb_img_path)
                if not os.path.exists(depth_img_path):
                    os.makedirs(depth_img_path)
                if not os.path.exists(colored_depth_img_path):
                    os.makedirs(colored_depth_img_path)

                filename = str(img_counter) + '.png'
                filename_csv = str(img_counter) + '.csv'

                np.savetxt(os.path.join(depth_img_path, filename_csv), np.array(depth_image), delimiter=",")

                filename_raw = str(img_counter) + '.raw'
                # save the rgb colour image
                cv2.imwrite(os.path.join(rgb_img_path, filename), color_image)
                # Save the depth image in raw binary format uint16.
                f = open(os.path.join(depth_img_path, filename_raw), mode='wb')
                depth_image.tofile(f)
                cv2.imwrite(os.path.join(colored_depth_img_path, filename), depth_color_image)

                print('images have been successfully saved')

            elif c == 27:  # esc to exit
                break


