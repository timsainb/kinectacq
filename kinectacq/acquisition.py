"""
Acquisition - functions for recording from azure
"""

import datetime, subprocess, numpy as np, time, sys
from multiprocessing import Process, Queue

from pyk4a import (
    PyK4A,
    Config,
    ColorResolution,
    DepthMode,
    WiredSyncMode,
)


from kinectacq.video_io import write_images
from kinectacq.visualization import display_images
from kinectacq.paths import ensure_dir


def capture_from_azure(
    k4a,
    filename_prefix,
    recording_length,
    display_frames=False,
    display_time=False,
    depth_function=None,
    ir_function=None,
    display_resolution_downsample=2,
    display_frequency=2,
    display_time_frequency=15,
    video_dtype=np.uint8,
    write_frames_kwargs={},
):
    """Continuously captures data from Azure Kinect camera and writes to frames.


    Args:
        k4a (k4a object): Camera K4A object
        filename_prefix (pathlib2.path): File storage location
        recording_length (float): [recording duration (seconds)]
        display_frames (bool, optional): Whether to display frames. Defaults to False.
        display_time (bool, optional): Whether to output time. Defaults to False.
        display_resolution_downsample (int, optional): How much to downsample display resolution. Defaults to 2
        display_frequency (int, optional): How frequently to display frames. Defaults to 2
        display_time_frequency (int, optional): How frequently to display time. Defaults to 15
    """
    # initialize the queue to write images to videos
    image_queue = Queue()
    write_process = Process(
        target=write_images,
        args=(image_queue, filename_prefix, video_dtype, write_frames_kwargs),
    )
    write_process.start()

    # Initialize the queue to display images on screen
    if display_frames:
        display_queue = Queue()
        display_process = Process(target=display_images, args=(display_queue,))
        display_process.start()

    # initialize K4A object
    k4a.start()

    # keep a list of timestamps
    system_timestamps = []
    device_timestamps = []
    start_time = time.time()
    count = 0

    try:
        # loop while computer time is less than recording length
        while time.time() - start_time < recording_length:
            # get output of device
            capture = k4a.get_capture()

            # if there is no depth data, this frame is dropped, so skip it
            if capture.depth is None:
                print("Dropped frame")
                continue

            # grab and save the timestamps for this frame
            system_timestamps.append(time.time())
            device_timestamps.append(capture.depth_timestamp_usec)

            # grab depth data
            depth = capture.depth.astype(np.int16)
            ir = capture.ir.astype(np.uint16)

            # preprocess depth data
            if depth_function is not None:
                depth = depth_function(depth)

            # preprocess IR data
            if ir_function is not None:
                ir = ir_function(ir)

            # add IR and depth data to image queue, to save
            image_queue.put((ir, depth))

            # every n frames, write to display
            # TODO add freq as variable
            if display_frames and count % display_frequency == 0:
                display_queue.put(
                    (
                        ir[
                            ::display_resolution_downsample,
                            ::display_resolution_downsample,
                        ],
                    )
                )

            # every n frames, write the time on the notebook
            # TODO rewrite as status bar
            if display_time and count % display_time_frequency == 0:
                sys.stdout.write(
                    "\rRecorded "
                    + repr(int(time.time() - start_time))
                    + " out of "
                    + repr(recording_length)
                    + " seconds"
                )
            count += 1

    except OSError:
        print("Recording stopped early")

    finally:
        # stop the camera object
        k4a.stop()

        # save the system and device timestamps
        system_timestamps = np.array(system_timestamps)
        np.save(filename_prefix / "system_timestamps.npy", system_timestamps)
        np.save(filename_prefix / "device_timestamps.npy", device_timestamps)

        # output the framerate info
        print(
            " - Frame rate = ",
            len(system_timestamps)
            / (system_timestamps.max() - system_timestamps.min()),
        )

        # empty tuple tells write_images to save
        image_queue.put(tuple())
        write_process.join()

        # empty tuple tells display_images to close window
        if display_frames:
            display_queue.put(tuple())
            display_process.join()


def start_recording(
    filename_prefix,
    recording_length,
    devices={
        "master": {
            "id": "master",
            "pyk4a_config": {
                "color_resolution": ColorResolution.RES_720P,
                "depth_mode": DepthMode.NFOV_UNBINNED,
                "synchronized_images_only": False,
                "wired_sync_mode": WiredSyncMode.MASTER,
            },
            "process_kwargs": {
                "display_frames": True,
                "display_time": False,
            },
        }
    },
    video_dtype=np.uint8,
    write_frames_kwargs={
        "codec": "ffv1",
        "crf": 14,
        "threads": 6,
        "fps": 30,
        "slices": 24,
        "slicecrc": 1,
        "frame_size": None,
        "get_cmd": False,
    },
    depth_function=None,
    ir_function=None,
):
    """Runs a recording session by running a subprocess for each camera.

    Args:
        filename_prefix (str): Prefix of filename
        recording_length (int): Duration to record (seconds)
        devices (dict): Dictionary of config info for each device
        depth_function (function): Function for processing depth data
        ir_function (function): Function for processing IR data
    """

    process_list = []
    for device_name in devices:

        # Create a k4a object referencing master
        k4a_obj = PyK4A(
            Config(**devices[device_name]["pyk4a_config"]),
            device_id=devices[device_name]["id"],
        )

        # ensure a directory exists for device
        ensure_dir(filename_prefix / device_name)

        # save camera parameters
        k4a_obj.start()
        time.sleep(1)
        k4a_obj.save_calibration_json(
            filename_prefix / device_name / "calibration.json"
        )
        k4a_obj.stop()

        # create a subprocess to run acqusition with that camera
        process_list.append(
            Process(
                target=capture_from_azure,
                args=(
                    k4a_obj,
                    filename_prefix / device_name,
                    recording_length,
                ),
                kwargs={
                    "display_frames": devices[device_name]["process_kwargs"][
                        "display_frames"
                    ],
                    "display_time": devices[device_name]["process_kwargs"][
                        "display_time"
                    ],
                    "depth_function": depth_function,
                    "ir_function": ir_function,
                    "video_dtype": video_dtype,
                    "write_frames_kwargs": write_frames_kwargs,
                },
            )
        )

    for p in process_list:
        p.start()
