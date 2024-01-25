import cv2
import time
import threading
import telegram
from loguru import logger
from datetime import datetime


# user modules
from violations import FiveS
from violations.yolov5_detector import Detector
from .camera_storage import CameraStorage

# logger.add("./logs/camera.log")


class Camera:
    def __init__(self, camera_data, telegram_bot,development_telegram_bot,comm_queue): # diatics botu sadece bizim gruba yelek icin bildirim atıyor
        
        self.alert_5S = camera_data["5S"]
        self.alert_yelek = camera_data["Yelek"]
        self.communication_queue = comm_queue
        self.heartbeat = time.time()

        
        self.camera_id = camera_data["CameraId"]
        self.camera_rtsp_url = camera_data["ConnectionStr"]
        self.bot = telegram_bot
        self.development_telegram_bot = development_telegram_bot
        self.specify_main_func(camera_data)

        self.checking_stream_interval = 60  # seconds

        # control variables
        self.yelek_inference_counter = 0
        self.STOP = False
        self.STOP_THREAD = False
        self.last_frame = None
        self.ret = None
        self.fps = 0
        self.last_update_time = 0

        self.frame_lock = threading.Lock()
        self.start_stream()

        self.storage = CameraStorage(self.camera_id)
        self.five_s = FiveS(camera_data["Poly"], self.storage)

    def specify_main_func(self, camera_data):
        if self.alert_yelek:
            self.yelek_detector = Detector(
                telegram_bot=self.development_telegram_bot,
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
        self.fps = 0
        self.last_frame = None
        self.ret = None
        self.stream_thread = threading.Thread(target=self.stream_process, args=())
        self.stream_thread.start()
        logger.debug(f"{self.camera_id} stream is started.")

    def stream_process(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_rtsp_url)
        except Exception as e:
            logger.error("[Camera-{}] Error at creating video capture: {}".format(self.camera_id, e))
        else:
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.bot.send_log(f"{self.camera_id} - Camera is connected - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
            logger.info(f"{self.camera_id} - connection is started - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")

        while not self.STOP_THREAD:
            self.ret, frame = self.cap.read()
            if not self.ret:
                logger.error("[Camera-{}] Stream is not available.".format(self.camera_id))
            if frame is not None:
                with self.frame_lock:
                    self.last_frame = frame.copy()
                    self.last_update_time = time.time()
            else:
                logger.debug("[Camera-{}] Frame is returned as None.", format(self.camera_id))
        logger.debug("[Camera-{}] Target function of stream thread is returned.".format(self.camera_id))
        self.cap.release()

    def getLatestFrame(self):
        temp_frame = None
        if self.last_frame is not None:
            with self.frame_lock:
                temp_frame = self.last_frame.copy()
        else:
            temp_frame = None
        return temp_frame

    def update_storage_frame(self):
        succeed = False
        frame = self.getLatestFrame()
        if frame is not None:
            self.storage.original_live_frame = frame.copy()
            self.storage.original_live_frame = cv2.resize(self.storage.original_live_frame, (1280, 720))
            self.storage.violation_live_frame = self.storage.original_live_frame.copy()
            succeed = True
        else:
            succeed = False
        return succeed, frame

    def check_stream_status(self):
        logger.debug(f"{self.camera_id} - FPS: {self.fps} - Camera Connection: {self.ret} - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")

        self.bot.send_log(
        f"{self.camera_id} - FPS: {self.fps} - Camera Connection: {self.ret} - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
        )

        if self.alert_yelek:
            self.bot.send_log(
            f"{self.camera_id} - Yelek tespiti calisiyor - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
            )

        logger.info("[Camera-{}] Total duration since last frame update : {}".format(self.camera_id, time.time() - self.last_update_time))

        if self.ret == False:
            logger.error("[Camera-{}] Stream is not available.".format(self.camera_id))
            self.STOP_THREAD = True
            time.sleep(3)

            if not self.stream_thread.is_alive():
                for _ in range(50):
                    try:
                        self.stream_thread.join(0.1)
                    except Exception as e:
                        pass
                    else:
                        logger.debug("[Camera-{}] Thread is killed.".format(self.camera_id))
                        break
            self.start_stream()
            logger.debug("[Camera-{}] Stream thread is creating again.".format(self.camera_id))
            time.sleep(3)

        else:
            logger.debug("[Camera-{}] Stream is available.".format(self.camera_id))

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
        while not self.STOP:
            self.heartbeat = time.time()
            try:
                succeed, last_frame = self.update_storage_frame()  # for fiveS
                if succeed:
                    self.main_func(frame=last_frame.copy())

                if time.time() - since > self.checking_stream_interval: # checking interval main.py'daki timeout'dan fazla olmali cünkü sadece burada mesaj güncelleniyor.
                    try:
                        logger.debug("Put heartbeat for: {}".format(self.camera_id))
                        message = {"FROM": f"cam{self.camera_id}", "HB": self.heartbeat}
                        self.communication_queue.put(message, timeout=0.05)
                    except Exception as e:
                        pass

                    self.check_stream_status()
                    since = time.time()

                # if time.time() - since > self.checking_stream_interval:
                #     logger.debug(
                #         "Difference between time and fiveS hearbeat:{}, Difference between time and yelek hearbeat: {}".format(
                #             time.time() - self.five_s.last_heartbeat, time.time() - self.yelek_detector.last_heartbeat
                #         )
                #     )
                #     if max(time.time() - self.five_s.last_heartbeat, time.time() - self.yelek_detector.last_heartbeat) > self.heartbeat_timeout:
                #         logger.error("System has overexceed heartbeat timeout. Run loop is breaking. Warming restarting.")
                #         self.STOP_THREAD = True
                #         break
                #     self.check_stream_status()
                #     since = time.time()
                #     time.sleep(0.5)
            except Exception as e:
                logger.error("Exception at start_camera_processing: {}".format(e))

        logger.debug("Existing from run loop...")
        time.sleep(2)
