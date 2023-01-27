#!/usr/bin/env python3


### usage -python3 deepstream_test_yolo_save_vid_multistream.py file:///home/acer/Desktop/Projects/Deepstream-Projects/people_test/1664187275275.h264 file:///home/acer/Desktop/Projects/Deepstream-Projects/people_test/1664187275275.h264

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
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.FPS import GETFPS

import configparser

import pyds
import os



fps_streams={}
PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3
past_tracking_meta=[0]




def osd_sink_pad_buffer_probe(pad,info,u_data):
    frame_number=0
    #Intiallizing object counter with 0.
    obj_counter = {
        PGIE_CLASS_ID_VEHICLE:0,
        PGIE_CLASS_ID_PERSON:0,
        PGIE_CLASS_ID_BICYCLE:0,
        PGIE_CLASS_ID_ROADSIGN:0
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
        py_nvosd_text_params.display_text = "Frame Number={} Number of Objects={} Vehicle_count={} Person_count={}".format(frame_number, num_rects, obj_counter[PGIE_CLASS_ID_VEHICLE], obj_counter[PGIE_CLASS_ID_PERSON])


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
        print(pyds.get_string(py_nvosd_text_params.display_text))
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
    # print(obj_counter)
    #logging.info(obj_counter)
    return Gst.PadProbeReturn.OK    

def cb_newpad(decodebin, decoder_src_pad,data):
    print("In cb_newpad\n")
    caps=decoder_src_pad.get_current_caps()
    gststruct=caps.get_structure(0)
    gstname=gststruct.get_name()
    source_bin=data
    features=caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    print("gstname=",gstname)
    if(gstname.find("video")!=-1):
        # Link the decodebin pad only if decodebin has picked nvidia
        # decoder plugin nvdec_*. We do this by checking if the pad caps contain
        # NVMM memory features.
        print("features=",features)
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad=source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
        else:
            sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")

def decodebin_child_added(child_proxy,Object,name,user_data):
    print("Decodebin child added:", name, "\n")
    if(name.find("decodebin") != -1):
        Object.connect("child-added",decodebin_child_added,user_data)

    # if "source" in name:
    #     Object.set_property("drop-on-latency", True)


def create_source_bin(index,uri):
    print("Creating source bin")

    # Create a source GstBin to abstract this bin's content from the rest of the
    # pipeline
    bin_name="source-bin-%02d" %index
    print(bin_name)
    nbin=Gst.Bin.new(bin_name)
    if not nbin:
        sys.stderr.write(" Unable to create source bin \n")

    # Source element for reading from the uri.
    # We will use decodebin and let it figure out the container format of the
    # stream and the codec and plug the appropriate demux and decode plugins.
    uri_decode_bin=Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")
    if not uri_decode_bin:
        sys.stderr.write(" Unable to create uri decode bin \n")
    # We set the input uri to the source element
    uri_decode_bin.set_property("uri",uri)
    # Connect to the "pad-added" signal of the decodebin which generates a
    # callback once a new pad for raw data has beed created by the decodebin
    uri_decode_bin.connect("pad-added",cb_newpad,nbin)
    uri_decode_bin.connect("child-added",decodebin_child_added,nbin)

    # We need to create a ghost pad for the source bin which will act as a proxy
    # for the video decoder src pad. The ghost pad will not have a target right
    # now. Once the decode bin creates the video decoder and generates the
    # cb_newpad callback, we will set the ghost pad target to the video decoder
    # src pad.
    Gst.Bin.add(nbin,uri_decode_bin)
    bin_pad=nbin.add_pad(Gst.GhostPad.new_no_target("src",Gst.PadDirection.SRC))
    if not bin_pad:
        sys.stderr.write(" Failed to add ghost pad in source bin \n")
        return None
    return nbin

pipeline_elements = {
    'queue': 0,
    'video_conv_1':0,
    'nvosd': 0,
    'video_conv_2':0,
    'capsfilter':0,
    'encoder':0,
    'codeparser':0,
    'container':0,
    'sink': 0
}
pipeline_elements_array  = []

print('pipeline_elements_array:', pipeline_elements_array)

def main(args):
    # Check input arguments
    if len(args) < 2:
        sys.stderr.write("usage: %s <uri1> [uri2] ... [uriN]\n" % args[0])
        sys.exit(1)

    for i in range(0,len(args)-1):
        fps_streams["stream{0}".format(i)]=GETFPS(i)
    number_sources=len(args)-1

    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create gstreamer elements
    # Create Pipeline element that will form a connection of other elements
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()
    is_live = False

    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")

    print("Creating streamux \n ")

    # Create nvstreammux instance to form batches from one or more sources.
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux \n")

    pipeline.add(streammux)
    for i in range(number_sources):
        print("Creating source_bin ",i," \n ")
        uri_name=args[i+1]
        if uri_name.find("rtsp://") == 0 :
            is_live = True
        source_bin=create_source_bin(i, uri_name)
        if not source_bin:
            sys.stderr.write("Unable to create source bin \n")
        pipeline.add(source_bin)
        padname="sink_%u" %i
        sinkpad= streammux.get_request_pad(padname) 
        if not sinkpad:
            sys.stderr.write("Unable to create sink pad bin \n")
        srcpad=source_bin.get_static_pad("src")
        if not srcpad:
            sys.stderr.write("Unable to create src pad bin \n")
        srcpad.link(sinkpad)

    # Use nvinfer to run inferencing on decoder's output,
    # behaviour of inferencing is set through config file
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")

    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    if not tracker:
        sys.stderr.write(" Unable to create tracker \n")

    demux = Gst.ElementFactory.make("nvstreamdemux", "demuxer")
    if not demux:
        sys.stderr.write(" Unable to create demux \n")

    for j in range(number_sources):
        
        new_pipeline = pipeline_elements.copy()
        print("Creating queue %u \n"%j)
        new_pipeline['queue'] = Gst.ElementFactory.make("queue", "nvtee-que_%u"%j)
        if not new_pipeline['queue']:
            sys.stderr.write(" Unable to create queue1 \n")

        # Use convertor to convert from NV12 to RGBA as required by nvosd
        print("Creating video_convertor_1 %u \n"%j)
        new_pipeline['video_conv_1'] = Gst.ElementFactory.make("nvvideoconvert", "convertor%u"%j)
        if not new_pipeline['video_conv_1']:
            sys.stderr.write(" Unable to create nvvidconv %u%j \n")

        # Create OSD to draw on the converted RGBA buffer
        print("Creating nvosd %u \n"%j)
        new_pipeline['nvosd'] = Gst.ElementFactory.make("nvdsosd", "onscreendisplay%u"%j)

        if not new_pipeline['nvosd']:
            sys.stderr.write(" Unable to create nvosd1 \n")

        print("Creating vodeo_convertor_2 %u \n"%j)
        new_pipeline['video_conv_2'] = Gst.ElementFactory.make("nvvideoconvert", "convertor2%u"%j)
        if not new_pipeline['video_conv_2']:
            sys.stderr.write(" Unable to create nvvidconv %u%j \n")


        # Use convertor to convert from NV12 to RGBA as required by nvosd
        nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
        if not nvvidconv:
            sys.stderr.write(" Unable to create nvvidconv \n")

        # Create OSD to draw on the converted RGBA buffer
        nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")

        if not nvosd:
            sys.stderr.write(" Unable to create nvosd \n")

        nvvidconv2 = Gst.ElementFactory.make("nvvideoconvert", "convertor2")
        if not nvvidconv2:
            sys.stderr.write(" Unable to create nvvidconv2 \n")



        print("Creating Capsfilter %u \n"%j)
        new_pipeline['capsfilter'] = Gst.ElementFactory.make("capsfilter", "capsfilter%u"%j)
        if not new_pipeline['capsfilter']:
            sys.stderr.write(" Unable to create capsfilter1 \n")

        print("Creating Encoder %u \n"%j)
        new_pipeline['encoder'] = Gst.ElementFactory.make("avenc_mpeg4", "encoder%u"%j)
        if not new_pipeline['encoder']:
            sys.stderr.write(" Unable to create encoder1 \n")
        new_pipeline['encoder'].set_property("bitrate", 2000000)

        print("Creating Code Parser %u \n"%j)
        new_pipeline['codeparser'] = Gst.ElementFactory.make("mpeg4videoparse", "mpeg4-parser%u"%j)
        if not new_pipeline['codeparser']:
            sys.stderr.write(" Unable to create code parser1 \n")

        print("Creating Container %u \n"%j)
        new_pipeline['container'] = Gst.ElementFactory.make("qtmux", "qtmux%u"%j)
        if not new_pipeline['container']:
            sys.stderr.write(" Unable to create container1 \n")

        print("Creating FileSink %u \n"%j)
        new_pipeline['sink'] = Gst.ElementFactory.make("filesink", "filesink%u"%j)
        if not new_pipeline['sink']:
            sys.stderr.write(" Unable to create file sink1 \n")

        new_pipeline['sink'].set_property("location", "./out_%u.mp4"%j)
        new_pipeline['sink'].set_property("sync", 1)
        new_pipeline['sink'].set_property("async", 0)

        pipeline_elements_array.append(new_pipeline)    
    

    if is_live:
        print("Atleast one of the sources is live")
        streammux.set_property('live-source', 1)

    # print("Playing file %s " %args[1])
    # source.set_property('location', args[1])
    # streammux.set_property('width', 1920)
    # streammux.set_property('height', 1080)
    streammux.set_property('width', 1280)
    streammux.set_property('height', 720)    
    streammux.set_property('batch-size', number_sources)
    streammux.set_property('batched-push-timeout', 4000000)
    pgie.set_property('config-file-path', "config_infer_primary_yoloV5.txt")
    pgie_batch_size=pgie.get_property("batch-size")
    if(pgie_batch_size != number_sources):
        print("WARNING: Overriding infer-config batch-size",pgie_batch_size," with number of sources ", number_sources," \n")
        pgie.set_property("batch-size",number_sources)

    #Set properties of tracker
    config = configparser.ConfigParser()
    config.read('tracker_config.txt')    
    config.sections()
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
            tracker.set_property('enable_batch_process', tracker_enable_batch_process)
        if key == 'enable-past-frame' :
            tracker_enable_past_frame = config.getint('tracker', key)
            tracker.set_property('enable_past_frame', tracker_enable_past_frame)

    print("Adding elements to Pipeline \n")
    # pipeline.add(source)
    # pipeline.add(h264parser)
    # pipeline.add(decoder)
    #pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(demux)


    for j in range(number_sources):
        pipeline.add(pipeline_elements_array[j]['queue'])
        pipeline.add(pipeline_elements_array[j]['video_conv_1'])
        pipeline.add(pipeline_elements_array[j]['video_conv_2'])
        pipeline.add(pipeline_elements_array[j]['capsfilter'])
        pipeline.add(pipeline_elements_array[j]['encoder'])
        pipeline.add(pipeline_elements_array[j]['codeparser'])
        pipeline.add(pipeline_elements_array[j]['container'])
        pipeline.add(pipeline_elements_array[j]['nvosd'])
        pipeline.add(pipeline_elements_array[j]['sink'])
        
    

    # we link the elements together
    # file-source -> h264-parser -> nvh264-decoder ->
    # nvinfer -> nvvidconv -> nvosd -> video-renderer
    print("Linking elements in the Pipeline \n")
    # source.link(h264parser)
    # h264parser.link(decoder)

    # sinkpad = streammux.get_request_pad("sink_0")
    # if not sinkpad:
    #     sys.stderr.write(" Unable to get the sink pad of streammux \n")
    # srcpad = decoder.get_static_pad("src")
    # if not srcpad:
    #     sys.stderr.write(" Unable to get source pad of decoder \n")
    # srcpad.link(sinkpad)
    
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(demux)
    # pad_element = {
    #     'sink_pad':0,
    #     'src_pad':0
    # }
    sink_pad = []
    demux_src_pad = []
    for j in range(number_sources):
        # j = j+1
        print('file no: ',j+1,args[j+1] )
        pipeline_elements_array[j]['queue'].link(pipeline_elements_array[j]['video_conv_1'])
        pipeline_elements_array[j]['video_conv_1'].link(pipeline_elements_array[j]['video_conv_2'])
        pipeline_elements_array[j]['video_conv_2'].link(pipeline_elements_array[j]['capsfilter'])
        pipeline_elements_array[j]['capsfilter'].link(pipeline_elements_array[j]['encoder'])
        pipeline_elements_array[j]['encoder'].link(pipeline_elements_array[j]['codeparser'])
        pipeline_elements_array[j]['codeparser'].link(pipeline_elements_array[j]['container'])
        pipeline_elements_array[j]['container'].link(pipeline_elements_array[j]['nvosd'])
        pipeline_elements_array[j]['nvosd'].link(pipeline_elements_array[j]['sink'])
    
        try:
            sink_pad[j-1] = pipeline_elements_array[j]['queue'].get_static_pad("sink")
            demux_src_pad[j] = demux.get_request_pad("src_%u" % j)
            if not demux_src_pad[j]:
                sys.stderr.write(" Unable to get the sink pad 1 of streammux \n")
            demux_src_pad[j].link(sink_pad[j])

        except:
            pass


    # queue2.link(nvvidconv2_a)
    # nvvidconv2_a.link(nvosd2)
    # nvosd2.link(nvvidconv2_b)
    # nvvidconv2_b.link(capsfilter2)
    # capsfilter2.link(encoder2)
    # encoder2.link(codeparser2)
    # codeparser2.link(container2)
    # container2.link(sink2)

    # sink_pad2 = queue2.get_static_pad("sink")

    # demux_src_pad2 = demux.get_request_pad("src_1")
    # if not demux_src_pad2:
    #     sys.stderr.write(" Unable to get the sink pad 1 of streammux \n")
    # demux_src_pad2.link(sink_pad2)
    

    # sink_pad = queue1.get_static_pad("sink")
    # tee_out1_pad = tee.get_request_pad('src_%u')
    # tee_out2_pad = tee.get_request_pad("src_%u")
    # if not tee_out1_pad or not tee_out2_pad:
    #     sys.stderr.write("Unable to get request pads\n")
    # tee_out1_pad.link(sink_pad)
    # sink_pad = queue2.get_static_pad("sink")
    # tee_out2_pad.link(sink_pad)

    # create an event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)

    # Lets add probe to get informed of the meta data generated, we add probe to
    # the sink pad of the osd element, since by that time, the buffer would have
    # had got all the metadata.
    # osdsinkpad1 = nvosd1.get_static_pad("sink")
    # if not osdsinkpad1:
    #     sys.stderr.write(" Unable to get sink pad of nvosd \n")

    # osdsinkpad1.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

    # osdsinkpad2 = nvosd2.get_static_pad("sink")
    # if not osdsinkpad2:
    #     sys.stderr.write(" Unable to get sink pad of nvosd \n")

    # osdsinkpad2.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

    # start play back and listen to events
    print("Starting pipeline \n")
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except:
        pass
    # cleanup
    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))