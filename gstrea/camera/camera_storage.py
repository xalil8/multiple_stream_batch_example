import cv2


class CameraStorage:
    def __init__(self, camera_id):
        self.camera_id = camera_id
        # untouched frame
        self.original_live_frame = None

        # violations drawn frame
        self.violation_live_frame = None

        # font
        self.font = cv2.FONT_HERSHEY_SIMPLEX

        self.font_scale = 1

        self.violation_font_color = (0, 0, 255)

        self.violation_font_ticknes = 2

        self.violation_line_type = cv2.LINE_AA

        self.violation_save_path = "/home/dia/Desktop/divisor-5s/divisor-SASA-ai-engine/app/violations/violation_images"