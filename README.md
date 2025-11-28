
#  <br> <img src="https://media0.giphy.com/media/J19OSJKmqCyP7Mfjt1/giphy.gif" width="80" height="30" /> **DeepStream 8.0 – Ultra-Optimized AI Video Analytics Stack**

### 🔖 *EXCLUSIVE Release – Fully Optimized • Low-Code • Docker-Ready*


<p align="center">
  <p align="center"><img width="70%" src="demo.gif"></p>
</p>


<p align="center">
  <b>YOLO Detection • YOLO Pose • Tracking • ROI Analytics • Multi-Stream Pipelines • Python First</b><br>
  <b>Fully Optimized · Low Code · Docker Ready · Production Tested</b>
</p>



<p align="center">
<img src="https://img.shields.io/badge/DeepStream-8.0-green?style=for-the-badge&logo=nvidia"/>
<img src="https://img.shields.io/badge/CUDA-12.x-green?style=for-the-badge&logo=nvidia"/>
<img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python"/>
<img src="https://img.shields.io/badge/Ubuntu-24.04-orange?style=for-the-badge&logo=ubuntu"/>
<img src="https://img.shields.io/badge/GPU-Driver%20570.133.20-yellow?style=for-the-badge&logo=nvidia"/>
</p>

---


# 🖥 **Recommended System Setup**


| Component              | Recommended / Supported                     |
| ---------------------- | ------------------------------------------- |
| **OS**                 | **Ubuntu 24.04 LTS**                        |
| **NVIDIA Driver**      | **570.133.20**                              |
| **CUDA Compatibility** | Fully compatible with **DeepStream 8.0**    |
| **DeepStream Version** | **DeepStream 8.0 (Production Ready)**       |
| **Docker Support**     | **Yes – NVIDIA Container Runtime required** |
| **Bare Metal Support** | Supported (Native DS 8.0 Install)           |

✔️ Fully Docker Compatible
✔️ Supports Bare-Metal
✔️ Works for Python & C++ pipelines
✔️ Optimized for YOLOv5/YOLOv8/YOLO-Pose/Custom CNNs



---

# ⚡ **Quick Start (3 Steps)**

**Setup your GPU + environment → Pull repo → Run QuickTest.sh**

---

## 1️⃣ Install NVIDIA driver

Follow NVIDIA official quick install:

🔗 [https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Quickstart.html](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Quickstart.html)

---

## 2️⃣ Clone this Repo

```bash
git clone https://github.com/bharath5673/Deepstream.git
```
---

## 3️⃣ Run Quick Demo

```bash
cd Deepstream
sh QuickTest.sh
```

Runs instantly with DS8.0-ready configs:

* YOLO Detection
* YOLO Pose
* Tracking
* Multi-Model + Multi-Stream
* ROI analytics

---

# 🎯 **What This Repo Provides**

### ✔️ **DeepStream 8.0 Templates (Production Ready)**

• Multi-model pipelines
• YOLO detection + pose
• Trajectory tracking
• ROI counting
• Multi-stream tiled processing
• Triton-ready configs
• Python & C++ versions

### ✔️ **Fully-Optimized & Low-Code**

Minimal code → Maximum performance.
Just edit config files & run.

### ✔️ **Docker-Ready**

Build + run your inference stack inside an isolated DS8.0 environment.

---

# 🌟 **Showcase Gallery**

### 🔥 Multi-Model Pipeline

<p align="center"><img width="70%" src="https://user-images.githubusercontent.com/33729709/210167600-6a677a62-40ee-4afa-b484-d0d56e78e230.gif"></p>

🔗 `DeepStream-Configs/DeepStream-MultiModel`

---

### 🟦 ROI Based Counting (Python)

<p align="center"><img width="70%" src="https://user-images.githubusercontent.com/33729709/211142186-a9ecd225-4f90-4310-91df-862e243f8833.gif"></p>

🔗 `DeepStream-Python/`

---

### 🟧 Yolo POSE

<p align="center"><img width="70%" src="pose_demo.gif"></p>

🔗 `DeepStream-Python/`

---

### ⚙️ Custom CNN → DeepStream in 3 Steps

<p align="center"><img width="60%" src="https://user-images.githubusercontent.com/33729709/222878115-7e34dbe3-ac50-4388-9430-e82db1e31a37.jpeg"></p>

🔗 `CNN-to-DeepStream/`

---

### ⚡ Quick Demo

```bash
cd Deepstream
sh QuickTest.sh
```

---

# 📂 **Repo Structure**

```
Deepstream/
│
├── DeepStream-Configs/
│   ├── DeepStream-MultiModel/
│   ├── test/ (multi-stream, tiling, custom pipelines)
│
├── DeepStream-Python/
│   ├── yolo
│   ├── yolo + pose
│   ├── ROI counting
│   ├── trajectory tracking
│
├── CNN-to-DeepStream/
│
└── QuickTest.sh
```

---


---

# 🙏 **Acknowledgements**

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/2/21/Nvidia_logo.svg" height="55"/>
  &nbsp;&nbsp;&nbsp;
  <img src="https://raw.githubusercontent.com/ultralytics/assets/main/logo/Ultralytics_Logomark_White.png" height="55"/>
  &nbsp;&nbsp;&nbsp;
  <img src="https://raw.githubusercontent.com/pytorch/pytorch/master/docs/source/_static/img/pytorch-logo-dark.png" height="55"/>
  &nbsp;&nbsp;&nbsp;
  <img src="https://opencv.org/wp-content/uploads/2020/07/OpenCV_logo_black.png" height="55"/>
</p>

<p align="center">
<b>Massive respect to the open-source community powering the DeepStream 8.0 ecosystem.</b><br>
<i>Models, configs, tracking logic, pose models, and deployment workflows are built on top of these amazing projects.</i>
</p>

---

## 🔰 **Credits & Sources**

<details>
<summary><b>🟩 YOLO Ecosystem</b></summary><br>

* [https://github.com/marcoslucianops/DeepStream-Yolo](https://github.com/marcoslucianops/DeepStream-Yolo)
* [https://github.com/ultralytics/ultralytics](https://github.com/ultralytics/ultralytics)
* [https://github.com/ultralytics/yolov5](https://github.com/ultralytics/yolov5)
* [https://github.com/ultralytics/yolov3](https://github.com/ultralytics/yolov3)
* [https://github.com/WongKinYiu/yolor](https://github.com/WongKinYiu/yolor)
* [https://github.com/WongKinYiu/PyTorch_YOLOv4](https://github.com/WongKinYiu/PyTorch_YOLOv4)
* [https://github.com/WongKinYiu/ScaledYOLOv4](https://github.com/WongKinYiu/ScaledYOLOv4)
* [https://github.com/Megvii-BaseDetection/YOLOX](https://github.com/Megvii-BaseDetection/YOLOX)
* [https://github.com/TexasInstruments/edgeai-yolov5/tree/yolo-pose](https://github.com/TexasInstruments/edgeai-yolov5/tree/yolo-pose)

</details>

---

<details>
<summary><b>🟦 Core AI / CV Architectures</b></summary><br>

* [https://github.com/AlexeyAB/darknet](https://github.com/AlexeyAB/darknet)
* [https://github.com/DingXiaoH/RepVGG](https://github.com/DingXiaoH/RepVGG)
* [https://github.com/JUGGHM/OREPA_CVPR2022](https://github.com/JUGGHM/OREPA_CVPR2022)

</details>

---

<details>
<summary><b>🟧 NVIDIA + DeepStream + Metropolis</b></summary><br>

* NVIDIA DeepStream SDK
* NVIDIA Metropolis documentation
* NVIDIA TensorRT & ONNX conversion tools
* NVIDIA samples & reference apps

</details>

---

<details>
<summary><b>🔵 Tracking, ROI, Multi-Model Inspirations</b></summary><br>

* NvDCF + KLT Tracker designs
* MOT community publications
* ROI analytics from DS sample apps
* Common open-source tracking repos

</details>

---

## ⭐ **Special Thanks**

<p align="center">
Thank you to every researcher, engineer, and developer who has contributed to<br>
YOLO, tracking algorithms, CNN architectures, and DeepStream integration guides.
</p>

<p align="center"><b>This project stands on the shoulders of giants.</b></p>

---

