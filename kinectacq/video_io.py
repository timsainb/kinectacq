import datetime, subprocess, numpy as np, cv2, time, sys
from multiprocessing import Process, Queue
from pyk4a import *



def get_number_of_frames(filepath):
    command = 'ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of default=nokey=1:noprint_wrappers=1'
    out = subprocess.Popen(command.split(' ')+[filepath], 
               stdout=subprocess.PIPE, 
               stderr=subprocess.STDOUT)
    stdout,stderr = out.communicate()    
    return int(stdout.decode('utf8').strip('\n'))


def write_frames(filename, frames, threads=6, fps=30, crf=10,
                 pixel_format='gray8', codec='h264', close_pipe=True,
                 pipe=None, slices=24, slicecrc=1, frame_size=None, get_cmd=False):
    """
    Write frames to avi file using the ffv1 lossless encoder
    """

    # we probably want to include a warning about multiples of 32 for videos
    # (then we can use pyav and some speedier tools)

    if not frame_size and type(frames) is np.ndarray:
        frame_size = '{0:d}x{1:d}'.format(frames.shape[2], frames.shape[1])

    command = ['ffmpeg',
               '-y',
               '-loglevel', 'fatal',
               '-framerate', str(fps),
               '-f', 'rawvideo',
               '-s', frame_size,
               '-pix_fmt', pixel_format,
               '-i', '-',
               '-an',
               '-crf',str(crf),
               '-vcodec', codec,
               '-preset', 'ultrafast',
               '-threads', str(threads),
               '-slices', str(slices),
               '-slicecrc', str(slicecrc),
               '-r', str(fps),
               filename]

    if get_cmd:
        return command

    if not pipe:
        pipe = subprocess.Popen(
            command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    for i in range(frames.shape[0]):
        pipe.stdin.write(frames[i,:,:].astype('uint8').tobytes())

    if close_pipe:
        pipe.stdin.close()
        return None
    else:
        return pipe


def write_color_frames(filename, frames, threads=6, fps=30, crf=22,
                 pixel_format='rgb24', codec='h264',close_pipe=True,
                 pipe=None,  slices=24, slicecrc=1, frame_size=None, get_cmd=False):
    """
    Write frames to avi file using the ffv1 lossless encoder
    """

    # we probably want to include a warning about multiples of 32 for videos
    # (then we can use pyav and some speedier tools)

    if not frame_size and type(frames) is np.ndarray:
        frame_size = '{0:d}x{1:d}'.format(frames.shape[2], frames.shape[1])

    command = ['ffmpeg',
               '-y',
               '-loglevel', 'fatal',
               '-threads', str(threads),
               '-framerate', str(fps),
               '-f', 'rawvideo',
               '-s', frame_size,
               '-pix_fmt', pixel_format,
               '-i', '-',
               '-an',
               '-vcodec', codec,
               '-preset', 'ultrafast',
               '-slices', str(slices),
               '-slicecrc', str(slicecrc),
               '-r', str(fps),
               '-crf',str(crf),
               filename]


    if get_cmd:
        return command

    if not pipe:
        pipe = subprocess.Popen(
            command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    for i in range(frames.shape[0]):
        pipe.stdin.write(frames[i,:,:,:].astype('uint8').tobytes())

    if close_pipe:
        pipe.stdin.close()
        return None
    else:
        return pipe

    

def read_frames(filename, frames, threads=6, fps=30,
                pixel_format='gray8', frame_size=(640,576),
                slices=24, slicecrc=1, get_cmd=False):
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
        'ffmpeg',
        '-loglevel', 'fatal',
        '-ss', str(datetime.timedelta(seconds=frames[0]/fps)),
        '-i', filename,
        '-vframes', str(len(frames)),
        '-f', 'image2pipe',
        '-s', '{:d}x{:d}'.format(frame_size[0], frame_size[1]),
        '-pix_fmt', pixel_format,
        '-threads', str(threads),
        '-slices', str(slices),
        '-slicecrc', str(slicecrc),
        '-vcodec', 'rawvideo',
        '-'
    ]

    if get_cmd:
        return command

    pipe = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = pipe.communicate()
    if(err):
        print('error', err)
        return None
    video = np.frombuffer(out, dtype='uint8').reshape((len(frames), frame_size[1], frame_size[0]))
    return video


def read_color_frames(filename, frames, threads=6, fps=30,
                pixel_format='rgb24', frame_size=(640,576),
                slices=24, slicecrc=1, get_cmd=False):
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
        'ffmpeg',
        '-loglevel', 'fatal',
        '-ss', str(datetime.timedelta(seconds=frames[0]/fps)),
        '-i', filename,
        '-vframes', str(len(frames)),
        '-f', 'image2pipe',
        '-s', '{:d}x{:d}'.format(frame_size[0], frame_size[1]),
        '-pix_fmt', pixel_format,
        '-threads', str(threads),
        '-slices', str(slices),
        '-slicecrc', str(slicecrc),
        '-vcodec', 'rawvideo',
        '-'
    ]

    if get_cmd:
        return command

    pipe = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = pipe.communicate()
    if(err):
        print('error', err)
        return None
    video = np.frombuffer(out, dtype='uint8').reshape((len(frames), frame_size[1], frame_size[0],3))
    return video





def display_images(display_queue):
    while True: 
        data = display_queue.get() 
        if len(data)==0: 
            cv2.destroyAllWindows()
            break
        else:
            ir = data[0]
            cv2.imshow('ir',ir)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break 


def write_images(image_queue, filename_prefix):
    depth_pipe = None
    ir_pipe = None 
    
    while True: 
        data = image_queue.get() 
        if len(data)==0: 
            depth_pipe.stdin.close()
            ir_pipe.stdin.close()
            break
        else:
            ir,depth = data
            depth_pipe = write_frames(filename_prefix+'.depth.avi', depth.astype(np.uint8)[None,:,:], codec='ffv1', close_pipe=False, pipe=depth_pipe)
            ir_pipe = write_frames(filename_prefix+'.ir.avi', ir.astype(np.uint8)[None,:,:], close_pipe=False, crf=14, pipe=ir_pipe)

  

def capture_from_azure(k4a, filename_prefix, recording_length, display_frames=False, display_time=False):
    
    image_queue = Queue()
    write_process = Process(target=write_images, args=(image_queue, filename_prefix))
    write_process.start()
    
    if display_frames: 
        display_queue = Queue()
        display_process = Process(target=display_images, args=(display_queue,))
        display_process.start()
        
    k4a.start()
    system_timestamps = []
    device_timestamps = []
    start_time = time.time()
    count = 0
    
    try:
        while time.time()-start_time < recording_length:  
            capture = k4a.get_capture()
            if capture.depth is None: 
                print('Dropped frame')
                continue
            
            system_timestamps.append(time.time())
            device_timestamps.append(capture.depth_timestamp_usec)

            depth = capture.depth.astype(np.int16)
            ir = capture.ir.astype(np.uint16)

            depth = np.clip((depth-435) * (depth < 690), 0, 255).astype(np.uint8)
            ir = np.clip(ir+100,160,5500)
            ir = ((np.log(ir)-5)*70).astype(np.uint8)

            image_queue.put((ir,depth))
            if display_frames and count % 2 == 0: 
                display_queue.put((ir[::2,::2],))

            if display_time and count % 15 == 0: 
                sys.stdout.write('\rRecorded '+repr(int(time.time()-start_time))+' out of '+repr(recording_length)+' seconds')
            count += 1
            
    except OSError:
        print('Recording stopped early')
        
    finally:
        k4a.stop()
        system_timestamps = np.array(system_timestamps) 
        np.save(filename_prefix+'.system_timestamps.npy',system_timestamps)
        np.save(filename_prefix+'.device_timestamps.npy',device_timestamps)
        print(' - Frame rate = ',len(system_timestamps) / (system_timestamps.max()-system_timestamps.min()))

        image_queue.put(tuple())
        write_process.join()

        if display_frames:
            display_queue.put(tuple())
            display_process.join()
            

def start_recording(filename_prefix, recording_length,top_device_id=0, bottom_device_id=1, display='top'):
    
    k4a_bottom = PyK4A(Config(color_resolution=ColorResolution.RES_720P,
                          depth_mode=DepthMode.NFOV_UNBINNED,
                          synchronized_images_only=False,
                          wired_sync_mode=WiredSyncMode.MASTER), device_id=bottom_device_id)

    k4a_top    = PyK4A(Config(color_resolution=ColorResolution.OFF,
                              depth_mode=DepthMode.NFOV_UNBINNED,
                              synchronized_images_only=False,
                              wired_sync_mode=WiredSyncMode.SUBORDINATE,
                              subordinate_delay_off_master_usec=640), device_id=top_device_id)

    p_top    = Process(target=capture_from_azure,
                       args=(k4a_top, filename_prefix+'.top', recording_length),
                       kwargs={'display_frames': display=='top', 'display_time': display!='top'})

    p_bottom = Process(target=capture_from_azure, 
                       args=(k4a_bottom, filename_prefix+'.bottom' , recording_length),
                       kwargs={'display_frames': display!='top', 'display_time': display=='top'})

    p_top.start()
    p_bottom.start()
    
    
    
    
def save_camera_params(prefix, bottom_device_id=0, top_device_id=1):
    k4a_bottom = PyK4A(Config(color_resolution=ColorResolution.RES_720P,
                              depth_mode=DepthMode.NFOV_UNBINNED,
                              synchronized_images_only=False,
                              wired_sync_mode=WiredSyncMode.MASTER), device_id=bottom_device_id)

    k4a_top    = PyK4A(Config(color_resolution=ColorResolution.OFF,
                              depth_mode=DepthMode.NFOV_UNBINNED,
                              synchronized_images_only=False,
                              wired_sync_mode=WiredSyncMode.SUBORDINATE,
                              subordinate_delay_off_master_usec=640), device_id=top_device_id)


    k4a_top.start()
    k4a_bottom.start()
    time.sleep(1)
    k4a_bottom.save_calibration_json(prefix+'.bottom.json')
    k4a_top.save_calibration_json(prefix+'.top.json')
    k4a_top.stop()
    k4a_bottom.stop()
