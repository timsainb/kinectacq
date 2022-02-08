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


def testfcn(x):
    """
    Parametric UMAP subclassing UMAP-learn, based on keras/tensorflow.
    There is also a non-parametric implementation contained within to compare
    with the base non-parametric implementation.
    Parameters
    ----------
    optimizer : tf.keras.optimizers, optional
        The tensorflow optimizer used for embedding, by default None
    batch_size : int, optional
        size of batch used for batch training, by default None
    dims :  tuple, optional
        dimensionality of data, if not flat (e.g. (32x32x3 images for ConvNet), by default None
    encoder : tf.keras.Sequential, optional
        The encoder Keras network
    decoder : tf.keras.Sequential, optional
        the decoder Keras network
    parametric_embedding : bool, optional
        Whether the embedder is parametric or non-parametric, by default True
    parametric_reconstruction : bool, optional
        Whether the decoder is parametric or non-parametric, by default False
    parametric_reconstruction_loss_fcn : bool, optional
        What loss function to use for parametric reconstruction, by default tf.keras.losses.BinaryCrossentropy
    parametric_reconstruction_loss_weight : float, optional
        How to weight the parametric reconstruction loss relative to umap loss, by default 1.0
    autoencoder_loss : bool, optional
        [description], by default False
    reconstruction_validation : array, optional
        validation X data for reconstruction loss, by default None
    loss_report_frequency : int, optional
        how many times per epoch to report loss, by default 1
    n_training_epochs : int, optional
        number of epochs to train for, by default 1
    global_correlation_loss_weight : float, optional
        Whether to additionally train on correlation of global pairwise relationships (>0), by default 0
    run_eagerly : bool, optional
        Whether to run tensorflow eagerly
    keras_fit_kwargs : dict, optional
        additional arguments for model.fit (like callbacks), by default {}
    """
    return


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
    write_process = Process(target=write_images, args=(image_queue, filename_prefix))
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
    depth_function=None,
    ir_function=None,
):
    """
    Runs a recording session by running a subprocess for each camera.
    Args:
        filename_prefix (str):
        recording_length (int):
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
                },
            )
        )

    for p in process_list:
        p.start()
