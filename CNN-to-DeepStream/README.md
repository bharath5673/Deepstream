# Custom CNN to DeepStream in Easy 3 steps

___
___

### step 1 : CNN model
___


##### here for instance im using UTKFace dataset for age or gender classifications using CNN model.

<a href="https://susanqq.github.io/UTKFace/">UTKFace</a> dataset is a large-scale face dataset with long age span (range from 0 to 116 years old). The dataset consists of over 20,000 face images with annotations of age, gender, and ethnicity. The images cover large variation in pose, facial expression, illumination, occlusion, resolution, etc. This dataset could be used on a variety of tasks, e.g., face detection, age estimation, age progression/regression, landmark localization, etc. 


##### load utkface images and train accordingly that have used in <a href="https://github.com/bharath5673/Deepstream/blob/main/CNN-to-DeepStream/custom_CNN_utkTest.ipynb">this notebook</a>

___

### step 2 : Model Migration

___

##### after model training is done convert that weights file from keras to onnx using <a href="https://github.com/bharath5673/Deepstream/blob/main/CNN-to-DeepStream/convert_2_onnx.py">convert_2_onnx.py</a>

```
### venv recommanded

pip install -r convert_2_onnx_requriements.txt

python3 convert_2_onnx.py  ### here im using for gender , and u can change accordingly

```

___


### step 3 : Deepstream config

___

##### now u can configure those onnx file as pgie or sgie for ur DeepStream applications

```
##sgie1
....
[property]
enable=1
gpu-id=0

onnx-file=weights/gender_cnn/gender.onnx
labelfile-path=weights/gender_cnn/labels.txt

network-input-order=1
infer-dims= 3;224;224
batch-size=1
....

```
for reference : <a href="https://github.com/bharath5673/Deepstream/blob/main/DeepStream-MultiModel/face/dstest2_sgie1_config.txt">dstest2_sgie1_config.txt</a>

