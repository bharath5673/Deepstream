#!/usr/bin/env python3

################################################################################
# SPDX-FileCopyrightText: Copyright (c) 2019-2021 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import sys
sys.path.append('../')
import platform
import configparser

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.FPS import GETFPS
import pyds

fps_streams={}

PGIE_CLASS_ID_TOOTHBRUSH = 80
PGIE_CLASS_ID_HAIR_DRYER = 79
PGIE_CLASS_ID_TEDDY_BEAR = 78
PGIE_CLASS_ID_SCISSORS = 77
PGIE_CLASS_ID_VASE = 76
PGIE_CLASS_ID_CLOCK = 75
PGIE_CLASS_ID_BOOK = 74
PGIE_CLASS_ID_REFRIGERATOR = 73
PGIE_CLASS_ID_SINK = 72
PGIE_CLASS_ID_TOASTER = 71
PGIE_CLASS_ID_OVEN = 70
PGIE_CLASS_ID_MICROWAVE = 69
PGIE_CLASS_ID_CELL_PHONE = 68
PGIE_CLASS_ID_KEYBOARD = 67
PGIE_CLASS_ID_REMOTE = 66
PGIE_CLASS_ID_MOUSE = 65
PGIE_CLASS_ID_LAPTOP = 64
PGIE_CLASS_ID_TVMONITOR = 63
PGIE_CLASS_ID_TOILET = 62
PGIE_CLASS_ID_DININGTABLE= 61
PGIE_CLASS_ID_BED = 60
PGIE_CLASS_ID_POTTEDPLANT = 59
PGIE_CLASS_ID_SOFA = 58
PGIE_CLASS_ID_CHAIR = 57
PGIE_CLASS_ID_CAKE = 56
PGIE_CLASS_ID_DONUT = 55
PGIE_CLASS_ID_PIZZA = 54
PGIE_CLASS_ID_HOT_DOG = 53
PGIE_CLASS_ID_CARROT = 52
PGIE_CLASS_ID_BROCCOLI = 51
PGIE_CLASS_ID_ORANGE = 50
PGIE_CLASS_ID_SANDWICH = 49
PGIE_CLASS_ID_APPLE = 48
PGIE_CLASS_ID_BANANA = 47
PGIE_CLASS_ID_BOWL = 46
PGIE_CLASS_ID_SPOON = 45
PGIE_CLASS_ID_KNIFE = 44
PGIE_CLASS_ID_FORK = 43
PGIE_CLASS_ID_CUP = 42
PGIE_CLASS_ID_WINE_GLASS = 41
PGIE_CLASS_ID_BOTTLE = 40
PGIE_CLASS_ID_TENNIS_RACKET = 39
PGIE_CLASS_ID_SURFBOARD = 38
PGIE_CLASS_ID_SKATEBOARD = 37
PGIE_CLASS_ID_BASEBALL_GLOVE = 36
PGIE_CLASS_ID_BASEBALL_BAT = 35
PGIE_CLASS_ID_KITE = 34
PGIE_CLASS_ID_SPORTS_BALL = 33
PGIE_CLASS_ID_SNOWBOARD = 32
PGIE_CLASS_ID_SKIS = 31
PGIE_CLASS_ID_FRISBEE = 30
PGIE_CLASS_ID_SUITCASE = 29
PGIE_CLASS_ID_TIE = 28
PGIE_CLASS_ID_HANDBAG = 27
PGIE_CLASS_ID_UMBRELLA = 26
PGIE_CLASS_ID_BACKPACK = 25
PGIE_CLASS_ID_UMBRELLA = 24
PGIE_CLASS_ID_GIRAFFE = 23
PGIE_CLASS_ID_ZEBRA = 22
PGIE_CLASS_ID_BEAR = 21
PGIE_CLASS_ID_ELEPHANT = 20
PGIE_CLASS_ID_COW = 19
PGIE_CLASS_ID_SHEEP = 18
PGIE_CLASS_ID_HORSE = 17
PGIE_CLASS_ID_DOG = 16
PGIE_CLASS_ID_CAT = 15
PGIE_CLASS_ID_BIRD = 14
PGIE_CLASS_ID_BENCH = 13
PGIE_CLASS_ID_PARKING_METER = 12
PGIE_CLASS_ID_STOP_SIGN = 11
PGIE_CLASS_ID_FIRE_HYDRANT = 10
PGIE_CLASS_ID_TRAFFIC_LIGHT = 9
PGIE_CLASS_ID_BOAT = 8
PGIE_CLASS_ID_TRUCK = 7
PGIE_CLASS_ID_TRAIN = 6
PGIE_CLASS_ID_BUS = 5
PGIE_CLASS_ID_AEROPLANE = 4
PGIE_CLASS_ID_MOTORBIKE = 3
PGIE_CLASS_ID_VEHICLE = 2
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 0
past_tracking_meta=[0]

def osd_sink_pad_buffer_probe(pad,info,u_data):
    frame_number=0
    #Intiallizing object counter with 0.
    obj_counter = {
        PGIE_CLASS_ID_TOOTHBRUSH:0,
        PGIE_CLASS_ID_HAIR_DRYER:0,
        PGIE_CLASS_ID_TEDDY_BEAR:0,
        PGIE_CLASS_ID_SCISSORS:0,
        PGIE_CLASS_ID_VASE:0,
        PGIE_CLASS_ID_CLOCK:0,
        PGIE_CLASS_ID_BOOK:0,
        PGIE_CLASS_ID_REFRIGERATOR:0,
        PGIE_CLASS_ID_SINK:0,
        PGIE_CLASS_ID_TOASTER:0,
        PGIE_CLASS_ID_OVEN:0,
        PGIE_CLASS_ID_MICROWAVE:0,
        PGIE_CLASS_ID_CELL_PHONE:0,
        PGIE_CLASS_ID_KEYBOARD:0,
        PGIE_CLASS_ID_REMOTE:0,
        PGIE_CLASS_ID_MOUSE:0,
        PGIE_CLASS_ID_LAPTOP:0,
        PGIE_CLASS_ID_TVMONITOR:0,
        PGIE_CLASS_ID_TOILET:0,
        PGIE_CLASS_ID_DININGTABLE:0,
        PGIE_CLASS_ID_BED:0,
        PGIE_CLASS_ID_POTTEDPLANT:0,
        PGIE_CLASS_ID_SOFA:0,
        PGIE_CLASS_ID_CHAIR:0,
        PGIE_CLASS_ID_CAKE:0,
        PGIE_CLASS_ID_DONUT:0,
        PGIE_CLASS_ID_PIZZA:0,
        PGIE_CLASS_ID_HOT_DOG:0,
        PGIE_CLASS_ID_CARROT:0,
        PGIE_CLASS_ID_BROCCOLI:0,
        PGIE_CLASS_ID_ORANGE:0,
        PGIE_CLASS_ID_SANDWICH:0,
        PGIE_CLASS_ID_APPLE:0,
        PGIE_CLASS_ID_BANANA:0,
        PGIE_CLASS_ID_BOWL:0,
        PGIE_CLASS_ID_SPOON:0,
        PGIE_CLASS_ID_KNIFE:0,
        PGIE_CLASS_ID_FORK:0,
        PGIE_CLASS_ID_CUP:0,
        PGIE_CLASS_ID_WINE_GLASS:0,
        PGIE_CLASS_ID_BOTTLE:0,
        PGIE_CLASS_ID_TENNIS_RACKET:0,
        PGIE_CLASS_ID_SURFBOARD:0,
        PGIE_CLASS_ID_SKATEBOARD:0,
        PGIE_CLASS_ID_BASEBALL_GLOVE:0,
        PGIE_CLASS_ID_BASEBALL_BAT:0,
        PGIE_CLASS_ID_KITE:0,
        PGIE_CLASS_ID_SPORTS_BALL:0,
        PGIE_CLASS_ID_SNOWBOARD:0,
        PGIE_CLASS_ID_SKIS:0,
        PGIE_CLASS_ID_FRISBEE:0,
        PGIE_CLASS_ID_SUITCASE:0,
        PGIE_CLASS_ID_TIE:0,
        PGIE_CLASS_ID_HANDBAG:0,
        PGIE_CLASS_ID_UMBRELLA:0,
        PGIE_CLASS_ID_BACKPACK:0,
        PGIE_CLASS_ID_UMBRELLA:0,
        PGIE_CLASS_ID_GIRAFFE:0,
        PGIE_CLASS_ID_ZEBRA:0,
        PGIE_CLASS_ID_BEAR:0,
        PGIE_CLASS_ID_ELEPHANT:0,
        PGIE_CLASS_ID_COW:0,
        PGIE_CLASS_ID_SHEEP:0,
        PGIE_CLASS_ID_HORSE:0,
        PGIE_CLASS_ID_DOG:0,
        PGIE_CLASS_ID_CAT:0,
        PGIE_CLASS_ID_BIRD:0,
        PGIE_CLASS_ID_BENCH:0,
        PGIE_CLASS_ID_PARKING_METER:0,
        PGIE_CLASS_ID_STOP_SIGN:0,
        PGIE_CLASS_ID_FIRE_HYDRANT:0,
        PGIE_CLASS_ID_TRAFFIC_LIGHT:0,
        PGIE_CLASS_ID_BOAT:0,
        PGIE_CLASS_ID_TRUCK:0,
        PGIE_CLASS_ID_TRAIN:0,
        PGIE_CLASS_ID_BUS:0,
        PGIE_CLASS_ID_AEROPLANE:0,
        PGIE_CLASS_ID_MOTORBIKE:0,
        PGIE_CLASS_ID_VEHICLE:0,
        PGIE_CLASS_ID_BICYCLE:0,
        PGIE_CLASS_ID_PERSON:0
    }

    num_rects=0
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    # Retrieve batch metadata from the gst_buffer
    # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
    # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
            # The casting is done by pyds.NvDsFrameMeta.cast()
            # The casting also keeps ownership of the underlying memory
            # in the C code, so the Python garbage collector will leave
            # it alone.
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        frame_number=frame_meta.frame_num
        num_rects = frame_meta.num_obj_meta
        l_obj=frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta=pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            obj_counter[obj_meta.class_id] += 1
            try: 
                l_obj=l_obj.next
            except StopIteration:
                break


        # Acquiring a display meta object. The memory ownership remains in
        # the C code so downstream plugins can still access it. Otherwise
        # the garbage collector will claim it when this probe function exits.
        display_meta=pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 1
        py_nvosd_text_params = display_meta.text_params[0]
        # Setting display text to be shown on screen
        # Note that the pyds module allocates a buffer for the string, and the
        # memory will not be claimed by the garbage collector.
        # Reading the display_text field here will return the C address of the
        # allocated string. Use pyds.get_string() to get the string content.
        py_nvosd_text_params.display_text = "Frame Number={} Number of Objects={} Car_count={} Person_count={}".format(frame_number, num_rects, obj_counter[PGIE_CLASS_ID_VEHICLE], obj_counter[PGIE_CLASS_ID_PERSON])

        # Now set the offsets where the string should appear
        py_nvosd_text_params.x_offset = 10
        py_nvosd_text_params.y_offset = 12

        # Font , font-color and font-size
        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 10
        # set(red, green, blue, alpha); set to White
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

        # Text background color
        py_nvosd_text_params.set_bg_clr = 1
        # set(red, green, blue, alpha); set to Black
        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
        # Using pyds.get_string() to get display_text as string
        # print(pyds.get_string(py_nvosd_text_params.display_text))
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        fps_streams["stream{0}".format(frame_meta.pad_index)].get_fps()

        try:
            l_frame=l_frame.next
        except StopIteration:
            break
    #past traking meta data
    if(past_tracking_meta[0]==1):
        l_user=batch_meta.batch_user_meta_list
        while l_user is not None:
            try:
                # Note that l_user.data needs a cast to pyds.NvDsUserMeta
                # The casting is done by pyds.NvDsUserMeta.cast()
                # The casting also keeps ownership of the underlying memory
                # in the C code, so the Python garbage collector will leave
                # it alone
                user_meta=pyds.NvDsUserMeta.cast(l_user.data)
            except StopIteration:
                break
            if(user_meta and user_meta.base_meta.meta_type==pyds.NvDsMetaType.NVDS_TRACKER_PAST_FRAME_META):
                try:
                    # Note that user_meta.user_meta_data needs a cast to pyds.NvDsPastFrameObjBatch
                    # The casting is done by pyds.NvDsPastFrameObjBatch.cast()
                    # The casting also keeps ownership of the underlying memory
                    # in the C code, so the Python garbage collector will leave
                    # it alone
                    pPastFrameObjBatch = pyds.NvDsPastFrameObjBatch.cast(user_meta.user_meta_data)
                except StopIteration:
                    break
                for trackobj in pyds.NvDsPastFrameObjBatch.list(pPastFrameObjBatch):
                    print("streamId=",trackobj.streamID)
                    print("surfaceStreamID=",trackobj.surfaceStreamID)
                    for pastframeobj in pyds.NvDsPastFrameObjStream.list(trackobj):
                        print("numobj=",pastframeobj.numObj)
                        print("uniqueId=",pastframeobj.uniqueId)
                        print("classId=",pastframeobj.classId)
                        print("objLabel=",pastframeobj.objLabel)
                        for objlist in pyds.NvDsPastFrameObjList.list(pastframeobj):
                            print('frameNum:', objlist.frameNum)
                            print('tBbox.left:', objlist.tBbox.left)
                            print('tBbox.width:', objlist.tBbox.width)
                            print('tBbox.top:', objlist.tBbox.top)
                            print('tBbox.right:', objlist.tBbox.height)
                            print('confidence:', objlist.confidence)
                            print('age:', objlist.age)
            try:
                l_user=l_user.next
            except StopIteration:
                break
    return Gst.PadProbeReturn.OK	

def main(args):
    # Check input arguments
    if(len(args)<2):
        sys.stderr.write("usage: %s <h264_elementary_stream> [0/1]\n" % args[0])
        sys.exit(1)

    for i in range(0,len(args)-1):
        fps_streams["stream{0}".format(i)]=GETFPS(i)
    number_sources=len(args)-1

    # Standard GStreamer initialization
    if(len(args)==3):
        past_tracking_meta[0]=int(args[2])
    Gst.init(None)

    # Create gstreamer elements
    # Create Pipeline element that will form a connection of other elements
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()

    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")

    # Source element for reading from the file
    print("Creating Source \n ")
    source = Gst.ElementFactory.make("filesrc", "file-source")
    if not source:
        sys.stderr.write(" Unable to create Source \n")

    # Since the data format in the input file is elementary h264 stream,
    # we need a h264parser
    print("Creating H264Parser \n")
    h264parser = Gst.ElementFactory.make("h264parse", "h264-parser")
    if not h264parser:
        sys.stderr.write(" Unable to create h264 parser \n")

    # Use nvdec_h264 for hardware accelerated decode on GPU
    print("Creating Decoder \n")
    decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder")
    if not decoder:
        sys.stderr.write(" Unable to create Nvv4l2 Decoder \n")

    # Create nvstreammux instance to form batches from one or more sources.
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux \n")

    # Use nvinfer to run inferencing on decoder's output,
    # behaviour of inferencing is set through config file
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")

    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    if not tracker:
        sys.stderr.write(" Unable to create tracker \n")

    sgie1 = Gst.ElementFactory.make("nvinfer", "secondary1-nvinference-engine")
    if not sgie1:
        sys.stderr.write(" Unable to make sgie1 \n")


    sgie2 = Gst.ElementFactory.make("nvinfer", "secondary2-nvinference-engine")
    if not sgie2:
        sys.stderr.write(" Unable to make sgie2 \n")

    sgie3 = Gst.ElementFactory.make("nvinfer", "secondary3-nvinference-engine")
    if not sgie3:
        sys.stderr.write(" Unable to make sgie3 \n")

    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")

    # Create OSD to draw on the converted RGBA buffer
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")

    if not nvosd:
        sys.stderr.write(" Unable to create nvosd \n")

    # Finally render the osd output
    if is_aarch64():
        transform = Gst.ElementFactory.make("nvegltransform", "nvegl-transform")

    print("Creating EGLSink \n")
    sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
    if not sink:
        sys.stderr.write(" Unable to create egl sink \n")

    print("Playing file %s " %args[1])
    source.set_property('location', args[1])
    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 2000000)

    #Set properties of pgie
    pgie.set_property('config-file-path', "../DeepStream-Configs/DeepStream-Yolo/config_infer_primary_yoloV5.txt")
    # pgie.set_property('config-file-path', "../DeepStream-Configs/DeepStream-Yolo/config_infer_primary_yoloV8.txt")


    #Set properties of tracker
    config = configparser.ConfigParser()
    config.read('../DeepStream-Configs/test/tracker_config.txt')    
    config.sections()

    for key in config['tracker']:
        if key == 'tracker-width' :
            tracker_width = config.getint('tracker', key)
            tracker.set_property('tracker-width', tracker_width)
        if key == 'tracker-height' :
            tracker_height = config.getint('tracker', key)
            tracker.set_property('tracker-height', tracker_height)
        if key == 'gpu-id' :
            tracker_gpu_id = config.getint('tracker', key)
            tracker.set_property('gpu_id', tracker_gpu_id)
        if key == 'll-lib-file' :
            tracker_ll_lib_file = config.get('tracker', key)
            tracker.set_property('ll-lib-file', tracker_ll_lib_file)
        if key == 'll-config-file' :
            tracker_ll_config_file = config.get('tracker', key)
            tracker.set_property('ll-config-file', tracker_ll_config_file)
        if key == 'enable-batch-process' :
            tracker_enable_batch_process = config.getint('tracker', key)
            # tracker.set_property('enable_batch_process', tracker_enable_batch_process)
        if key == 'enable-past-frame' :
            tracker_enable_past_frame = config.getint('tracker', key)
            tracker.set_property('enable_past_frame', tracker_enable_past_frame)

    print("Adding elements to Pipeline \n")
    pipeline.add(source)
    pipeline.add(h264parser)
    pipeline.add(decoder)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(nvvidconv)
    pipeline.add(nvosd)
    pipeline.add(sink)
    if is_aarch64():
        pipeline.add(transform)

    # we link the elements together
    # file-source -> h264-parser -> nvh264-decoder ->
    # nvinfer -> nvvidconv -> nvosd -> video-renderer
    print("Linking elements in the Pipeline \n")
    source.link(h264parser)
    h264parser.link(decoder)

    sinkpad = streammux.get_request_pad("sink_0")
    if not sinkpad:
        sys.stderr.write(" Unable to get the sink pad of streammux \n")
    srcpad = decoder.get_static_pad("src")
    if not srcpad:
        sys.stderr.write(" Unable to get source pad of decoder \n")
    srcpad.link(sinkpad)
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(nvvidconv)
    nvvidconv.link(nvosd)
    if is_aarch64():
        nvosd.link(transform)
        transform.link(sink)
    else:
        nvosd.link(sink)


    # create and event loop and feed gstreamer bus mesages to it
    loop = GLib.MainLoop()

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)

    # Lets add probe to get informed of the meta data generated, we add probe to
    # the sink pad of the osd element, since by that time, the buffer would have
    # had got all the metadata.
    osdsinkpad = nvosd.get_static_pad("sink")
    if not osdsinkpad:
        sys.stderr.write(" Unable to get sink pad of nvosd \n")
    osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)


    print("Starting pipeline \n")
    
    # start play back and listed to events
    pipeline.set_state(Gst.State.PLAYING)
    try:
      loop.run()
    except:
      pass

    # cleanup
    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))

