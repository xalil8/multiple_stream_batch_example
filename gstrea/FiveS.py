import cv2
import api
import time
import requests
import numpy as np
from loguru import logger
from datetime import datetime

# logger.add("./logs/fives.log")


class FiveS:
    def __init__(self, five_s_polygon, storage) -> None:
        self.storage = storage
        self.violation_type_id = 1
        self.show_on_screen = False

        self.last_heartbeat = None

        self.violation_sleep_threshold = 600  # ihlal bulduktan sonra 10 dakika kontrol etme
        self.violated_object_threshold_time = 120  # 2 dakika boyunca obje hareketsiz kalırsa
        self.violation_control_threshold = 5

        # initialize 1999/09/09 09:09:09 AM GMT timestamp
        # last violation timer for 10 min sleep
        self.last_violation_timer = 936868149
        self.violation_control_timer = 936868149

        # reference update frequency
        self.reference_frame = None
        self.reference_frames = []
        self.reference_update_timer = time.time()
        self.reference_update_frequency = 30  # kaç saniyede bir reference frameler güncellenecek
        self.reference_list_length = 14  # referans fraemim ne kadar uzunlukta

        # Poly
        polygon = np.array(five_s_polygon)
        self.mask = np.zeros((720, 1280, 1), dtype=np.uint8)
        cv2.fillPoly(self.mask, np.int32([polygon]), (255, 255, 255))

        self.violation_tracker = []

    def process_image(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # gray = cv2.GaussianBlur(gray, (21, 21), 0)
        # gray = cv2.bitwise_and(gray, self.mask)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilate = cv2.morphologyEx(gray, cv2.MORPH_DILATE, kernel)

        # get absolute difference between dilate and thresh
        diff = cv2.absdiff(dilate, gray)
        # invert
        edges = 255 - diff
        gray = cv2.GaussianBlur(edges, (21, 21), 0)
        gray = cv2.bitwise_and(gray, self.mask)
        return gray

    def add_padding_to_bounding_box(self, x, y, w, h):
        return x + 10, y + 10, w + 20, h + 20

    def update_reference_frame(self):
        if time.time() - self.reference_update_timer > self.reference_update_frequency:
            self.reference_frames.append(self.storage.original_live_frame)
            if len(self.reference_frames) > self.reference_list_length:
                self.reference_frames.pop(0)
            self.reference_update_timer = time.time()
            self.reference_frame = self.process_image(np.median(self.reference_frames, axis=0).astype(dtype=np.uint8))

            if self.show_on_screen:
                cv2.imshow("ref", self.reference_frame)

    def clean_out_contours(self, contours, hierarchies):
        main_contours = []
        for index, (cont, hierarchy) in enumerate(zip(contours, hierarchies[0])):
            area1 = cv2.contourArea(cont)
            if area1 > 100 and hierarchy[3] < 0:
                x, y, w, h = cv2.boundingRect(cont)
                x1, y1, w1, h1 = self.add_padding_to_bounding_box(x, y, w, h)

                if len(main_contours) == 0:
                    main_contours.append([x, y, w, h, area1])
                else:
                    for index, (x2, y2, w2, h2, area2) in enumerate(main_contours):
                        x2, y2, w2, h2 = self.add_padding_to_bounding_box(x2, y2, w2, h2)

                        # https://www.google.com/search?q=opencv+bounding+box+collision+detection&sxsrf=APq-WBsaU3jN78ORQ9dHf8gIEprx2CRHnw%3A1646813103290&ei=r18oYvSdEcKGxc8P-8CyuAc&oq=opencv+bounding+box+colli&gs_lcp=Cgdnd3Mtd2l6EAMYATIFCCEQoAEyBQghEKABMgUIIRCgATIFCCEQoAE6BwgAEEcQsAM6BAgjECc6BAgAEEM6BQgAEJECOgUIABDLAToFCAAQgAQ6CggAEIAEEIcCEBQ6BggAEBYQHjoHCCEQChCgAUoECEEYAEoECEYYAFCiCVj_YWD2bmgBcAF4AIABrQGIAeQOkgEEMC4xNZgBAKABAcgBCMABAQ&sclient=gws-wiz#kpvalbx=_zV8oYu68MOKGxc8PhKSTkAs16
                        if (x1 + w1) >= (x2) and x1 <= (x2 + w2) and (y1 + h1) >= y2 and y1 <= (y2 + h2):
                            if area1 > area2:
                                main_contours[index] = [x, y, w, h, area1]
                        else:
                            main_contours.append([x, y, w, h, area1])

                # cv2.rectangle(self.storage.violation_live_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
        return main_contours

    def update_violation_tracker(self, cleaned_contours):
        if len(self.violation_tracker) == 0:
            for x1, y1, w1, h1, _ in cleaned_contours:
                self.violation_tracker.append(
                    {
                        "x_middle": x1 + int((w1 / 2)),
                        "y_middle": y1 + int((h1 / 2)),
                        "x": x1,
                        "y": y1,
                        "w": w1,
                        "h": h1,
                        "start_time": time.time(),
                        "update_time": time.time(),
                    }
                )
        else:
            for x1, y1, w1, h1, _ in cleaned_contours:
                x = x1 + int((w1 / 2))
                y = y1 + int((h1 / 2))
                for track in self.violation_tracker:
                    if track["x_middle"] - 3 < x < track["x_middle"] + 3 and track["y_middle"] - 3 < y < track["y_middle"] + 3:
                        track["update_time"] = time.time()
                        break
                else:
                    self.violation_tracker.append(
                        {
                            "x_middle": x1 + int((w1 / 2)),
                            "y_middle": y1 + int((h1 / 2)),
                            "x": x1,
                            "y": y1,
                            "w": w1,
                            "h": h1,
                            "start_time": time.time(),
                            "update_time": time.time(),
                        }
                    )

        self.violation_tracker = [track for track in self.violation_tracker if time.time() - track["update_time"] < 25]

    def convert_back(self, x, y, w, h):
        return int(round(x - (w / 2))), int(round(y - (h / 2))), int(round(x + (w / 2))), int(round(y + (h / 2)))

    def save_original_labeled_data(self, t, violation_date):
        x_min, y_min, x_max, y_max = self.convert_back(float(t["x"]), float(t["y"]), float(t["w"]), float(t["h"]))

        box_center_x = ((x_max - x_min) / 2) + x_min
        box_center_y = ((y_max - y_min) / 2) + y_min

        box_width = x_max - x_min
        box_height = y_max - y_min

        boinding_box = (box_center_x, box_center_y, box_width, box_height)
        box_list = boinding_box / np.array(
            [
                self.storage.original_live_frame.shape[1],
                self.storage.original_live_frame.shape[0],
                self.storage.original_live_frame.shape[1],
                self.storage.original_live_frame.shape[0],
            ]
        )

        object_yolo_txt = f"""{0} {" ".join([f"{float(i):.6f}" for i in box_list])}"""
        txt_path = "/home/dia/Desktop/divisor-5s/divisor-SASA-ai-engine/app/violations/violation_images_with_tag"
        with open(f"{txt_path}/violation_{self.storage.camera_id}_{violation_date}.txt", "a") as f:
            f.write(object_yolo_txt)
        cv2.imwrite(f"""{txt_path}/violation_{self.storage.camera_id}_{violation_date}.png""", self.storage.original_live_frame)

    def main(self, show_on_screen):
            
        # logger.info("[Camera-{}] FiveS main was called.".format(self.storage.camera_id))
        self.show_on_screen = show_on_screen
        self.update_reference_frame()

        self.last_heartbeat = time.time()
        # frames > 10 olacak
        if (
            len(self.reference_frames) > 10
            and time.time() - self.last_violation_timer > self.violation_sleep_threshold
            and time.time() - self.violation_control_timer > self.violation_control_threshold
        ):
            self.violation_control_timer = time.time()

            frame_delta = cv2.absdiff(self.reference_frame, self.process_image(self.storage.original_live_frame))
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            # dilate the threshold applied image to fill in holes, then find contours
            # on threshold applied image
            thresh = cv2.dilate(thresh, None, iterations=2)

            contours, hierarchies = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if show_on_screen:
                cv2.imshow(f"Mask", thresh)

            if len(contours) != 0:
                cleaned_contours = self.clean_out_contours(contours=contours, hierarchies=hierarchies)

                # burası kapanacak # sorulacak
                # for x, y, w, h, _ in cleaned_contours:
                #     cv2.rectangle(self.storage.violation_live_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                #     # cv2.rectangle(self.storage.violation_live_frame, (x - 10, y - 10),
                #     # (x - 10 + w + 20, y - 10 + h + 20), (255, 0, 0), 5)
            else:
                cleaned_contours = []

            self.update_violation_tracker(cleaned_contours)

            for t in self.violation_tracker:
                # cv2.rectangle(self.storage.violation_live_frame, (t["x"] - 5, t["y"] - 5),
                #               (t["x"] + t["w"] + 5, t["y"] + t["h"] + 5), (255, 0, 0), 2)
                if time.time() - t["start_time"] > self.violated_object_threshold_time:
                    print("VİOLATİON :)")
                    cv2.putText(
                        self.storage.violation_live_frame,
                        "5S IHLALI",
                        (50, 100),
                        self.storage.font,
                        self.storage.font_scale,
                        self.storage.violation_font_color,
                        self.storage.violation_font_ticknes,
                        self.storage.violation_line_type,
                    )
                    cv2.rectangle(self.storage.violation_live_frame, (t["x"] - 10, t["y"] - 10), (t["x"] + t["w"] + 10, t["y"] + t["h"] + 10), (0, 0, 255), 2)

                    cv2.putText(
                        self.storage.violation_live_frame,
                        f'{t["h"]}',
                        (t["x"] + t["w"] + 5, t["y"] + int(t["h"] / 2)),
                        self.storage.font,
                        0.6,
                        (255, 0, 255),
                        1,
                        self.storage.violation_line_type,
                    )
                    cv2.putText(
                        self.storage.violation_live_frame,
                        f'{t["w"]}',
                        (t["x"] + int(t["w"] / 2), t["y"] - 5),
                        self.storage.font,
                        0.6,
                        (255, 0, 255),
                        1,
                        self.storage.violation_line_type,
                    )

                    violation_date = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
                    self.last_violation_timer = time.time()
                    self.violation_tracker.clear()
                    self.save_original_labeled_data(t, violation_date)

                    violation_image_path = f"""{self.storage.violation_save_path}/violation_{self.storage.camera_id}_{violation_date}.png"""
                    cv2.imwrite(violation_image_path, self.storage.violation_live_frame)

                    api.create_violation(self.storage.camera_id, self.violation_type_id, violation_image_path)
                    logger.info(f"5S Violaton Sent, camera_id: {self.storage.camera_id}, date: {datetime.now()}")
                    # logger.info("[Camera-{}] Fives main method was returned with true.".format(self.storage.camera_id))
                    return True

        # logger.info("[Camera-{}] Fives main method was returned with false.".format(self.storage.camera_id))
        return False
