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

    Args:
        filename ([type]): [description]
        frames ([type]): [description]
        threads (int, optional): [description]. Defaults to 6.
        fps (int, optional): [description]. Defaults to 30.
        crf (int, optional): [description]. Defaults to 10.
        pixel_format (str, optional): [description]. Defaults to "gray8".
        codec (str, optional): [description]. Defaults to "h264".
        close_pipe (bool, optional): [description]. Defaults to True.
        pipe ([type], optional): [description]. Defaults to None.
        slices (int, optional): [description]. Defaults to 24.
        slicecrc (int, optional): [description]. Defaults to 1.
        frame_size ([type], optional): [description]. Defaults to None.
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
        pipe.stdin.write(frames[i, :, :].astype("uint8").tobytes())

    if close_pipe:
        pipe.stdin.close()
        return None
    else:
        return pipe


def write_color_frames(
    filename,
    frames,
    threads=6,
    fps=30,
    crf=22,
    pixel_format="rgb24",
    codec="h264",
    close_pipe=True,
    pipe=None,
    slices=24,
    slicecrc=1,
    frame_size=None,
    get_cmd=False,
):
    """Write frames to avi file using the ffv1 lossless encoder
    TODO: we probably want to include a warning about multiples of 32
    for videos (then we can use pyav and some speedier tools)

    Args:
        filename ([type]): [description]
        frames ([type]): [description]
        threads (int, optional): [description]. Defaults to 6.
        fps (int, optional): [description]. Defaults to 30.
        crf (int, optional): [description]. Defaults to 22.
        pixel_format (str, optional): [description]. Defaults to "rgb24".
        codec (str, optional): [description]. Defaults to "h264".
        close_pipe (bool, optional): [description]. Defaults to True.
        pipe ([type], optional): [description]. Defaults to None.
        slices (int, optional): [description]. Defaults to 24.
        slicecrc (int, optional): [description]. Defaults to 1.
        frame_size ([type], optional): [description]. Defaults to None.
        get_cmd (bool, optional): [description]. Defaults to False.

    Returns:
        [type]: [description]
    """

    if not frame_size and type(frames) is np.ndarray:
        frame_size = "{0:d}x{1:d}".format(frames.shape[2], frames.shape[1])

    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "fatal",
        "-threads",
        str(threads),
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
        "-vcodec",
        codec,
        "-preset",
        "ultrafast",
        "-slices",
        str(slices),
        "-slicecrc",
        str(slicecrc),
        "-r",
        str(fps),
        "-crf",
        str(crf),
        filename,
    ]

    if get_cmd:
        return command

    if not pipe:
        pipe = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    for i in range(frames.shape[0]):
        pipe.stdin.write(frames[i, :, :, :].astype("uint8").tobytes())

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
    """
    Reads in frames from the .mp4/.avi file using a pipe from ffmpeg.
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


def read_color_frames(
    filename,
    frames,
    threads=6,
    fps=30,
    pixel_format="rgb24",
    frame_size=(640, 576),
    slices=24,
    slicecrc=1,
    get_cmd=False,
):
    """
    Reads in frames from the .mp4/.avi file using a pipe from ffmpeg.
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
        (len(frames), frame_size[1], frame_size[0], 3)
    )
    return video


def write_images(image_queue, filename_prefix):
    """Writes images from a multiprocessing queue to a video file
    using the write_frames function.
    Args:
        image_queue ([type]): Multiprocessing queue
        filename_prefix ([type]): data storage location
    """

    depth_pipe = None
    ir_pipe = None

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
                depth.astype(np.uint8)[None, :, :],
                codec="ffv1",
                close_pipe=False,
                pipe=depth_pipe,
            )
            ir_pipe = write_frames(
                filename_prefix / "ir.avi",
                ir.astype(np.uint8)[None, :, :],
                close_pipe=False,
                crf=14,
                pipe=ir_pipe,
            )
