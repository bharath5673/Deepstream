#!/usr/bin/env python3

################################################################################
# SPDX-FileCopyrightText: Copyright (c) 2019-2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
sys.path.append('/root/deepstream_python_apps/apps/')
import os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst
from common.platform_info import PlatformInfo
from common.bus_call import bus_call
import pyds
import configparser
import numpy as np
import datetime


# Load COCO class names (optional)
COCO_CLASSES = []
with open("/root/DeepStream-Yolo/labels.txt", "r") as f:  # File should contain one class per line
    COCO_CLASSES = [line.strip() for line in f.readlines()]
# Constants
MUXER_BATCH_TIMEOUT_USEC = 33000


def osd_sink_pad_buffer_probe(pad, info, u_data):
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    if not batch_meta:
        return Gst.PadProbeReturn.OK

    l_frame = batch_meta.frame_meta_list
    while l_frame:
        frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        frame_number = frame_meta.frame_num

        l_obj = frame_meta.obj_meta_list
        while l_obj:
            obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)

            class_id = obj_meta.class_id
            tracker_id = obj_meta.object_id
            rect = obj_meta.rect_params

            # bottom-center of bbox
            x = int(rect.left + rect.width / 2)
            y = int(rect.top + rect.height)

            print(f"Frame {frame_number} | Class {class_id} | ObjID {tracker_id} | BBox=({x},{y})")
            sys.stdout.flush()
            
            l_obj = l_obj.next
        l_frame = l_frame.next

    return Gst.PadProbeReturn.OK

def main(args):
    if len(args) < 2:
        sys.stderr.write("Usage: %s <input_file.h264> [--display]\n" % args[0])
        return 1

    input_file = args[1]
    enable_display = ("--display" in args)

    Gst.init(None)
    pipeline = Gst.Pipeline.new("deepstream-pipeline")
    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")
        return 1

    # Use uridecodebin for universal input handling
    source = Gst.ElementFactory.make("uridecodebin", "uri-source")
    if not source:
        sys.stderr.write(" Unable to create uridecodebin source \n")
        return 1

    streammux = Gst.ElementFactory.make("nvstreammux", "stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create streammux \n")
        return 1

    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")
        return 1

    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    if not tracker:
        sys.stderr.write(" Unable to create tracker \n")
        return 1

    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")
        return 1

    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    if not nvosd:
        sys.stderr.write(" Unable to create nvosd \n")
        return 1

    nvvidconv2 = Gst.ElementFactory.make("nvvideoconvert", "convertor2")
    if not nvvidconv2:
        sys.stderr.write(" Unable to create nvvidconv2 \n")
        return 1

    # Use NVIDIA hardware encoder with fallback
    encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
    if not encoder:
        encoder = Gst.ElementFactory.make("x264enc", "encoder")
        if not encoder:
            sys.stderr.write(" Unable to create encoder \n")
            return 1

    # Add h264parse after encoder for proper MP4 muxing
    h264parse2 = Gst.ElementFactory.make("h264parse", "h264-parser2")
    if not h264parse2:
        sys.stderr.write(" Unable to create h264parse2 \n")
        return 1

    muxer = Gst.ElementFactory.make("qtmux", "mp4-muxer")
    if not muxer:
        sys.stderr.write(" Unable to create muxer \n")
        return 1

    sink = Gst.ElementFactory.make("filesink", "file-sink")
    if not sink:
        sys.stderr.write(" Unable to create sink \n")
        return 1

    tee = Gst.ElementFactory.make("tee", "tee")
    if not tee:
        sys.stderr.write(" Unable to create tee \n")
        return 1

    queue1 = Gst.ElementFactory.make("queue", "queue1")
    if not queue1:
        sys.stderr.write(" Unable to create queue1 \n")
        return 1

    # Display branch (only if enabled)
    display_sink = None
    queue2 = None
    if enable_display:
        queue2 = Gst.ElementFactory.make("queue", "queue2")
        if not queue2:
            sys.stderr.write(" Unable to create queue2 \n")
            return 1
        display_sink = Gst.ElementFactory.make("nveglglessink", "display-sink")
        if not display_sink:
            sys.stderr.write(" Unable to create display sink \n")
            return 1

    
    # Convert file path to URI format
    if input_file.startswith("file://"):
        uri = input_file
    else:
        uri = "file://" + os.path.abspath(input_file)
    
    source.set_property("uri", uri)
    source.set_property("buffer-duration", 0)
    source.set_property("buffer-size", 0)

    streammux.set_property("width", 768)
    streammux.set_property("height", 432)
    streammux.set_property("batch-size", 1)
    streammux.set_property("batched-push-timeout", 4000000)  # MUXER_BATCH_TIMEOUT_USEC
    streammux.set_property("live-source", 0)

    pgie.set_property("config-file-path", "/root/DeepStream-Configs/config_infer_primary_yoloV8.txt")


    encoder.set_property("bitrate", 2000000)
    # Create output directory and better file naming
    os.makedirs("./outputs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sink.set_property("location", f"/root/outputs/deepstream_test_yolo_save_vid_out_{timestamp}.mp4")
    sink.set_property("sync", False)
    sink.set_property("async", False)

    if enable_display and display_sink:
        display_sink.set_property("sync", False)


    elems = [source, streammux, pgie, nvvidconv, nvosd, 
             tee, queue1, nvvidconv2, encoder, h264parse2, muxer, sink]
    
    if enable_display and display_sink:
        elems.extend([queue2, display_sink])

    for elem in elems:
        if elem:
            pipeline.add(elem)


    
    # Link all elements except source (uridecodebin)
    streammux.link(pgie)
    pgie.link(nvvidconv)
    nvvidconv.link(nvosd)
    nvosd.link(tee)

    # Recording branch
    tee.link(queue1)
    queue1.link(nvvidconv2)
    nvvidconv2.link(encoder)
    encoder.link(h264parse2)
    h264parse2.link(muxer)
    muxer.link(sink)

    # Display branch
    if enable_display and display_sink:
        tee.link(queue2)
        queue2.link(display_sink)


    def on_pad_added(element, pad, target_element):
        # Only connect video pads
        if pad.query_caps(None).to_string().startswith('video/'):
            sinkpad = target_element.get_static_pad("sink_0")
            if not sinkpad:
                sinkpad = target_element.get_request_pad("sink_0")
            pad.link(sinkpad)

    source.connect("pad-added", on_pad_added, streammux)


    osdsinkpad = nvosd.get_static_pad("sink")
    if osdsinkpad:
        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)


    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    print("Starting pipeline... Display:", enable_display)
    print(f"Input: {input_file}")
    print(f"Output: ./outputs/out_{timestamp}.mp4")
    sys.stdout.flush()
    
    # Set pipeline to PLAYING state
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        sys.stderr.write("Unable to set pipeline to PLAYING state\n")
        return 1
    
    try:
        loop.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        pipeline.set_state(Gst.State.NULL)
        print("Pipeline stopped")
    
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))