import cv2


def display_images(display_queue):
    while True:
        data = display_queue.get()
        if len(data) == 0:
            cv2.destroyAllWindows()
            break
        else:
            ir = data[0]
            cv2.imshow("ir", ir)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
