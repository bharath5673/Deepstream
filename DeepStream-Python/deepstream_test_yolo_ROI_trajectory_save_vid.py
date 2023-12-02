#!/usr/bin/env python3

################################################################################
# Copyright (c) 2020, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
################################################################################

import sys
sys.path.append('../')
import configparser
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
import pyds
from scipy.spatial import distance


# Ray tracing
def ray_tracing_method(x,y,poly):
    n = len(poly)
    inside = False
    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x,p1y = p2x,p2y
    return inside
# count objects inside roi

def count_objects(center_x, bottom, tracker, tracker_ids, poly, center_y, firstDetectedinROI) :
    #point = (center_x, center_y)               # Centroid
    point = (center_x, bottom)                  # Bottom
    is_object_counted = False
    if ray_tracing_method(point[0], point[1], poly):
        firstDetectedinROI.append(tracker) 
        is_object_counted = True
        tracker_ids[tracker] = 1
    return is_object_counted

def getEuclideanDistance(point1, point2):
    return distance.euclidean(point1, point2)


PGIE_CLASS_IDS = {
    'PGIE_CLASS_ID_VEHICLE' : 0, 
    'PGIE_CLASS_ID_PERSON' : 0,
    'PGIE_CLASS_ID_BICYCLE' : 0,
    'PGIE_CLASS_ID_ROADSIGN' : 0  
}

#Intiallizing object counter with 0.
obj_counter = { id:0 for id in PGIE_CLASS_IDS.values() }
obj_ids = { ids:[] for ids in PGIE_CLASS_IDS.values() }
obj_ids_array = []
past_tracking_meta=[0]
tracker_ids = {}
firstDetectedinROI = []
trajectoryPlottingData = {}



def osd_sink_pad_buffer_probe(pad,info,u_data):
    frame_number=0
    #Intiallizing object counter with 0.
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
            # The casting is done by pyds.glist_get_nvds_frame_meta()
            # The casting also keeps ownership of the underlying memory
            # in the C code, so the Python garbage collector will leave
            # it alone.
            #frame_meta = pyds.glist_get_nvds_frame_meta(l_frame.data)
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        frame_number=frame_meta.frame_num
        num_rects = frame_meta.num_obj_meta
        l_obj=frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                #obj_meta=pyds.glist_get_nvds_object_meta(l_obj.data)
                obj_meta=pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            try:
                # obj_counter[obj_meta.class_id] += 1

                class_id = obj_meta.class_id
                tracker = obj_meta.object_id
                top = obj_meta.rect_params.top
                left = obj_meta.rect_params.left
                height = obj_meta.rect_params.height
                width = obj_meta.rect_params.width
                #score = obj_meta.confidence

                bottom = top + height
                right = left + width
                center_y = (top + bottom) / 2
                center_x = (left + right) / 2


                ###trajectory
                if tracker not in trajectoryPlottingData.keys() :
                    trajectoryPlottingData[tracker] = [(round(center_x), round(center_y))]
                else:
                    trajectoryPlottingData[tracker].append((round(center_x), round(center_y)))
                # print(trajectoryPlottingData)

                ###objects inside ROI
                is_object_counted = count_objects(center_x, bottom, tracker, tracker_ids, poly, center_y, firstDetectedinROI)
                if is_object_counted :
                    if class_id in obj_counter.keys():                        
                        if tracker not in obj_ids[class_id]:
                            obj_counter[obj_meta.class_id] += 1
                            obj_ids[class_id].append(tracker)

            except:
                pass


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
        # py_nvosd_text_params.display_text = "Frame Number={} Number of Objects={} Vehicle_count={} Person_count={}".format(frame_number, num_rects, obj_counter[PGIE_CLASS_ID_VEHICLE], obj_counter[PGIE_CLASS_ID_PERSON])
        py_nvosd_text_params.display_text = f"Frame Number={frame_number} Number of Objects={num_rects} Person_count={obj_counter[PGIE_CLASS_IDS['PGIE_CLASS_ID_PERSON']]} " 

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


        # Creat ROI lines
        # ROI line first
        py_nvosd_line_params_1 = display_meta.line_params[0]
        py_nvosd_line_params_1.x1 = ROI_line['top_left'][0]
        py_nvosd_line_params_1.y1 = ROI_line['top_left'][1]
        py_nvosd_line_params_1.x2 = ROI_line['top_right'][0]
        py_nvosd_line_params_1.y2 = ROI_line['top_right'][1]
        py_nvosd_line_params_1.line_width = 4
        py_nvosd_line_params_1.line_color.red = 1.0
        py_nvosd_line_params_1.line_color.green = 1.0
        py_nvosd_line_params_1.line_color.blue = 1.0
        py_nvosd_line_params_1.line_color.alpha = 1.0
        display_meta.num_lines += 1
        # ROI line second
        py_nvosd_line_params_2 = display_meta.line_params[1]
        py_nvosd_line_params_2.x1 = ROI_line['top_right'][0]
        py_nvosd_line_params_2.y1 = ROI_line['top_right'][1]
        py_nvosd_line_params_2.x2 = ROI_line['bottom_right'][0]
        py_nvosd_line_params_2.y2 = ROI_line['bottom_right'][1]
        py_nvosd_line_params_2.line_width = 4
        py_nvosd_line_params_2.line_color.red = 1.0
        py_nvosd_line_params_2.line_color.green = 1.0
        py_nvosd_line_params_2.line_color.blue = 1.0
        py_nvosd_line_params_2.line_color.alpha = 1.0
        display_meta.num_lines += 1
        # ROI line third
        py_nvosd_line_params_3 = display_meta.line_params[2]
        py_nvosd_line_params_3.x1 = ROI_line['bottom_right'][0]
        py_nvosd_line_params_3.y1 = ROI_line['bottom_right'][1]
        py_nvosd_line_params_3.x2 = ROI_line['bottom_left'][0]
        py_nvosd_line_params_3.y2 = ROI_line['bottom_left'][1]
        py_nvosd_line_params_3.line_width = 4
        py_nvosd_line_params_3.line_color.red = 1.0
        py_nvosd_line_params_3.line_color.green = 1.0
        py_nvosd_line_params_3.line_color.blue = 1.0
        py_nvosd_line_params_3.line_color.alpha = 1.0
        display_meta.num_lines += 1
        # ROI line fourth
        py_nvosd_line_params_4 = display_meta.line_params[3]
        py_nvosd_line_params_4.x1 = ROI_line['bottom_left'][0]
        py_nvosd_line_params_4.y1 = ROI_line['bottom_left'][1]
        py_nvosd_line_params_4.x2 = ROI_line['top_left'][0]
        py_nvosd_line_params_4.y2 = ROI_line['top_left'][1]
        py_nvosd_line_params_4.line_width = 4
        py_nvosd_line_params_4.line_color.red = 1.0
        py_nvosd_line_params_4.line_color.green = 1.0
        py_nvosd_line_params_4.line_color.blue = 1.0
        py_nvosd_line_params_4.line_color.alpha = 1.0
        display_meta.num_lines += 1


        # Using pyds.get_string() to get display_text as string
        print(pyds.get_string(py_nvosd_text_params.display_text))
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)



        params_count = 5
        nvosd_dict = {}
        for id in trajectoryPlottingData.keys():
            center_list = trajectoryPlottingData[id]

            trajectory_length = 0
            for i in range(len(center_list) - 1):                
                if params_count % 15 == 0:
                    params_count = 0
                    display_meta=pyds.nvds_acquire_display_meta_from_pool(batch_meta)
                    display_meta.num_labels += 1

                nvosd_dict[str(frame_number) + str(id) + str(i)] = display_meta.line_params[params_count]
                params_count +=1
                
                (nvosd_dict[str(frame_number) + str(id) + str(i)].x1, nvosd_dict[str(frame_number) + str(id) + str(i)].y1) = center_list[i]
                (nvosd_dict[str(frame_number) + str(id) + str(i)].x2, nvosd_dict[str(frame_number) + str(id) + str(i)].y2) = center_list[i+1]
                nvosd_dict[str(frame_number) + str(id) + str(i)].line_width = 2
                nvosd_dict[str(frame_number) + str(id) + str(i)].line_color.red = 0.0
                nvosd_dict[str(frame_number) + str(id) + str(i)].line_color.green = 1.0
                nvosd_dict[str(frame_number) + str(id) + str(i)].line_color.blue = 0.0
                nvosd_dict[str(frame_number) + str(id) + str(i)].line_color.alpha = 1.0
                display_meta.num_lines += 1
                trajectory_length += getEuclideanDistance(center_list[i], center_list[i+1])


        try:
            l_frame=l_frame.next
        except StopIteration:
            break
            
    return Gst.PadProbeReturn.OK    


def main(args):

    global poly, ROI_line, roi_factor,obj_counter_array, obj_ids_array,obj_counter

    # Check input arguments
    if len(args) != 2:
        sys.stderr.write("usage: %s <media file or uri>\n" % args[0])
        sys.exit(1)

    # Standard GStreamer initialization
    GObject.threads_init()
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

    capsfilter = Gst.ElementFactory.make("capsfilter", "capsfilter")
    if not capsfilter:
        sys.stderr.write(" Unable to create capsfilter \n")

    caps = Gst.Caps.from_string("video/x-raw, format=I420")
    capsfilter.set_property("caps", caps)

    encoder = Gst.ElementFactory.make("avenc_mpeg4", "encoder")
    if not encoder:
        sys.stderr.write(" Unable to create encoder \n")
    encoder.set_property("bitrate", 2000000)

    print("Creating Code Parser \n")
    codeparser = Gst.ElementFactory.make("mpeg4videoparse", "mpeg4-parser")
    if not codeparser:
        sys.stderr.write(" Unable to create code parser \n")

    print("Creating Container \n")
    container = Gst.ElementFactory.make("qtmux", "qtmux")
    if not container:
        sys.stderr.write(" Unable to create code parser \n")

    print("Creating Sink \n")
    sink = Gst.ElementFactory.make("filesink", "filesink")
    if not sink:
        sys.stderr.write(" Unable to create file sink \n")

    sink.set_property("location", "./out.mp4")
    sink.set_property("sync", 1)
    sink.set_property("async", 0)

    print("Playing file %s " %args[1])
    source.set_property('location', args[1])
    streammux.set_property('width', 1280)
    streammux.set_property('height', 720)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)

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
        # tracker.set_property('tracker-width', 640)
        # tracker.set_property('tracker-height', 384)

    print("Adding elements to Pipeline \n")
    pipeline.add(source)
    pipeline.add(h264parser)
    pipeline.add(decoder)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(nvvidconv)
    pipeline.add(nvvidconv2)
    pipeline.add(encoder)
    pipeline.add(capsfilter)
    pipeline.add(codeparser)
    pipeline.add(container)
    pipeline.add(nvosd)
    pipeline.add(sink)

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
    nvosd.link(nvvidconv2)
    nvvidconv2.link(capsfilter)
    capsfilter.link(encoder)
    encoder.link(codeparser)

    sinkpad1 = container.get_request_pad("video_0")
    if not sinkpad1:
        sys.stderr.write(" Unable to get the sink pad of qtmux \n")
    srcpad1 = codeparser.get_static_pad("src")
    if not srcpad1:
        sys.stderr.write(" Unable to get mpeg4 parse src pad \n")
    srcpad1.link(sinkpad1)
    container.link(sink)

    # create an event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()
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

    #### ROI
    # roi_factor =  {'ROI_line': {'top_left': [300, 650], 'top_right': [600, 100], \
    # 'bottom_left': [850, 100], 'bottom_right': [1000, 600]}, 'video_dims': [1280, 720]}

    roi_factor =  {'ROI_line': {'top_left': [600, 100], 'top_right': [850, 100], \
    'bottom_left': [300, 650], 'bottom_right': [1000, 600]}, 'video_dims': [1280, 720]}

    # roi_factor =  {'ROI_line': {'top_left': [0, 0], 'top_right': [0, 720], \
    # 'bottom_left': [1280, 0], 'bottom_right': [1280, 720]}, 'video_dims': [1280, 720]}
    
    #logging.info(roi_factor)
    if not roi_factor :
        print("Exiting since ROI Factor is empty")
        sys.exit(1)

    ROI_line = roi_factor["ROI_line"]
    poly = [ROI_line['top_left'], ROI_line['top_right'], ROI_line['bottom_right'], ROI_line['bottom_left'], ROI_line['top_left']]

    print('ROI : ',poly)
    main(sys.argv)
    print('total_count : ',obj_counter)
    sys.exit()