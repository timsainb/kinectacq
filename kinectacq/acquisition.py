"""
Acquisition - functions for recording from azure
"""

import datetime, subprocess, numpy as np, time, sys
from multiprocessing import Process, Queue
from tqdm.auto import tqdm

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
    recording_duration,
    save_color=False,
    display_frames=False,
    display_time=False,
    depth_function=None,
    ir_function=None,
    color_function=None,
    display_resolution_downsample=2,
    display_frequency=2,
    display_time_frequency=15,
    samplerate=30,
    ir_depth_dtype=np.uint8,
    ir_depth_write_frames_kwargs={},
    color_write_frames_kwargs={},
    pbar_device=None,
):
    """Continuously captures data from Azure Kinect camera and writes to frames.


    Args:
        k4a (k4a object): Camera K4A object
        filename_prefix (pathlib2.path): File storage location
        recording_duration (float): [recording duration (seconds)]
        save_color (bool, optional): Whether to save the color data. Defaults to False.
        display_frames (bool, optional): Whether to display frames. Defaults to False.
        display_time (bool, optional): Whether to output time. Defaults to False.
        depth_function (function, optional): Filtering/processing function for depth data. Defaults to None.
        ir_function (function, optional): Filtering/processing function for ir data. Defaults to None.
        color_function (function, optional): Filtering/processing function for color data. Defaults to None.
        display_resolution_downsample (int, optional): How much to downsample display resolution. Defaults to 2
        display_frequency (int, optional): How frequently to display frames. Defaults to 2
        display_time_frequency (int, optional): How frequently to display time. Defaults to 15
        samplerate (int, optional): Samplerate of camera in Hz. Defaults to 30
    """

    # initialize the queue to write images to videos
    image_queue = Queue()
    write_process = Process(
        target=write_images,
        args=(
            image_queue,
            filename_prefix,
            ir_depth_dtype,
            save_color,
            ir_depth_write_frames_kwargs,
            color_write_frames_kwargs,
            pbar_device,
        ),
    )
    write_process.start()

    # Initialize the queue to display images on screen
    if display_frames:
        display_queue = Queue()
        display_process = Process(target=display_images, args=(display_queue,))
        display_process.start()

    # initialize K4A object
    k4a.start()

    # announce that the camera has been successfully initialized
    print("capture_from_azure initialized: {} ".format(filename_prefix.stem))

    # pre-allocate an array of timestamps (overallocate to ensure no errors)
    n_samples = int(np.ceil(samplerate * (recording_duration * 1.5)))
    system_timestamps = np.zeros(n_samples, dtype=np.uint64)
    depth_timestamps = np.zeros(n_samples, dtype=np.uint64)
    ir_timestamps = np.zeros(n_samples, dtype=np.uint64)
    if save_color:
        color_timestamps = np.zeros(n_samples, dtype=np.uint64)

    start_time = time.time()
    count = 0

    try:
        # loop while computer time is less than recording length
        while time.time() - start_time < recording_duration:
            # get output of device
            capture = k4a.get_capture()

            # if there is no depth data, this frame is dropped, so skip it
            if capture.ir is None:
                print("Dropped frame: ir")

            if capture.depth is None:
                print("Dropped frame: depth")

            if save_color:
                if capture.color is None:
                    print("Dropped frame: color")

            # grab and save the timestamps for this frame
            system_timestamps[count] = time.time_ns()
            ir_timestamps[count] = capture._depth_timestamp_usec
            depth_timestamps[count] = capture._ir_timestamp_usec
            if save_color:
                color_timestamps[count] = capture._color_timestamp_usec

            # grab depth data
            depth = capture.depth.astype(np.int16)
            ir = capture.ir.astype(np.uint16)
            if save_color:
                color = capture.color

            # preprocess depth data
            if (depth is not None) & (depth_function is not None):
                depth = depth_function(depth)

            # preprocess IR data
            if (ir is not None) & (ir_function is not None):
                ir = ir_function(ir)

            # save color information
            if save_color:
                if color is not None:
                    color = color.astype(np.uint8)
                    if color_function is not None:
                        color = color_function(color)

            # get timestamps
            if save_color:
                capture._color_timestamp_usec

            # add IR and depth data to image queue, to save
            if save_color:
                image_queue.put((ir, depth, color))
            else:
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

            count += 1

    except (OSError, KeyboardInterrupt):
        print("Recording stopped early")

    finally:
        # stop the camera object
        k4a.stop()

        # save the system and device timestamps
        np.save(filename_prefix / "system_timestamps.npy", system_timestamps[:count])
        np.save(filename_prefix / "depth_timestamps.npy", depth_timestamps[:count])
        np.save(filename_prefix / "ir_timestamps.npy", ir_timestamps[:count])
        if save_color:
            np.save(filename_prefix / "color_timestamps.npy", color_timestamps)

        nsec = (np.max(system_timestamps) - np.min(system_timestamps[:count])) * 1e-9
        # output the framerate info
        framerate = round(count / nsec, 4)
        print("Framerate ({}):{}".format(filename_prefix.stem, framerate))

        # empty tuple tells write_images to save
        image_queue.put(tuple())
        write_process.join()

        # empty tuple tells display_images to close window
        if display_frames:
            display_queue.put(tuple())
            display_process.join()


def start_recording(
    filename_prefix,
    recording_duration,
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
                "save_color": False,
                "display_frames": True,
                "display_time": False,
            },
        }
    },
    ir_depth_dtype=np.uint8,
    ir_depth_write_frames_kwargs={
        "codec": "ffv1",  # "ffv1",
        "crf": 14,
        "threads": 6,
        "fps": 30,
        "slices": 24,
        "slicecrc": 1,
        "frame_size": None,
        "get_cmd": False,
    },
    color_write_frames_kwargs={
        "codec": "h264",  # "ffv1",
        "crf": 22,
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
        recording_duration (int): Duration to record (seconds)
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

        # create a progress bar for monitoring frame writing
        pbar_device = tqdm(
            total=30 * recording_duration,
            desc="{} (frames written)".format(device_name),
        )

        # ensure a directory exists for device
        ensure_dir(filename_prefix / device_name)

        # save camera parameters
        if True:
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
                    recording_duration,
                ),
                kwargs={
                    "display_frames": devices[device_name]["process_kwargs"][
                        "display_frames"
                    ],
                    "display_time": devices[device_name]["process_kwargs"][
                        "display_time"
                    ],
                    "save_color": devices[device_name]["process_kwargs"]["save_color"],
                    "depth_function": depth_function,
                    "ir_function": ir_function,
                    "ir_depth_dtype": ir_depth_dtype,
                    "ir_depth_write_frames_kwargs": ir_depth_write_frames_kwargs,
                    "color_write_frames_kwargs": color_write_frames_kwargs,
                    "pbar_device": pbar_device,
                },
            )
        )

    for p in process_list:
        p.start()

    start_time = time.time()
    try:
        with tqdm(total=recording_duration, desc="Recording (s)") as pbar:
            while time.time() - start_time < recording_duration:
                time.sleep(1)
                pbar.update(1)
            pbar.close()
        print("Finished recording: {}".format(datetime.datetime.now()))
    except KeyboardInterrupt:
        print("Exiting: KeyboardInterrupt")
