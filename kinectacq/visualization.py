import cv2
import matplotlib
import numpy as np

def display_images(display_queue, display_fcn, depth = False):
    try:
        while True:
            data = display_queue.get()
            if len(data) == 0:
                cv2.destroyAllWindows()
                break
            else:
                
                ir = data[0]
                ir = display_fcn(ir)
                ir = cv2.normalize(ir, None, 255,0, cv2.NORM_MINMAX, cv2.CV_8UC1)
                if depth:
                    ir = matplotlib.cm.turbo(ir)
                cv2.imshow("ir", ir)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        
        
        

