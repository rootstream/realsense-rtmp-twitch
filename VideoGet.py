from threading import Thread
import cv2
import pyrealsense2 as rs
import json
import time

class VideoGet:
    """
    Class that continuously gets frames from a VideoCapture object
    with a dedicated thread.
    """

    # Control parameters
    # =======================
    clipping_distance_in_meters = 1.5  # 1.5 meters
    # ======================


    def loadConfiguration(self, profile, json_file):
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


    def spatial_filtering(self, depth_frame, magnitude=2, alpha=0.5, delta=20, holes_fill=0):
        spatial = rs.spatial_filter()
        spatial.set_option(rs.option.filter_magnitude, magnitude)
        spatial.set_option(rs.option.filter_smooth_alpha, alpha)
        spatial.set_option(rs.option.filter_smooth_delta, delta)
        spatial.set_option(rs.option.holes_fill, holes_fill)
        depth_frame = spatial.process(depth_frame)
        return depth_frame


    def hole_filling(self, depth_frame):
        hole_filling = rs.hole_filling_filter()
        depth_frame = hole_filling.process(depth_frame)
        return depth_frame


    def __init__(self, src=0):
        # self.stream = cv2.VideoCapture(src)

        # ========================
        # 1. Configure all streams
        # ========================

        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # ======================
        # 2. Start the streaming
        # ======================
        print("Starting up the Intel Realsense D435...")
        print("")
        profile = self.pipeline.start(config)
        
        json_file = "MidResHighDensityPreset.json" # MidResHighDensityPreset.json / custom / MidResHighAccuracyPreset

        # Load the configuration here
        self.loadConfiguration(profile, json_file)

        # =================================
        # 3. The depth sensor's depth scale
        # =================================
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        print("Depth Scale is: ", depth_scale)
        print("")

        clipping_distance = self.clipping_distance_in_meters / depth_scale

        # ==========================================
        # 4. Create an align object.
        #    Align the depth image to the rgb image.
        # ==========================================
        align_to = rs.stream.color
        self.align = rs.align(align_to)
        
        self.stopped = False
            
        # finally:
            # Stop streaming
            # self.pipeline.stop()


    def start(self):    
        Thread(target=self.get, args=()).start()
        return self

    def get(self):
        # ===========================================
        # 5. Skip the first 30 frames.
        # This gives the Auto-Exposure time to adjust
        # ===========================================
        for x in range(50):
            frames = self.pipeline.wait_for_frames()
            # Align the depth frame to color frame
            aligned_frames = self.align.process(frames)

        print("Intel Realsense D435 started successfully.")
        print("")
        while not self.stopped:
            start_time = time.time()
            # ======================================
            # 6. Wait for a coherent pair of frames:
            # ======================================
            frames = self.pipeline.wait_for_frames()

            # =======================================
            # 7. Align the depth frame to color frame
            # =======================================
            aligned_frames = self.align.process(frames)

            # ================================================
            # 8. Fetch the depth and colour frames from stream
            # ================================================
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            if not depth_frame or not color_frame:
                continue
            self.depth_frame = depth_frame
            self.color_frame = color_frame


    def stop(self):
        self.stopped = True