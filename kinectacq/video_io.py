import datetime, subprocess, numpy as np, cv2, time, sys
from multiprocessing import Process, Queue


def get_number_of_frames(filepath):
    command = "ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of default=nokey=1:noprint_wrappers=1"
    out = subprocess.Popen(
        command.split(" ") + [filepath],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, stderr = out.communicate()
    return int(stdout.decode("utf8").strip("\n"))


def write_frames(
    filename,
    frames,
    video_dtype=np.uint8,
    threads=6,
    fps=30,
    crf=10,
    pixel_format="gray8",
    codec="h264",
    close_pipe=True,
    pipe=None,
    slices=24,
    slicecrc=1,
    frame_size=None,
    get_cmd=False,
):

    """Write frames to avi file using the ffv1 lossless encoder
    TODO: Write color frames

    Args:
        filename (str): Where the file is saved
        frames (np.array): video data to be written
        threads (int, optional): number of threads to use to write video. Defaults to 6.
        fps (int, optional): Sets the framerate. Defaults to 30.
        crf (int, optional): Constant Rate Factor. 0 is lossless, 23 is default. Defaults to 10.
        pixel_format (str, optional): Sets the pixel format. Defaults to "gray8".
        codec (str, optional): Sets the video codec. Defaults to "h264".
        close_pipe (bool, optional): Whether to close the pipe after writing. Defaults to True.
        pipe (subprocess.Popen, optional): The current pipe to write frames. If None,
            creates a pipe. Defaults to None.
        slices (int, optional): Each frame is split into this number of slices.
            This affects multithreading performance, as well as filesize: Increasing
            the number of slices might speed up performance, but also increases the filesize. Defaults to 24.
        slicecrc (int, optional): 0=off, 1=on
            Enabling this option adds CRC information to each slice. This makes
            it possible for a decoder to detect errors in the bitstream, rather than
            blindly decoding a broken slice.. Defaults to 1.
        frame_size ([type], optional): frame size (e.g. 352x240). Defaults to None.
        get_cmd (bool, optional): [description]. Defaults to False.

    Returns:
        [type]: [description]
    """

    # we probably want to include a warning about multiples of 32 for videos
    # (then we can use pyav and some speedier tools)

    if not frame_size and type(frames) is np.ndarray:
        frame_size = "{0:d}x{1:d}".format(frames.shape[2], frames.shape[1])

    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "fatal",
        "-framerate",
        str(fps),
        "-f",
        "rawvideo",
        "-s",
        frame_size,
        "-pix_fmt",
        pixel_format,
        "-i",
        "-",
        "-an",
        "-crf",
        str(crf),
        "-vcodec",
        codec,
        "-preset",
        "ultrafast",
        "-threads",
        str(threads),
        "-slices",
        str(slices),
        "-slicecrc",
        str(slicecrc),
        "-r",
        str(fps),
        filename,
    ]

    if get_cmd:
        return command

    if not pipe:
        pipe = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    for i in range(frames.shape[0]):
        pipe.stdin.write(frames[i, :, :].astype(video_dtype).tobytes())

    if close_pipe:
        pipe.stdin.close()
        return None
    else:
        return pipe


def read_frames(
    filename,
    frames,
    threads=6,
    fps=30,
    pixel_format="gray8",
    frame_size=(640, 576),
    slices=24,
    slicecrc=1,
    get_cmd=False,
):
    """Reads in frames from the .mp4/.avi file using a pipe from ffmpeg.

    Args:
        filename (str): filename to get frames from
        frames (list or 1d numpy array): list of frames to grab
        threads (int): number of threads to use for decode
        fps (int): frame rate of camera in Hz
        pixel_format (str): ffmpeg pixel format of data
        frame_size (str): wxh frame size in pixels
        slices (int): number of slices to use for decode
        slicecrc (int): check integrity of slices
    Returns:
        3d numpy array:  frames x h x w
    """

    command = [
        "ffmpeg",
        "-loglevel",
        "fatal",
        "-ss",
        str(datetime.timedelta(seconds=frames[0] / fps)),
        "-i",
        filename,
        "-vframes",
        str(len(frames)),
        "-f",
        "image2pipe",
        "-s",
        "{:d}x{:d}".format(frame_size[0], frame_size[1]),
        "-pix_fmt",
        pixel_format,
        "-threads",
        str(threads),
        "-slices",
        str(slices),
        "-slicecrc",
        str(slicecrc),
        "-vcodec",
        "rawvideo",
        "-",
    ]

    if get_cmd:
        return command

    pipe = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = pipe.communicate()
    if err:
        print("error", err)
        return None
    video = np.frombuffer(out, dtype="uint8").reshape(
        (len(frames), frame_size[1], frame_size[0])
    )
    return video


def write_images(
    image_queue,
    filename_prefix,
    _dtype=np.uint8,
    write_frames_kwargs={},
):
    """Writes images from a multiprocessing queue to a video file
    using the write_frames function.

    Args:
        image_queue ([type]): Multiprocessing queue
        filename_prefix ([type]): data storage location
    """

    depth_pipe = None
    ir_pipe = None

    if _dtype == np.uint8:
        pixel_format = "gray8"
    elif _dtype == np.uint16:
        pixel_format = "gray16"
    else:
        raise ValueError("format for dtype {} has not been defined".format(_dtype))

    while True:
        data = image_queue.get()
        if len(data) == 0:
            depth_pipe.stdin.close()
            ir_pipe.stdin.close()
            break
        else:
            ir, depth = data
            depth_pipe = write_frames(
                filename_prefix / "depth.avi",
                depth.astype(_dtype)[None, :, :],
                close_pipe=False,
                pipe=depth_pipe,
                pixel_format=pixel_format,
                video_dtype=_dtype,
                **write_frames_kwargs
            )
            ir_pipe = write_frames(
                filename_prefix / "ir.avi",
                ir.astype(_dtype)[None, :, :],
                close_pipe=False,
                pipe=ir_pipe,
                pixel_format=pixel_format,
                video_dtype=_dtype,
                **write_frames_kwargs
            )
