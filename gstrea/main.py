import time
import telegram
import threading
from loguru import logger
import multiprocessing as mp
from camera.camera import Camera
from camera_data import cameras_data

from notification import TelegramBot

logger.add("./logs/main.log")

STOP = False


def CAMERA_PROCESS(camera_data, comm_queue):

    yelek_development_bot = telegram.Bot(token="6670171232:AAFMTfDvzrpJ47Djq3rBtCpK59L2gMdGLy4") # sadece yelek ile ilgili resimleri göndermek icin var
    bot = TelegramBot(token="6305744379:AAFrF6iaBp5kM2KA-wCfo5d73uvPu4b_te8", chat_id="-1001921770942")
    camera = Camera(camera_data=camera_data, telegram_bot=bot, development_telegram_bot=yelek_development_bot, comm_queue=comm_queue)
    time.sleep(2)
    camera.run()


def signal_handler(a, b):
    global STOP

    STOP = True
    print("SIGINT!")


class Process_Controller:
    def __init__(self):
        self.STOP = False
        self.processes_dict = {}
        self.process_heartbeats = {"cam1": time.time(), "cam2": time.time(),"cam3":time.time(),"cam4":time.time()} # bunu basta initialize ettigim icin ilk seferde heartbeat kuyruktan gelmese de buradan geliyor
        self.main_queue = mp.Queue(maxsize=20)
        self.start_processes()

        self.MESSAGE_LOCK = threading.Lock()
        self.STOP_LISTENER_THREAD = False
        self.checking_interval = 120  # second
        self.HEARTBEAT_TIMEOUT = 180  # second

    def start(self):
        self.control_thread = threading.Thread(target=self.main)
        self.control_thread.start()
        self.message_listener_thread = threading.Thread(target=self.listen)
        self.message_listener_thread.start()
        logger.debug("Listener and controller thread in main are started.")
        time.sleep(0.1)

    def start_processes(self):
        cam1_process = mp.Process(name="1", target=CAMERA_PROCESS, args=(cameras_data["1"][0], self.main_queue))
        cam2_process = mp.Process(name="2", target=CAMERA_PROCESS, args=(cameras_data["1"][1], self.main_queue))
        cam3_process = mp.Process(name="3", target=CAMERA_PROCESS, args=(cameras_data["1"][2], self.main_queue))
        cam4_process = mp.Process(name="4", target=CAMERA_PROCESS, args=(cameras_data["1"][3], self.main_queue))
        self.processes_dict = {"cam1": cam1_process, "cam2": cam2_process,"cam3":cam3_process,"cam4":cam4_process}
        cam1_process.start()
        cam2_process.start()
        cam3_process.start()
        cam4_process.start()
        time.sleep(2)
        logger.debug("All Processes are started.")

    def listen(self):
        while not self.STOP_LISTENER_THREAD:
            try:
                message = self.main_queue.get(timeout=0.1)
            except Exception as e:
                pass
            else:
                with self.MESSAGE_LOCK:
                    self.process_heartbeats[message["FROM"]] = message["HB"]

    def main(self):
        since = time.time()
        while not self.STOP:
            if time.time() - since > self.checking_interval:
                since = time.time()
                with self.MESSAGE_LOCK:
                    for cam_name in self.process_heartbeats:
                        logger.debug(
                            f"{cam_name} last heartbeat time: {self.process_heartbeats[cam_name]} and difference: {time.time() - self.process_heartbeats[cam_name]}"
                        )
                        if time.time() - self.process_heartbeats[cam_name] > self.HEARTBEAT_TIMEOUT:
                            self.stop_process(cam_name)
                            self.restart_process(cam_name)
                            time.sleep(2)

    def stop_process(self, cam_name):
        logger.error(f"Trying to stop {cam_name} process.")
        self.processes_dict[cam_name].terminate()
        # self.process_dict[cam_name].kill() # python3.7 and later
        time.sleep(2)

        for _ in range(50):
            if not (self.processes_dict[cam_name].is_alive()):
                try:
                    self.processes_dict[cam_name].join(0.05)
                except Exception as e:
                    pass
                else:
                    logger.debug(f"{cam_name} process is stopped successfuly.")
                    del self.processes_dict[cam_name]
                    break

    def restart_process(self, cam_name):
        logger.debug(f"Restarting {cam_name} process.")
        if cam_name == "cam1":
            cam1_process = mp.Process(name="1", target=CAMERA_PROCESS, args=(cameras_data["1"][0], self.main_queue))
            cam1_process.start()
            self.processes_dict[cam_name] = cam1_process
            self.process_heartbeats[cam_name] = time.time()

        elif cam_name == "cam2":
            cam2_process = mp.Process(name="2", target=CAMERA_PROCESS, args=(cameras_data["1"][1], self.main_queue))
            cam2_process.start()
            self.processes_dict[cam_name] = cam2_process
            self.process_heartbeats[cam_name] = time.time()


        elif cam_name == "cam3":
            cam3_process = mp.Process(name="3", target=CAMERA_PROCESS, args=(cameras_data["1"][2], self.main_queue))
            cam3_process.start()
            self.processes_dict[cam_name] = cam3_process
            self.process_heartbeats[cam_name] = time.time()

        
        elif cam_name == "cam4":
            cam4_process = mp.Process(name="4", target=CAMERA_PROCESS, args=(cameras_data["1"][3], self.main_queue))
            cam4_process.start()
            self.processes_dict[cam_name] = cam4_process
            self.process_heartbeats[cam_name] = time.time()


if __name__ == "__main__":
    process_controller = Process_Controller()
    process_controller.start()

    while not STOP:
        time.sleep(0.5)

    process_controller.STOP = True


# if __name__ == "__main__":
#     comm_queue1 = mp.Queue(maxsize=10)
#     cam1_process = mp.Process(name="1", target=CAMERA_PROCESS, args=(cameras_data["1"][0], comm_queue1))

#     comm_queue2 = mp.Queue(maxsize=10)
#     cam2_process = mp.Process(name="2", target=CAMERA_PROCESS, args=(cameras_data["1"][1], comm_queue2))

#     processes_list = [cam1_process, cam2_process]
#     cam1_process.start()
#     cam2_process.start()
#     logger.debug("Processes are started.")
#     time.sleep(2)

#     check_interval = time.time()
#     while not STOP:
#         if time.time() - check_interval > 60:
#             deleted_process_names = []
#             for index, process in enumerate(processes_list):
#                 if not process.is_alive():
#                     logger.debug("{} process is not alive.".format(str(index)))
#                     deleted_process_names.append(process.name)

#                     for _ in range(50):
#                         try:
#                             process.join(0.1)
#                         except Exception as e:
#                             pass
#                         else:
#                             logger.debug("Process is joined.")
#                             del processes_list[index]
#                             break

#             for process_name in deleted_process_names:
#                 logger.debug("New process is started for {}. camera".format(process_name))
#                 logger.debug("Used {} adress for new process".format(cameras_data["1"][int(process_name) - 1]))
#                 processes_list.append(mp.Process(name=process_name, target=CAMERA_PROCESS, args=(cameras_data["1"][int(process_name) - 1])).start())
#                 time.sleep(3)
