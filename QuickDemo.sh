#!/bin/bash
set -e

# -----------------------------------
# CONFIG
# -----------------------------------
export DISPLAY=:1
xhost +

CONTAINER_NAME="DS-temp"
IMAGE_NAME="bharath5673/deepstream8-yolo-python-x86:latest"

PROJECT_ROOT="./"

# Paths to copy
COPY_PATHS=(
    "$PROJECT_ROOT/DeepStream-Configs"
    "$PROJECT_ROOT/weights"
    "$PROJECT_ROOT/DeepStream-Python"
    "./inputs"
    "./outputs"
    "./test_ds.py"
)

# -----------------------------------
# REMOVE OLD CONTAINER
# -----------------------------------
docker rm -f $CONTAINER_NAME 2>/dev/null || true

echo "Creating container..."
docker create --gpus all \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  --network host \
  --privileged \
  -w /root \
  -v "$(pwd)/outputs:/root/outputs" \
  --name $CONTAINER_NAME \
  $IMAGE_NAME sleep infinity

echo "Starting container..."
docker start $CONTAINER_NAME

# -----------------------------------
# COPY FILES INTO CONTAINER
# -----------------------------------
echo "Copying required project folders..."
for path in "${COPY_PATHS[@]}"; do
    docker cp "$path" "$CONTAINER_NAME:/root/"
done

# -----------------------------------
# RUN MAIN TEST SCRIPT
# -----------------------------------
echo "Running test_ds.py..."
docker exec -it $CONTAINER_NAME python3 /root/test_ds.py

# -----------------------------------
# CLEANUP
# -----------------------------------
echo "Cleaning up container..."
docker rm -f $CONTAINER_NAME

sudo chown -R $USER:$USER ./outputs

echo "Done!"
