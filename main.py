import time
import signal
from loguru import logger
import multiprocessing as mp
from streamer import Streamer

STOP = False
/home/dia/Desktop/divisor-5s/divisor-SASA-ai-engine_updated_v2/divisor-SASA-ai-engine_updated/camera/camera_gstreamer.py
logger.add("./logs/stream.log")


def test_camera_connection(rtsp_adress, camera_name):
    logger.info(f"{camera_name} process is started.")
    stream = Streamer(address=rtsp_adress)
    stream.startStream()
    logger.info(f"{camera_name} stream is started.")

    checked_time = None
    since = time.time()
    while not STOP:
        if time.time() - checked_time > 10:
            logger.error(f"{camera_name} stream is not available during 10 seconds.")
        if stream.isNewFrameAvailable():
            frame = stream.getLatestFrame()
            if frame is None:
                logger.error(f"{camera_name} frame is returned as None.")
            else:
                checked_time = time.time()
        else:
            time.sleep(0.001)

    stream.stopStream()


def signal_handler(a, b):
    global STOP

    logger.debug("SIGINT RECEIVED.")
    STOP = True


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    camera1_process = mp.Process(
        target=test_camera_connection,
        args=(
            "rtsp://admin:Welc0me12@192.168.1.5:554/Streaming/Channels/1/",
            "camera1",
        ),
    )

    camera2_process = mp.Process(
        target=test_camera_connection,
        args=(
            "rtsp://admin:Welc0me12@192.168.1.15:554/Streaming/Channels/1/",
            "camera2",
        ),
    )

    camera3_process = mp.Process(
        target=test_camera_connection,
        args=(
            "rtsp://admin:Welc0me12@192.168.1.23:554/Streaming/Channels/1/",
            "camera3",
        ),
    )

    camera4_process = mp.Process(
        target=test_camera_connection,
        args=(
            "rtsp://admin:Welc0me12@192.168.1.6:554/Streaming/Channels/1/",
            "camera4",
        ),
    )

    camera1_process.start()
    # camera2_process.start()
    # camera3_process.start()
    # camera4_process.start()

    while not STOP:
        time.sleep(0.1)

    time.sleep(5)
