
# git clone --recurse-submodules  https://github.com/bharath5673/Deepstream.git

cd Deepstream
cd DeepStream-Configs

cd DeepStream-Yolo
pwd
CUDA_VER=12.1 make -C nvdsinfer_custom_impl_Yolo
cd ..

cd DeepStream-Yolo-Face
pwd
export CUDA_VER=12.1
CUDA_VER=12.1 
make -C nvdsinfer_custom_impl_Yolo_face
make
cd ..

cd DeepStream-Yolo-Pose
pwd
export CUDA_VER=12.1
make -C nvdsinfer_custom_impl_Yolo_pose
make
cd ..

cd DeepStream-Yolo-Seg
pwd
CUDA_VER=12.1 make -C nvdsinfer_custom_impl_Yolo_seg
cd ..
echo '\n\nbuild successful\n\n'


cd ..
ls weights
echo '\n\nCopying weight files\n\n'
cp -r weights/yolov8s.onnx DeepStream-Configs/DeepStream-Yolo
cp -r weights/yolov8s-seg.onnx DeepStream-Configs/DeepStream-Yolo-Seg
cp -r weights/yolov8n-face.onnx DeepStream-Configs/DeepStream-Yolo-Face
cp -r weights/yolov8s-pose.onnx DeepStream-Configs/DeepStream-Yolo-Pose


echo '\n\nRunning Object Detection Demo\n\n'
cd DeepStream-Configs/DeepStream-Yolo
sed -i 's/config_infer_primary\.txt/config_infer_primary_yoloV8\.txt/g' deepstream_app_config.txt
deepstream-app -c deepstream_app_config.txt
cd ..
cd ..

echo '\n\nRunning Face Detection Demo\n\n'
cd DeepStream-Configs/DeepStream-Yolo-Face
pwd
ls
./deepstream -s file:///opt/nvidia/deepstream/deepstream/samples/streams/sample_1080p_h264.mp4 -c config_infer_primary_yoloV8_face.txt
cd ..
cd ..

echo '\n\nRunning Pose Detection Demo\n\n'
cd DeepStream-Configs/DeepStream-Yolo-Pose
./deepstream -s file:///opt/nvidia/deepstream/deepstream/samples/streams/sample_1080p_h264.mp4 -c config_infer_primary_yoloV8_pose.txt
cd ..
cd ..

echo '\n\nRunning Instance Segmenation Demo\n\n'
cd DeepStream-Configs/DeepStream-Yolo-Seg
# sed -i 's/config_infer_primary\.txt/config_infer_primary_yoloV8-seg\.txt/g' deepstream_app_config.txt
deepstream-app -c deepstream_app_config.txt
cd ..
cd ..


echo '\n\nQuick Fininshed..\n\n'