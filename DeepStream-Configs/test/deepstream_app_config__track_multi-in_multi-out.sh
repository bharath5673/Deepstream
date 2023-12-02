### Use case 1

# Two video sources are mux’ed together using nvstreammux.
# The muxer’s output goes to nvinfer which is configured with batch-size=2.
# After nvinfer, we use nvstreamdemux to display the contents of video source 0, and 1 along with inference output for each overlaid using nvdsosd plugin on two separate windows.

gst-launch-1.0 -e nvstreammux name=mux batch-size=2 width=1920 height=1080 ! nvinfer config-file-path=/home/bharath5673/Desktop/Projects/Deepstream/DeepStream/DeepStream-Yolo/config_infer_primary_yoloV5.txt batch-size=2
! nvstreamdemux name=demux filesrc location=/ opt/nvidia/deepstream/deepstream/samples/streams/sample_1080p_h264.mp4 ! qtdemux ! h264parse ! nvv4l2decoder ! queue !
mux.sink_0 filesrc location=/opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264 ! h264parse ! nvv4l2decoder !
queue ! mux.sink_1 demux.src_0 ! "video/x-raw(memory:NVMM), format=NV12" ! queue ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA" ! nvdsosd !
nvvideoconvert ! nveglglessink demux.src_1 ! queue ! "video/x-raw(memory:NVMM), format=NV12" ! queue ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA" ! nvdsosd ! nveglglessink




# ###Use case 2

# # Two video sources are mux’ed together using nvstreammux.
# # The muxer’s output goes to nvinfer which is configured with batch-size=2.
# # After nvinfer, we use nvstreamdemux to write the contents of video source 0 along with inference output overlaid using nvdsosd plugin to a file.
# # The contents of video source 1 post demux is directly displayed on screen using nveglglessink plugin

# gst-launch-1.0 -e nvstreammux name=mux batch-size=2 width=1920 height=1080 ! nvinfer config-file-path=/home/acer/Desktop/Projects/Deepstream-Projects/DeepStream-Yolo/config_infer_primary_yoloV5.txt batch-size=2  ! nvstreamdemux name=demux filesrc location=/opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264 ! h264parse ! nvv4l2decoder ! queue ! mux.sink_0 filesrc location=/opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264 ! h264parse ! nvv4l2decoder ! queue ! mux.sink_1 demux.src_0 ! "video/x-raw(memory:NVMM), format=NV12" ! queue ! nvvideoconvert ! "video/x-raw(memory:NVMM), format=RGBA" ! nvdsosd ! nvvideoconvert ! nvv4l2h264enc ! h264parse ! qtmux ! filesink location=./out.mp4 demux.src_1 ! queue ! nveglglessink





# ###Use case 3

# # Use case 3 demonstrates displaying both streams as it is in two separate windows.
# # Two video sources are mux’ed together using nvstreammux.
# # The muxer’s output goes to nvinfer which is configured with batch-size=2.
# # After nvinfer, we use nvstreamdemux to display the contents of video source 0, and 1 on two separate windows.

# gst-launch-1.0 -e nvstreammux name=mux batch-size=2 width=1920 height=1080 ! nvinfer config-file-path=/home/acer/Desktop/Projects/Deepstream-Projects/DeepStream-Yolo/config_infer_primary_yoloV5.txt batch-size=2  ! nvstreamdemux name=demux filesrc location=/opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264 ! h264parse ! nvv4l2decoder ! queue ! mux.sink_0 filesrc location=/opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264 ! h264parse ! nvv4l2decoder ! queue ! mux.sink_1 demux.src_0 ! queue ! nvvideoconvert ! nveglglessink demux.src_1 ! queue ! nveglglessink