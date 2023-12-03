# Deepstream deepstream-6.3-ubuntu20.04

1. Make sure that you [install Deepstream 6.3 as shown in this Guide](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Quickstart.html)

2. Clone the repository recursively:

    ```
    git clone --recurse-submodules  https://github.com/bharath5673/Deepstream.git
    ```

    If you already cloned and forgot to use `--recurse-submodules` you can run `git submodule update --init`

3. follow the instructions as shown in the repos..


![output3](https://user-images.githubusercontent.com/33729709/210167948-382731f2-6905-44ca-aaf9-d35ae9d099a0.gif)





___
___
<br>
<img src="https://media0.giphy.com/media/J19OSJKmqCyP7Mfjt1/giphy.gif" width="80" height="30" />    
<h2>DeepStream MultiModel</h2>

![output3](https://user-images.githubusercontent.com/33729709/210167600-6a677a62-40ee-4afa-b484-d0d56e78e230.gif)


@ https://github.com/bharath5673/Deepstream/tree/main/DeepStream-Configs/DeepStream-MultiModel

<br>

___
___
<br>
<img src="https://media0.giphy.com/media/J19OSJKmqCyP7Mfjt1/giphy.gif" width="80" height="30" />    
<h2>ROI based counts on deepstream</h2>


![output](https://user-images.githubusercontent.com/33729709/211142186-a9ecd225-4f90-4310-91df-862e243f8833.gif)

@ https://github.com/bharath5673/Deepstream/tree/main/DeepStream-Python
<br>

___
___
<br>
<img src="https://media0.giphy.com/media/J19OSJKmqCyP7Mfjt1/giphy.gif" width="80" height="30" />    
<h2>Trajectory tracking on deepstream</h2>



![output3](https://user-images.githubusercontent.com/33729709/215127343-b540a737-d3bc-4fe8-8835-050497d325a3.gif)


@ https://github.com/bharath5673/Deepstream/tree/main/DeepStream-Python
<br>

___
___

<br>

<img src="https://user-images.githubusercontent.com/33729709/222878237-fb9e902e-79ef-4393-9bb6-e1bc9b3a77b3.gif" width="120" height="40" />    
<h2>Custom CNN to DeepStream in simple 3 steps </h2>


![5ef98519-07bb-4983-81e1-81a3debfdd462](https://user-images.githubusercontent.com/33729709/222878115-7e34dbe3-ac50-4388-9430-e82db1e31a37.jpeg)


START @ https://github.com/bharath5673/Deepstream/tree/main/CNN-to-DeepStream

<br>

___
___


<br>
<h2>Easy steps installation</h2> @
https://gist.github.com/bharath5673/800a18cc7474ce9c22fda6deaaa98354
</br>

___
___


<br>
<img src="https://user-images.githubusercontent.com/33729709/222878237-fb9e902e-79ef-4393-9bb6-e1bc9b3a77b3.gif" width="120" height="40" />    
<h2>Deepstream ONNXified Quick DEMO</h2>

```
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

```

___
___
