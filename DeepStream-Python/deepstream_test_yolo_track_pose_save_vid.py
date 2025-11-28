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
import datetime
import numpy as np
import csv, os, time, pyds
from threading import Lock
from ctypes import sizeof, c_float

print("InferApiApp")
print("Starting per-source independent DeepStream pipelines...")

# -------------------------------
# Initial configs
# -------------------------------
MUXER_OUTPUT_WIDTH = 1920 // 2
MUXER_OUTPUT_HEIGHT = 1080 // 2
MUXER_BATCH_TIMEOUT_USEC = 33000
TILED_OUTPUT_WIDTH = 768
TILED_OUTPUT_HEIGHT = 432
STREAMMUX_WIDTH = MUXER_OUTPUT_WIDTH 
STREAMMUX_HEIGHT = MUXER_OUTPUT_HEIGHT
MAX_ELEMENTS_IN_DISPLAY_META = 16
STREAMMUX_BATCH_SIZE = 1
PERF_MEASUREMENT_INTERVAL_SEC = 5


# ======================================================
# pose detection probe (PGIE)
# ======================================================
skeleton = [
    [16, 14], [14, 12], [17, 15], [15, 13], [12, 13],
    [6, 12], [7, 13], [6, 7], [6, 8], [7, 9],
    [8, 10], [9, 11], [2, 3], [1, 2], [1, 3],
    [2, 4], [3, 5], [4, 6], [5, 7]
]

# Define left/right body parts (approx based on COCO format)
LEFT_PARTS = {5, 7, 9, 11, 13, 15, 17}
RIGHT_PARTS = {6, 8, 10, 12, 14, 16, 18}
EYE_POINTS = {2, 3}  # left_eye, right_eye

def parse_pose_from_meta(batch_meta, frame_meta, obj_meta):
    display_meta = None
    data = obj_meta.mask_params.get_mask_array()
    num_joints = int(obj_meta.mask_params.size / (sizeof(c_float) * 3))

    gain = min(obj_meta.mask_params.width / STREAMMUX_WIDTH, obj_meta.mask_params.height / STREAMMUX_HEIGHT)
    pad_x = (obj_meta.mask_params.width - STREAMMUX_WIDTH * gain) * 0.5
    pad_y = (obj_meta.mask_params.height - STREAMMUX_HEIGHT * gain) * 0.5

    # --- Draw keypoints ---
    for i in range(num_joints):
        xc = (data[i * 3 + 0] - pad_x) / gain
        yc = (data[i * 3 + 1] - pad_y) / gain
        conf = data[i * 3 + 2]

        if conf < 0.5:
            continue

        if display_meta is None or display_meta.num_circles == MAX_ELEMENTS_IN_DISPLAY_META:
            display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        circle_params = display_meta.circle_params[display_meta.num_circles]
        circle_params.xc = int(min(STREAMMUX_WIDTH - 1, max(0, xc)))
        circle_params.yc = int(min(STREAMMUX_HEIGHT - 1, max(0, yc)))


        circle_params.circle_color.alpha = 1.0
        circle_params.has_bg_color = 1
        circle_params.bg_color.red = 0.0
        circle_params.bg_color.green = 0.0
        circle_params.bg_color.blue = 0.0
        circle_params.bg_color.alpha = 1.0

        display_meta.num_circles += 1

    # --- Draw skeleton lines ---
    for (p1, p2) in skeleton:
        x1 = (data[(p1 - 1) * 3 + 0] - pad_x) / gain
        y1 = (data[(p1 - 1) * 3 + 1] - pad_y) / gain
        c1 = data[(p1 - 1) * 3 + 2]
        x2 = (data[(p2 - 1) * 3 + 0] - pad_x) / gain
        y2 = (data[(p2 - 1) * 3 + 1] - pad_y) / gain
        c2 = data[(p2 - 1) * 3 + 2]

        if c1 < 0.5 or c2 < 0.5:
            continue

        if display_meta is None or display_meta.num_lines == MAX_ELEMENTS_IN_DISPLAY_META:
            display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        line_params = display_meta.line_params[display_meta.num_lines]
        line_params.x1 = int(min(STREAMMUX_WIDTH - 1, max(0, x1)))
        line_params.y1 = int(min(STREAMMUX_HEIGHT - 1, max(0, y1)))
        line_params.x2 = int(min(STREAMMUX_WIDTH - 1, max(0, x2)))
        line_params.y2 = int(min(STREAMMUX_HEIGHT - 1, max(0, y2)))
        line_params.line_width = 3

        # Color code based on which side of body
        if (p1 in LEFT_PARTS or p2 in LEFT_PARTS):
            line_params.line_color.red = 0.0
            line_params.line_color.green = 0.5
            line_params.line_color.blue = 1.0
        elif (p1 in RIGHT_PARTS or p2 in RIGHT_PARTS):
            line_params.line_color.red = 1.0
            line_params.line_color.green = 0.5
            line_params.line_color.blue = 0.0

        line_params.line_color.alpha = 1.0
        display_meta.num_lines += 1



def osd_sink_pad_buffer_probe(pad, info, u_data):
    meta = u_data or {}
    src_id = meta.get("src_id", 0)
    stream_name = meta.get("name", f"src_{src_id}")

    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    if not batch_meta:
        return Gst.PadProbeReturn.OK

    l_frame = batch_meta.frame_meta_list
    while l_frame:
        frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        frame_number = int(frame_meta.frame_num)
        l_obj = frame_meta.obj_meta_list

        frame_detections = {
            "frame_id": frame_number,
            "detections": []
        }

        while l_obj:
            obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)

            # --- Pose drawing ---
            parse_pose_from_meta(batch_meta, frame_meta, obj_meta)

            # --- Object info ---
            class_id = obj_meta.class_id
            tracker_id = int(obj_meta.object_id) if obj_meta.object_id != 0xFFFFFFFF else -1
            confidence = round(float(obj_meta.confidence) * 100, 1)
            obj_label = obj_meta.obj_label or f"Class_{class_id}"

            rect = obj_meta.rect_params
            xmin, ymin = int(rect.left), int(rect.top)
            xmax, ymax = int(rect.left + rect.width), int(rect.top + rect.height)

            print(f"[DS] Src={stream_name} | Frame={frame_number} | ID={tracker_id} | "
                  f"{obj_label} ({confidence}%) | Box=({xmin},{ymin},{xmax},{ymax})")

            # --- Save structured detections ---
            frame_detections["detections"].append({
                "id": tracker_id,
                "label": obj_label,
                "cls_id": class_id,
                "score": confidence,
                "box": [xmin, ymin, xmax, ymax],
                "model": "primary" if obj_meta.unique_component_id == 1 else "secondary"
            })

            # --- Overlay box & label with ID ---
            obj_meta.rect_params.border_width = 3
            obj_meta.rect_params.border_color.set(1.0, 0.0, 0.0, 1.0)  # red border
            obj_meta.text_params.display_text = f"ID:{tracker_id} | {obj_label}:{confidence:.1f}%"
            obj_meta.text_params.font_params.font_name = "Serif"
            obj_meta.text_params.font_params.font_size = 8
            obj_meta.text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
            obj_meta.text_params.set_bg_clr = 1
            obj_meta.text_params.text_bg_clr.set(0.0, 0.0, 0.0, 0.9)

            l_obj = l_obj.next

        # --- Overlay frame summary text ---
        display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 1
        text_params = display_meta.text_params[0]
        text_params.display_text = f"Frame {frame_number} | Objects: {len(frame_detections['detections'])}"
        text_params.x_offset = 10
        text_params.y_offset = 15
        text_params.font_params.font_name = "Serif"
        text_params.font_params.font_size = 8
        text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
        text_params.set_bg_clr = 1
        text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        # Debug output (optional)
        # print(f"✅ Frame {frame_number} — {len(frame_detections['detections'])} detections")

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

    streammux.set_property("width", MUXER_OUTPUT_WIDTH)
    streammux.set_property("height", MUXER_OUTPUT_HEIGHT)
    streammux.set_property("batch-size", 1)
    streammux.set_property("batched-push-timeout", 4000000)  # MUXER_BATCH_TIMEOUT_USEC
    streammux.set_property("live-source", 0)

    pgie.set_property("config-file-path", "/root/DeepStream-Configs/config_infer_primary_yoloV8_pose.txt")
    # pgie.set_property("config-file-path", "/root/DeepStream-Configs/config_infer_primary_yolo11_pose.txt")

    # Tracker config handling
    try:
        config = configparser.ConfigParser()
        config.read('/root/DeepStream-Configs/dstest2_tracker_config.txt')
        if 'tracker' in config:
            for key in config['tracker']:
                val = config.get('tracker', key)
                tracker.set_property(key.replace('-', '_'), int(val) if val.isdigit() else val)
    except Exception as e:
        print(f"Warning: Could not load tracker config: {e}")

    encoder.set_property("bitrate", 2000000)

    # Create output directory and better file naming
    os.makedirs("./outputs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sink.set_property("location", f"/root/outputs/deepstream_test_yolo_track_pose_save_vid_out_{timestamp}.mp4")
    sink.set_property("sync", False)
    sink.set_property("async", False)

    if enable_display and display_sink:
        display_sink.set_property("sync", False)


    elems = [source, streammux, pgie, tracker, nvvidconv, nvosd, 
             tee, queue1, nvvidconv2, encoder, h264parse2, muxer, sink]
    
    if enable_display and display_sink:
        elems.extend([queue2, display_sink])

    for elem in elems:
        if elem:
            pipeline.add(elem)


    
    # Link all elements except source (uridecodebin)
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(nvvidconv)
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