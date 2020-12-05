#!python3

import pyrealsense2 as rs
import numpy as np
import cv2
import os
import json
import time
import platform
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

Gst.init(None)

dir_path = os.path.dirname(os.path.realpath(__file__))

key = open(dir_path + "/.key").read()

# Control parameters
# =======================
json_file = dir_path + "/" + "MidResHighDensityPreset.json" # MidResHighDensityPreset.json / custom / MidResHighAccuracyPreset
clipping_distance_in_meters = 1.5  # 1.5 meters
# ======================


def image_file_counter(path):
    files = 0
    for _, _, filenames in os.walk(path):
        files += len(filenames)
    return files + 1


def loadConfiguration(profile, json_file):
    dev = profile.get_device()
    advnc_mode = rs.rs400_advanced_mode(dev)
    print("Advanced mode is", "enabled" if advnc_mode.is_enabled() else "disabled")
    json_obj = json.load(open(json_file))
    json_string = str(json_obj).replace("'", '\"')
    advnc_mode.load_json(json_string)

    while not advnc_mode.is_enabled():
        print("Trying to enable advanced mode...")
        advnc_mode.toggle_advanced_mode(True)

        # At this point the device will disconnect and re-connect.
        print("Sleeping for 5 seconds...")
        time.sleep(5)

        # The 'dev' object will become invalid and we need to initialize it again
        dev = profile.get_device()
        advnc_mode = rs.rs400_advanced_mode(dev)
        print("Advanced mode is", "enabled" if advnc_mode.is_enabled() else "disabled")
        advnc_mode.load_json(json_string)


def spatial_filtering(depth_frame, magnitude=2, alpha=0.5, delta=20, holes_fill=0):
    spatial = rs.spatial_filter()
    spatial.set_option(rs.option.filter_magnitude, magnitude)
    spatial.set_option(rs.option.filter_smooth_alpha, alpha)
    spatial.set_option(rs.option.filter_smooth_delta, delta)
    spatial.set_option(rs.option.holes_fill, holes_fill)
    depth_frame = spatial.process(depth_frame)
    return depth_frame

dbg = True

def hole_filling(depth_frame):
    hole_filling = rs.hole_filling_filter()
    depth_frame = hole_filling.process(depth_frame)
    return depth_frame

def on_bus_message(message):
    print("on_bus_message")
    t = message.type
    if t == Gst.MessageType.EOS:
        print("Eos")
    elif t == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        print('Warning: %s: %s\n' % (err, debug))
        #sys.stderr.write('Warning: %s: %s\n' % (err, debug))
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print('Error: %s: %s\n' % (err, debug))
        #sys.stderr.write('Error: %s: %s\n' % (err, debug))   
    
    return True

# define global variables
# ========================
# file names and paths
rgb_img_path = 'captured_images/rgb_image/'
depth_img_path = 'captured_images/depth_image/'
colored_depth_img_path = 'captured_images/coloured_depth_image/'
intrinsics = True
rotate_camera = False
width = 640
height = 480

if __name__ == "__main__":
        # ========================
    # 1. Configure all streams
    # ========================
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, width, height, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, 30)

    # ======================
    # 2. Start the streaming
    # ======================
    print("Starting up the Intel Realsense...")
    print("")
    profile = pipeline.start(config)

    # Load the configuration here
    loadConfiguration(profile, json_file)

    # =================================
    # 3. The depth sensor's depth scale
    # =================================
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    print("Depth Scale is: ", depth_scale)
    print("")

    clipping_distance = clipping_distance_in_meters / depth_scale

    # ==========================================
    # 4. Create an align object.
    #    Align the depth image to the rgb image.
    # ==========================================
    align_to = rs.stream.depth
    align = rs.align(align_to)

    try:
        # ===========================================
        # 5. Skip the first 30 frames.
        # This gives the Auto-Exposure time to adjust
        # ===========================================
        for x in range(50):
            frames = pipeline.wait_for_frames()
            # Align the depth frame to color frame
            aligned_frames = align.process(frames)

        print("Intel Realsense started successfully.")
        print("")

        # ===========================================
        # Setup gstreamer
        # Usefull gst resources / cheatsheets
        # https://github.com/matthew1000/gstreamer-cheat-sheet/blob/master/rtmp.md
        # http://wiki.oz9aec.net/index.php/Gstreamer_cheat_sheet
        # https://github.com/matthew1000/gstreamer-cheat-sheet/blob/master/mixing.md
        # ===========================================
        RTMP_SERVER = key
        CLI = ''

        if platform.system() == "Linux":
            #assuming Linux means RPI
            CLI='appsrc name=mysource format=TIME do-timestamp=TRUE is-live=TRUE caps="video/x-raw,format=BGR,width='+str(width)+',height='+ str(height*2) + ',framerate=(fraction)30/1,pixel-aspect-ratio=(fraction)1/1" ! videoconvert ! omxh264enc ! video/x-h264 ! h264parse ! video/x-h264 ! queue ! flvmux name=mux ! rtmpsink location="'+ RTMP_SERVER +'" alsasrc ! audioconvert ! audioresample ! audio/x-raw,rate=48000 ! voaacenc ! audio/mpeg ! aacparse ! audio/mpeg, mpegversion=4 ! mux.'

        elif platform.system() == "Darwin":
            #macos
            CLI='appsrc name=mysource format=TIME do-timestamp=TRUE is-live=TRUE caps="video/x-raw,format=BGR,width='+str(width)+',height='+ str(height*2) + ',framerate=(fraction)30/1,pixel-aspect-ratio=(fraction)1/1" ! videoconvert ! vtenc_h264 ! video/x-h264 ! h264parse ! video/x-h264 ! queue max-size-buffers=4 ! flvmux name=mux ! rtmpsink location="'+ RTMP_SERVER +'" sync=true   osxaudiosrc do-timestamp=true ! audioconvert ! audioresample ! audio/x-raw,rate=48000 ! faac bitrate=48000 ! audio/mpeg ! aacparse ! audio/mpeg, mpegversion=4 ! queue max-size-buffers=4 ! mux.'

        #todo: windows

        print( CLI )
        pipe=Gst.parse_launch(CLI)

        appsrc=pipe.get_by_name("mysource")
        appsrc.set_property('emit-signals',True) #tell sink to emit signals

         # Set up a pipeline bus watch to catch errors.
        bus = pipe.get_bus()
        bus.connect("message", on_bus_message)

        pipe.set_state(Gst.State.PLAYING)

        while True:
            # ======================================
            # 6. Wait for a coherent pair of frames:
            # ======================================
            frames = pipeline.wait_for_frames()

            # =======================================
            # 7. Align the depth frame to color frame
            # =======================================
            aligned_frames = align.process(frames)

            # ================================================
            # 8. Fetch the depth and colour frames from stream
            # ================================================
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            if not depth_frame or not color_frame:
                continue

            # print the camera intrinsics just once. it is always the same
            if intrinsics:
                print("Intel Realsense Camera Intrinsics: ")
                print("========================================")
                print(depth_frame.profile.as_video_stream_profile().intrinsics)
                print(color_frame.profile.as_video_stream_profile().intrinsics)
                print("")
                intrinsics = False

            # =====================================
            # 9. Apply filtering to the depth image
            # =====================================
            # Apply a spatial filter without hole_filling (i.e. holes_fill=0)
            # depth_frame = spatial_filtering(depth_frame, magnitude=2, alpha=0.5, delta=10, holes_fill=1)
            # Apply hole filling filter
            # depth_frame = hole_filling(depth_frame)

            # ==================================
            # 11. Convert images to numpy arrays
            # ==================================
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            # ======================================================================
            # 12. Only rotate the images if the realsense camera is placed vertical.
            # Otherwise set the variable "rotate_camera = False"
            # ======================================================================
            if rotate_camera:
                depth_image = np.rot90(depth_image, 3)
                color_image = np.rot90(color_image, 3)

            # grey_color = 0
            # depth_image_3d = np.dstack((depth_image, depth_image, depth_image))
            # bg_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), grey_color, color_image)

            # We need to encode/pack the 16bit depth value to RGB
            # we do this by treating it as the Hue in HSV. 
            # we then encode HSV to RGB and stream that
            # on the other end we reverse RGB to HSV, H will give us the depth value back.
            # HSV elements are in the 0-1 range so we need to normalize the depth array to 0-1
            # First set a far plane and set everything beyond that to 0

            clipped = depth_image > 4000
            depth_image[clipped] = 0

            # Now normalize using that far plane
            # cv expects the H in degrees, not 0-1 :(
            depth_image_norm = (depth_image * (360/4000)).astype( np.float32)

            # Create 3 dimensional HSV array where H=depth, S=1, V=1
            depth_hsv = np.concatenate([depth_image_norm[..., np.newaxis]]*3, axis=2)
            #depth_hsv[:,:,0] = 1
            depth_hsv[:,:,1] = 1
            depth_hsv[:,:,2] = 1

            discard = depth_image_norm == 0
            s = depth_hsv[:,:,1]
            v = depth_hsv[:,:,2] 
            s[ discard] = 0
            v[ discard] = 0

            # cv2.cvtColor to convert HSV to RGB
            # problem is that cv2 expects hsv to 8bit (0-255)
            hsv = cv2.cvtColor(depth_hsv, cv2.COLOR_HSV2BGR)
            hsv8 = (hsv*255).astype( np.uint8)

            # Stack rgb and depth map images horizontally for visualisation only
            images = np.vstack((color_image, hsv8))

            # push to gstreamer
            frame = images.tostring()
            buf = Gst.Buffer.new_allocate(None, len(frame), None)
            buf.fill(0,frame)
            appsrc.emit("push-buffer", buf)

            msg = bus.pop_filtered(
                Gst.MessageType.ERROR | Gst.MessageType.EOS
            )

            while( msg ): 
                on_bus_message(msg)
                msg = bus.pop_filtered(
                    Gst.MessageType.ERROR | Gst.MessageType.EOS
                )

            cv2.namedWindow('RGB and Depth Map Images')
            images = cv2.resize(images, (width, height*2), interpolation = cv2.INTER_AREA)
            cv2.imshow('RGB and Depth Map Images', images)
            c = cv2.waitKey(1)

            # =============================================
            # If the 's' key is pressed, we save the images
            # =============================================
            if c == ord('s'):
                print('stop')

            elif c == ord('p'):
                print('pause')
                pipe.set_state(Gst.State.NULL)

            elif c == 27:  # esc to exit
                break

    finally:
        # Stop streaming
        pipeline.stop()
