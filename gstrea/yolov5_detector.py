import os
import cv2
import time
import torch
import telegram
import numpy as np
from loguru import logger
from datetime import datetime

# {0: "anomaly", 1: "mavi", 2: "person", 3: "sari"}

# logger.add("./logs/yelek.log")


class Detector:
    def __init__(self, telegram_bot, camera_name, contour_threshold, model_path, model_confidence=0.75):
        self.camera_name = camera_name
        self.contour_threshold = contour_threshold
        self.bot = telegram_bot
        self.detection_log_path = "./logs/yelek_detections"
        
        self.bot.send_message(chat_id="-1001875614534",text=f"[camera_{self.camera_name}] yelek detection is started. - {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")

        # TO GATHER DATA FOR DETECTION DEVELOPMENT
        self.data_save_counter = 0
        self.data_save_interval = 60

        # control variables
        self.last_photo_sent_time = 0
        self.total_send_photo_interval = 60  # seconds
        self.last_heartbeat = time.time()

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = torch.hub.load("ultralytics/yolov5", "custom", path=model_path, force_reload=False, device=device)
        self.model.conf = model_confidence
        self.lower_yellow = np.array([0, 0, 130])
        self.upper_yellow = np.array([166, 255, 255])

    def draw_contour(self, frame, coordinates):
        """
        Apply yellow color filters to detected person then find biggest yellow countour and its area

        Args:
            frame: The video frame to draw contours on.
            coordinates: The coordinates of the detected object.
        Returns:
            tuple: A tuple containing the frame with contours and the contour area.
        """
        x1, y1, x2, y2 = coordinates
        roi = frame[y1:y2, x1:x2].copy()
        # resize roi to fixed size (200,150)
        yellow_mask = cv2.inRange(roi, self.lower_yellow, self.upper_yellow)
        contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            yellow_mask = cv2.cvtColor(yellow_mask, cv2.COLOR_GRAY2BGR)
            cv2.drawContours(yellow_mask, [largest_contour], -1, (0, 0, 255), thickness=2)
            # contour_with_red_line = cv2.drawContours(roi, [largest_contour], -1, (255, 0, 255), thickness=2)
            contour_area = cv2.contourArea(largest_contour)
            return yellow_mask, contour_area
        else:
            return None, None

    def inference(self, frame):
        """
        Perform object detection on a video frame and send notifications if necessary.

        Args:
            frame: The video frame to perform object detection on.
        """
        self.last_heartbeat = time.time()
        # logger.info("[Camera-{}] Yolov5 detector inference method was called.".format(self.camera_name))
        frame = cv2.resize(frame, (1920, 1080))
        results = self.model(frame.copy())
        det = results.xyxy[0]

        for j, (output) in enumerate(det):
            id = int(output[5])
            self.conf = round(float(output[4]), 2)
            
            # TO GATHER MORE DATA FOR DEVELOPMENT 
            self.data_save_counter += 1
            if self.data_save_counter % self.data_save_interval == 0:
                unique_yolov5_detection_log_id = int(len(os.listdir("./logs/yelek_yolov5_detections"))) + 1
                try:
                    cv2.imwrite(f"./logs/yelek_yolov5_detections/{str(unique_yolov5_detection_log_id)}_id{str(id)}.jpg",frame)
                except Exception as e:
                    pass


            if id == 3 or id == 0:
                x1, y1, x2, y2 = map(int, output[:4])
                coordinates = x1, y1, x2, y2
                self.filtered_image, self.contour_area = self.draw_contour(frame, coordinates)
                if self.contour_area is not None:
                    if self.contour_area < self.contour_threshold:
                        logger.info(f"{self.camera_name} contour size {self.contour_area}")
                    else:
                        self.send_notification(frame, coordinates)

        # logger.info("[Camera-{}] Yolov5 detector inference method was returned.".format(self.camera_name))

    def send_notification(self, frame, coordinates):
        """
        Send a notification with the detected object information.

        Args:
            frame: The video frame containing the object.
            coordinates: The coordinates of the detected object.

        """

        if time.time() - self.last_photo_sent_time > self.total_send_photo_interval:  # 60 seconds
            x1, y1, x2, y2 = coordinates
            center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.circle(frame, (center_x, center_y), radius=3, color=(0, 255, 255), thickness=-1)
            cv2.putText(frame, f"Yabanci  {self.conf}", (x1 + 10, y1 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            resized = cv2.resize(frame, (1280, 720))
            unique_image_id = int(len(os.listdir(self.detection_log_path))) // 2 + 1
            cv2.imwrite(f"{self.detection_log_path}/camera_{self.camera_name}_{str(unique_image_id)}_image.jpg", resized)
            cv2.imwrite(f"{self.detection_log_path}/camera_{self.camera_name}_{str(unique_image_id)}_contour.jpg", self.filtered_image)
            logger.info("[Camera-{}] SARI YELEK FOUND.".format(self.camera_name))

            self.bot.send_photo(chat_id="-1001875614534",photo=open(f"{self.detection_log_path}/camera_{self.camera_name}_{str(unique_image_id)}_image.jpg", "rb"),caption=f"contour area {self.contour_area}")
            # self.bot.send_photo(chat_id="-1001947655350", photo=open(f"{self.camera_name}_contour.jpg", "rb"), caption=f"contour area {self.contour_area}")
            # self.bot.send_photo(
            #     chat_id="-1001947655350",
            #     photo=open(f"{self.detection_log_path}/camera_{self.camera_name}_{str(unique_image_id)}_image.jpg", "rb"),
            #     caption=f"{self.camera_name } SAHADA MUTEAHHIT PERSONAL TESPIT EDILDI",
            # )
            self.last_photo_sent_time = time.time()  # Update the last photo sent time
