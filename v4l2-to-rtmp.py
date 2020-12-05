#!/usr/bin/env python

from prctl import set_name

set_name("v4l2-to-rtmp")


import sys, os
import time
from datetime import datetime


V4L2_DEVICE="/dev/video0"
V4L2_CHANNEL_NUMBER=0
V4L2_NORM = 0

VIDEOSCALE='video/x-raw-yuv, framerate=25/1'

VIDEOCROP_LEFT = 0
VIDEOCROP_RIGHT = 0
VIDEOCROP_BOTTOM = 0
VIDEOCROP_TOP = 0

X264_KEY_INT_MAX=25
X264_PRESET=2
X264_BITRATE=600
X264_QUANTIZER=22

ALSA_DEVICE="hw:0"
AUDIOCONVERT="audio/x-raw-int,rate=44100,channels=2"

RTMPSINK_LOCATION = "rtmp://10.14.10.102:1935/rtmp/output live=output"
FILESINK_LOCATION = "output.flv"

RECORD_TIME = 7200

from optparse import OptionParser

parser = OptionParser()
parser.add_option("-d", "--device", dest="V4L2_DEVICE",
                  help="v4l2 device (" + str(V4L2_DEVICE) + ")",
                  default=V4L2_DEVICE)
parser.add_option("-c", "--channel", dest="V4L2_CHANNEL_NUMBER",
                  help="v4l2 channel (" + str(V4L2_CHANNEL_NUMBER) + ")",
                  default=V4L2_CHANNEL_NUMBER)
parser.add_option("-n", "--norm", dest="V4L2_NORM",
                  help="v4l2 norm (" + str(V4L2_NORM) + ")",
                  default=V4L2_NORM)

parser.add_option("-L", "--videocropleft", dest="VIDEOCROP_LEFT",
                  help="videocrop left (" + str(VIDEOCROP_LEFT) + ")",
                  default=VIDEOCROP_LEFT)
parser.add_option("-R", "--videocropright", dest="VIDEOCROP_RIGHT",
                  help="videocrop right (" + str(VIDEOCROP_RIGHT) + ")",
                  default=VIDEOCROP_RIGHT)
parser.add_option("-T", "--videocroptop", dest="VIDEOCROP_TOP",
                  help="videocrop top (" + str(VIDEOCROP_TOP) + ")",
                  default=VIDEOCROP_TOP)
parser.add_option("-B", "--videocropbottom", dest="VIDEOCROP_BOTTOM",
                  help="videocrop bottom (" + str(VIDEOCROP_BOTTOM) + ")",
                  default=VIDEOCROP_BOTTOM)





parser.add_option("-s", "--videoscale", dest="VIDEOSCALE",
                  help="videoscale filter (" + str(VIDEOSCALE) + ")",
                  default=VIDEOSCALE)

parser.add_option("-b", "--bitrate", dest="X264_BITRATE",
                  help="x264enc bitrate (" + str(X264_BITRATE) + ")",
                  default=X264_BITRATE)
parser.add_option("-p", "--preset", dest="X264_PRESET",
                  help="x264enc preset (" + str(X264_PRESET) + ")",
                  default=X264_PRESET)
parser.add_option("-k", "--keyframes", dest="X264_KEY_INT_MAX",
                  help="x264enc key int max (" + str(X264_KEY_INT_MAX) + ")",
                  default=X264_KEY_INT_MAX)
parser.add_option("-q", "--quantizer", dest="X264_QUANTIZER",
                  help="x264enc quantizer (" + str(X264_QUANTIZER) + ")",
                  default=X264_QUANTIZER)

parser.add_option("-A", "--alsadevice", dest="ALSA_DEVICE",
                  help="Alsa device (" + str(ALSA_DEVICE) + ")",
                  default=ALSA_DEVICE)
parser.add_option("-a", "--audioconvert", dest="AUDIOCONVERT",
                  help="audioconvert filter (" + str(AUDIOCONVERT) + ")",
                  default=AUDIOCONVERT)

parser.add_option("-f", "--filename", dest="FILESINK_LOCATION",
                  help="filename (" + str(FILESINK_LOCATION) + ")",
                  default=FILESINK_LOCATION)
parser.add_option("-l", "--livestream", dest="RTMPSINK_LOCATION",
                  help="livestream (" + str(RTMPSINK_LOCATION) + ")",
                  default=RTMPSINK_LOCATION)

parser.add_option("-r", "--recordtime", dest="RECORD_TIME",
                  help="Time recording (" + str(RECORD_TIME) + ")",
                  default=RECORD_TIME)



(ops, args) = parser.parse_args()



# import pygst
# pygst.require("0.10")

import gobject
gobject.threads_init()
import gst
# gst.debug_set_active(True)
# gst.debug_set_default_threshold(4)
#  http://wiki.oz9aec.net/index.php/Gstreamer_cheat_sheet



player = gst.Pipeline("player")
print (player)

v4l2src = gst.element_factory_make("v4l2src", "v4l2src")
v4l2src.set_property("device", ops.V4L2_DEVICE )
v4l2src.set_property("norm", int(ops.V4L2_NORM) )
# TODO:  brigthness, contrast, saturation, hue

try:
    # print v4l2src.get_state()
    v4l2src.set_state(gst.STATE_PAUSED)
    # print v4l2src.get_state()
    # print v4l2src.list_channels()
    c = v4l2src.list_channels()[int(ops.V4L2_CHANNEL_NUMBER)]
    v4l2src.set_channel(c)
    v4l2src.set_state(gst.STATE_READY)
    # v4l2src.set_state(gst.STATE_NULL)
    # print v4l2src.get_state()
except  e:
    # print "Unable change v4l2 channel: %s" % ops.V4L2_CHANNEL_NUMBER
    v4l2src.set_state(gst.STATE_NULL)
    # print v4l2src.get_state()


videorate = gst.element_factory_make("videorate", "videorate")
videorate_filter = gst.element_factory_make("capsfilter", "videorate_filter")

videocrop = gst.element_factory_make("videocrop", "videocrop")
videocrop.set_property("right", int(ops.VIDEOCROP_RIGHT) )
videocrop.set_property("left", int(ops.VIDEOCROP_LEFT) )
videocrop.set_property("top", int(ops.VIDEOCROP_TOP) )
videocrop.set_property("bottom", int(ops.VIDEOCROP_BOTTOM) )

videoscale = gst.element_factory_make("videoscale", "videoscale")
videoscale_filter = gst.element_factory_make("capsfilter", "videoscale_filter")
videoscale_filter.set_property('caps',
    gst.caps_from_string(ops.VIDEOSCALE))




x264enc = gst.element_factory_make("x264enc", "x264enc")
x264enc.set_property("sliced-threads",True )
x264enc.set_property("cabac",True )
x264enc.set_property("intra-refresh",False )
x264enc.set_property("quantizer", int(ops.X264_QUANTIZER) )
x264enc.set_property("rc-lookahead",15 )
x264enc.set_property("bitrate",int(ops.X264_BITRATE) )
x264enc.set_property("tune","zerolatency" )
x264enc.set_property("byte-stream", False)
x264enc.set_property("key-int-max", int(ops.X264_KEY_INT_MAX))
x264enc.set_property("speed-preset", int(ops.X264_PRESET))




alsasrc = gst.element_factory_make("alsasrc", "alsasrc")
alsasrc.set_property("device", ops.ALSA_DEVICE)
audioconvert = gst.element_factory_make("audioconvert", "audioconvert")
audioconvert_filter = gst.element_factory_make("capsfilter", "audioconvert_filter")
audioconvert_filter.set_property('caps',
    gst.caps_from_string(ops.AUDIOCONVERT))




ffenc_aac = gst.element_factory_make("ffenc_aac", "ffenc_aac")




videoscale_q = gst.element_factory_make("queue", "videoscale_q")
videoscale_q.set_property("leaky", True)
audio0_q = gst.element_factory_make("queue", "audio0_q")
audio0_q.set_property("leaky", True)
video0_q = gst.element_factory_make("queue", "video0_q")
video0_q.set_property("leaky", True)
audio1_q = gst.element_factory_make("queue", "audio1_q")
audio1_q.set_property("leaky", True)
video1_q = gst.element_factory_make("queue", "video1_q")
video1_q.set_property("leaky", True)
filesink_q = gst.element_factory_make("queue", "filesink_q")
filesink_q.set_property("leaky", True)
rtmpsink_q = gst.element_factory_make("queue", "rtmpsink_q")
rtmpsink_q.set_property("leaky", True)




flvmux = gst.element_factory_make("flvmux", "flvmux")
tee = gst.element_factory_make("tee", "tee")




rtmpsink  = gst.element_factory_make("rtmpsink", "rtmpsink")
rtmpsink.set_property("location", ops.RTMPSINK_LOCATION)


filesink = gst.element_factory_make("filesink", "filesink")
filesink.set_property("location",ops.FILESINK_LOCATION)




player.add(v4l2src,videorate,videocrop,videorate_filter,videoscale,videoscale_filter)
player.add(x264enc)
player.add(alsasrc,audioconvert,audioconvert_filter,ffenc_aac)
player.add(videoscale_q,audio0_q,audio1_q,video0_q,video1_q)
player.add(flvmux,tee)
player.add(filesink,rtmpsink)
player.add(filesink_q,rtmpsink_q)




gst.element_link_many(alsasrc, audio0_q, audioconvert, audioconvert_filter,\
        ffenc_aac, audio1_q)
gst.element_link_many(v4l2src,videorate, videocrop, videorate_filter,\
        videoscale_q, videoscale,videoscale_filter,video0_q,x264enc,video1_q)

audio1_q.link(flvmux)
video1_q.link(flvmux)

flvmux.link(tee)

tee.link(filesink_q)
tee.link(rtmpsink_q)
tee.set_state(gst.STATE_PLAYING)

filesink_q.link(filesink)
rtmpsink_q.link(rtmpsink)


print ("Playing")
player.set_state(gst.STATE_PLAYING)

# import gobject
# 
# loop = gobject.MainLoop()
# context = loop.get_context()
# 
# while 1:
#     # Handle commands here
#     context.iteration(True)


# print "Stopped"
# player.set_state(gst.STATE_NULL)

time.sleep(int(ops.RECORD_TIME))