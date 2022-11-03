#!/bin/bash

echo "\n\n[INFO] : This build works for Yolov5 and Yolov7 \n"

echo "\n[INFO] : please wait... \n"
make $1 -C nvdsinfer_custom_impl_Yolo clean
echo "\n[INFO] : clean complete... \n"
make $1  -C nvdsinfer_custom_impl_Yolo

echo "\n\n[INFO] : build complete.. \n\n"
