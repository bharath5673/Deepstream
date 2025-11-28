import subprocess

# --------------------------------------------
# MANUALLY LIST FILES YOU WANT TO RUN
# --------------------------------------------
FILES_TO_RUN = [
    # "DeepStream-Python/deepstream_test_1.py",
    "DeepStream-Python/deepstream_test_yolo_save_vid.py",
    "DeepStream-Python/deepstream_test_yolo_track_save_vid.py",
    "DeepStream-Python/deepstream_test_yolo_track_ROI_save_vid.py",
    "DeepStream-Python/deepstream_test_yolo_track_pose_save_vid.py"
    # "DeepStream-Python/deepstream_test_yolo_track_multimodel.py"
]

# Arguments you want to pass to every script
COMMON_ARGS = [
    "file:///root/inputs/people-detection.mp4",
    "--display"
]

def main():
    for file in FILES_TO_RUN:
        print(f"\n==============================")
        print(f" RUNNING: {file}")
        print(f"==============================")

        try:
            subprocess.run(["python3", file] + COMMON_ARGS, check=True)
        except subprocess.CalledProcessError:
            print(f"❌ ERROR while running {file}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()