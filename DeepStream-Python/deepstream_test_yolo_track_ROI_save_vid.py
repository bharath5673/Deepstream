#!/usr/bin/env python3

################################################################################
# SPDX-FileCopyrightText: Copyright (c) 2019-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
from collections import deque


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

# Load COCO class names (optional)
COCO_CLASSES = []
with open("/root/DeepStream-Yolo/labels.txt", "r") as f:  # File should contain one class per line
    COCO_CLASSES = [line.strip() for line in f.readlines()]
# Constants
MUXER_BATCH_TIMEOUT_USEC = 33000

# ============================================================
# GLOBALS (single stream)
# ============================================================
rois = [
    [(81, 423), (23, 344), (40, 288), (23, 251), (35, 215), (219, 213), (81, 423)],
    [(610, 423), (560, 213), (730, 215), (730, 218), (683, 291), (703, 335), (633, 420), (610, 423)]
]

object_traj = {}               # tid -> list of centroid points
MAX_TRAJ = 30                  # how long trajectory to keep
roi_counts = [set() for _ in rois]    # cumulative counts

# Trajectory settings (tweak these)
MAX_TRAJ = 20             # max points stored per object
TRAJ_TTL_FRAMES = 30      # remove trajectory if not seen for this many frames
TRAJ_SEG_FADE = True      # fade older segments if True
last_seen = {}     # tid -> last frame index seen
# frame counter used by TTL logic
_global_frame_idx = 0


# ============================================================
# Helper: point in polygon (ray casting)
# ============================================================
def point_in_poly(x, y, poly):
    inside = False
    p1x, p1y = poly[0]
    for i in range(1, len(poly) + 1):
        p2x, p2y = poly[i % len(poly)]
        if (y > min(p1y, p2y)) and (y <= max(p1y, p2y)) and (x <= max(p1x, p2x)):
            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y + 1e-6) + p1x
            if x <= xinters:
                inside = not inside
        p1x, p1y = p2x, p2y
    return inside

# ============================================================
# Helper: point in polygon (ray casting)
# ============================================================
# Drop-in replacement for your osd_sink_pad_buffer_probe
def osd_sink_pad_buffer_probe(pad, info, u_data):
    global _global_frame_idx, object_traj, last_seen, roi_counts

    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK

    # ---- Stream name (same as before) ----
    stream_name = getattr(u_data, "stream_name", None) if u_data is not None else None
    if stream_name is None:
        try:
            stream_name = u_data.get("stream_name", "stream") if isinstance(u_data, dict) else "stream"
        except Exception:
            stream_name = "stream"

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list

    # increment a global frame counter once per call
    _global_frame_idx += 1
    current_frame_idx = _global_frame_idx

    while l_frame:
        frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)

        # per-frame hit list (not cumulative)
        frame_hits = [set() for _ in rois]

        # ----------------------------------------------------------------
        # 1) Walk objects, update frame_hits, roi_counts, object_traj, last_seen
        # ----------------------------------------------------------------
        l_obj = frame_meta.obj_meta_list
        while l_obj:
            obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)

            tid = int(getattr(obj_meta, "object_id", -1))
            if tid < 0:
                l_obj = l_obj.next
                continue

            # bottom-center of bbox (centroid)
            rect = obj_meta.rect_params
            cx = int(rect.left + rect.width / 2)
            cy = int(rect.top + rect.height)

            # ROI Hit check
            for idx, poly in enumerate(rois):
                try:
                    if point_in_poly(cx, cy, poly):
                        frame_hits[idx].add(tid)
                        roi_counts[idx].add(tid)    # cumulative unique IDs
                except Exception:
                    pass

            # maintain deque for trajectory
            dq = object_traj.get(tid)
            if dq is None:
                dq = deque(maxlen=MAX_TRAJ)
                object_traj[tid] = dq
            dq.append((cx, cy))

            # update last seen
            last_seen[tid] = current_frame_idx

            l_obj = l_obj.next

        # prune stale trajectories (not seen for TRAJ_TTL_FRAMES)
        stale = [tid_k for tid_k, last in list(last_seen.items())
                 if current_frame_idx - last > TRAJ_TTL_FRAMES]
        for tid_k in stale:
            last_seen.pop(tid_k, None)
            object_traj.pop(tid_k, None)

        # ----------------------------------------------------------------
        # 2) Prepare display_meta and draw ROIs + labels
        # ----------------------------------------------------------------
        try:
            display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)

            # reset counters for this display_meta
            display_meta.num_lines = 0
            display_meta.num_labels = 0

            # draw polygons and label each ROI at its top-left
            for ridx, poly in enumerate(rois):
                # polygon edges
                for j in range(len(poly)):
                    if display_meta.num_lines >= len(display_meta.line_params):
                        break
                    x1, y1 = poly[j]
                    x2, y2 = poly[(j + 1) % len(poly)]
                    ln = display_meta.line_params[display_meta.num_lines]
                    ln.x1 = int(x1); ln.y1 = int(y1)
                    ln.x2 = int(x2); ln.y2 = int(y2)
                    ln.line_width = 3
                    ln.line_color.set(0.0, 0.0, 1.0, 1.0)
                    display_meta.num_lines += 1

                # label top-left of ROI
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                lx, ly = min(xs), min(ys)
                if display_meta.num_labels < len(display_meta.text_params):
                    txt = display_meta.text_params[display_meta.num_labels]
                    txt.display_text = f"ROI {ridx}: {len(roi_counts[ridx])}"
                    txt.x_offset = int(lx + 5)
                    txt.y_offset = int(ly + 15)
                    txt.font_params.font_name = "Serif"
                    txt.font_params.font_size = 14
                    txt.font_params.font_color.set(1.0, 1.0, 0.0, 1.0)
                    txt.set_bg_clr = 1
                    txt.text_bg_clr.set(0.0, 0.0, 0.0, 0.5)
                    display_meta.num_labels += 1

            # ----------------------------------------------------------------
            # 3) DRAW TRAJECTORIES FOR ALL OBJECTS (not nested in ROI loop)
            #    — allocate remaining line slots across object segments until full
            # ----------------------------------------------------------------
            total_line_capacity = len(display_meta.line_params)
            # available lines left for trajectories
            avail = total_line_capacity - display_meta.num_lines
            if avail > 0:
                # We'll iterate objects and draw segments until 'avail' exhausted.
                # This prevents one huge trajectory from consuming all slots and starving others.
                for tid, dq in object_traj.items():
                    if avail <= 0:
                        break
                    pts = list(dq)
                    if len(pts) < 2:
                        continue
                    n_segments = len(pts) - 1

                    # draw each segment, decrement avail
                    for sidx in range(n_segments):
                        if avail <= 0:
                            break
                        # safety check again (keeps display_meta consistent)
                        if display_meta.num_lines >= total_line_capacity:
                            avail = 0
                            break

                        x1, y1 = pts[sidx]
                        x2, y2 = pts[sidx + 1]
                        seg = display_meta.line_params[display_meta.num_lines]
                        seg.x1 = int(x1); seg.y1 = int(y1)
                        seg.x2 = int(x2); seg.y2 = int(y2)
                        seg.line_width = 2

                        if TRAJ_SEG_FADE:
                            age_ratio = (sidx + 1) / max(1, n_segments)
                            alpha = 0.15 + 0.85 * age_ratio
                            seg.line_color.set(0.0, 1.0, 0.0, float(alpha))
                        else:
                            seg.line_color.set(0.0, 1.0, 0.0, 1.0)

                        display_meta.num_lines += 1
                        avail -= 1

            # attach display_meta
            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        except Exception as e:
            # print helpful debug
            print("Adding display meta failed:", e)

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
    sink.set_property("location", f"/root/outputs/deepstream_test_yolo_track_ROI_save_vid_out_{timestamp}.mp4")
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