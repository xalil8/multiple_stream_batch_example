import cv2
import time
from loguru import logger
from datetime import datetime

# user modules
from camera.get_rtsp_stream import Streamer
from violations import FiveS
from violations.yolov5_detector import Detector
from .camera_storage import CameraStorage

logger.add("./logs/camera.log")


class Camera:
    def __init__(self, camera_data, telegram_bot):
        self.alert_5S = camera_data["5S"]
        self.alert_yelek = camera_data["Yelek"]
        self.specify_main_func(camera_data)

        self.camera_id = camera_data["CameraId"]
        self.camera_rtsp_url = camera_data["ConnectionStr"]
        self.bot = telegram_bot

        self.checking_stream_interval = 120  # seconds
        self.heartbeat_timeout = 60  # seconds

        # control variables
        self.yelek_inference_counter = 0
        self.STOP = True
        self.fps = 0
        self.last_update_time = 0

        self.start_stream()

        self.storage = CameraStorage(self.camera_id)
        self.five_s = FiveS(camera_data["Poly"], self.storage)

    def specify_main_func(self, camera_data):
        if self.alert_yelek:
            self.yelek_detector = Detector(
                telegram_bot=self.bot,
                camera_name=self.camera_id,
                contour_threshold=camera_data["contour_threshold"],
                model_path="./object_detection_weight/v4.pt",
                model_confidence=0.75,
            )
            if self.alert_5S:
                self.main_func = self.main_for_5s_and_yelek
            else:
                self.main_func = self.main_for_yelek
        elif self.alert_5S:
            self.main_func = self.main_for_5s

    def start_stream(self):
        self.stream = Streamer(address=self.camera_rtsp_url)
        self.stream.startStream()
        # self.bot.send_log(f"{self.camera_id} - Camera is connected - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
        logger.info(f"{self.camera_id} - connection is started - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
        self.fps = 0

    def update_storage_frame(self):
        succeed = False
        if self.stream.isNewFrameAvailable():
            frame = self.stream.getLatestFrame()
            self.last_update_time = time.time()
            if frame is not None:
                self.storage.original_live_frame = frame.copy()
                self.storage.original_live_frame = cv2.resize(self.storage.original_live_frame, (1280, 720))
                self.storage.violation_live_frame = self.storage.original_live_frame.copy()
                succeed = True
            else:
                succeed = False
        return succeed, frame

    def check_stream_status(self):
        logger.info("[Camera-{}] Total duration since last frame update : {}".format(self.camera_id, time.time() - self.last_update_time))

        if self.stream.lastBufferReceivedTime() < 1:
            logger.debug(f"{self.camera_id} - FPS: {self.fps} - Camera Connection: True - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")

            # self.bot.send_log(
            # f"{self.camera_id} - FPS: {self.fps} - Camera Connection: True - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
            # )

            if self.alert_yelek:
                pass
                # self.bot.send_log(
                # f"{self.camera_id} - Yelek tespiti calisiyor - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
                # )

        else:
            logger.debug(f"[{self.camera_id}] CAMERA NOT ACTIVE! RESTARTING STREAM PIPELINE!")
            # self.bot.send_log(
            # f"{self.camera_id} - FPS: {self.fps} - Camera Connection: False - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
            # )
            if self.alert_yelek:
                pass
                # self.bot.send_log(
                # f"{self.camera_id} - Yelek tespiti calismiyor - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
                # )

            self.stream.stopStream()
            self.stream.startStream()
            time.sleep(1)

    def main_for_5s(self, frame, show_on_screen=False):
        self.five_s.main(show_on_screen=show_on_screen)

    def main_for_yelek(self, frame, show_on_screen=False):
        if self.yelek_inference_counter % 20 == 0:
            self.yelek_detector.inference(frame)
        self.yelek_inference_counter += 1

    def main_for_5s_and_yelek(self, frame, show_on_screen=False):
        self.five_s.main(show_on_screen=show_on_screen)
        if self.yelek_inference_counter % 20 == 0:
            self.yelek_detector.inference(frame)
        self.yelek_inference_counter += 1

    def run(self):
        since = time.time()
        t1 = time.time()
        while not self.STOP:
            try:
                self.fps = 1 / (time.time() - t1)
                succeed, last_frame = self.update_storage_frame()  # for fiveS
                if succeed:
                    self.main_func(frame=last_frame.copy())

                if time.time() - since > self.checking_stream_interval:
                    logger.debug(
                        "Difference between time and fiveS hearbeat:{}, Difference between time and yelek hearbeat: {}".format(
                            time.time() - self.five_s.last_heartbeat, time.time() - self.yelek_detector.last_heartbeat
                        )
                    )
                    if max(time.time() - self.five_s.last_heartbeat, time.time() - self.yelek_detector.last_heartbeat) > self.heartbeat_timeout:
                        logger.error("System has overexceed heartbeat timeout. Run loop is breaking. Warming restarting.")
                        self.stream.stopStream()
                        break
                    self.check_stream_status()
                    since = time.time()
                    time.sleep(0.5)
                t1 = time.time()
            except Exception as e:
                logger.error("Exception at start_camera_processing: {}".format(e))

        logger.debug("Existing from run loop...")
        time.sleep(3)
