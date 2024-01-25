"""
H265 yapmak için sadece 80 ve 81. satirlari degistir
"""


#!/usr/bin/env python3
import sys
import gi
from loguru import logger
import numpy as np
import cv2
import threading
import time

# from debugger_imshow import Imshow


gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gst, GLib, GObject

# Initialize GStreamer
Gst.init(sys.argv[1:])


class Streamer:
    def __init__(self, address, debug=False):
        self.__rtspAddress = address
        self.__DEBUG = debug

        self.__objectName = "object_" + str(address)
        self.__LOGPREFIX = "[STREAMER_" + self.__objectName + "] "

        # Elements
        self.__source = None
        self.__jitter = None
        self.__depay = None
        self.__parse = None
        self.__decoder = None
        self.__convert1 = None
        self.__convert2 = None
        self.__capsfilter1 = None
        self.__sink = None

        self.__pipeline = None

        # self.__LOOP = GLib.MainLoop()
        self.__LOOP = GObject.MainLoop.new(None, False)

        self.__LOCK = threading.Lock()
        self.__mainLoopThread = None

        self.__isStarted = False

        self.__newImageAvailable = False
        self.__IMAGE = None
        self.__ERROR_OCCURED = False

        self.__createElements()
        self.__connectSignals()
        self.__addElementsIntoPipeline()
        self.__prepareCapsFilters()
        self.__setPropsOfElements()
        self.__linkElements()

        self.__BUS = self.__pipeline.get_bus()
        self.__BUS.add_signal_watch()
        self.__BUS.connect("message", self.__busMessages)

        self.__EOSRECEIVED = False
        self.__PIPELINE_STATE = None
        self.__LAST_BUFFER_RECEIVED_TIME = time.time()

    def __createElements(self):
        # Create the elements
        self.__source = Gst.ElementFactory.make("rtspsrc", "source")
        self.__jitter = Gst.ElementFactory.make("rtpjitterbuffer", "jitter")
        self.__depay = Gst.ElementFactory.make("rtph264depay", "rtpdepay")
        self.__parse = Gst.ElementFactory.make("h264parse", "parse")
        self.__decoder = Gst.ElementFactory.make("nvv4l2decoder", "decoder")
        self.__convert1 = Gst.ElementFactory.make("nvvideoconvert", "convert1")
        self.__convert2 = Gst.ElementFactory.make("videoconvert", "convert2")
        self.__capsfilter1 = Gst.ElementFactory.make("capsfilter", "filter1")
        self.__sink = Gst.ElementFactory.make("appsink", "sink")

        # Create the empty pipeline
        self.__pipeline = Gst.Pipeline.new("streamer-pipeline")

        if (
            not self.__pipeline
            or not self.__source
            or not self.__jitter
            or not self.__depay
            or not self.__parse
            or not self.__decoder
            or not self.__convert1
            or not self.__convert2
            or not self.__capsfilter1
            or not self.__sink
        ):
            logger.error(self.__LOGPREFIX + "Not all elements could be created.")
            # sys.exit(1)

    def __connectSignals(self):
        # Connect signals
        self.__source.connect("pad-added", self.__padAddedToRtsp)
        self.__source.connect("pad-removed", self.__padRemovedFromRtsp)
        self.__sink.connect("new-sample", self.__appsinkConvertBuffer)

    def __addElementsIntoPipeline(self):
        # Build the pipeline
        self.__pipeline.add(self.__source)
        self.__pipeline.add(self.__jitter)
        self.__pipeline.add(self.__depay)
        self.__pipeline.add(self.__parse)
        self.__pipeline.add(self.__decoder)
        self.__pipeline.add(self.__convert1)
        self.__pipeline.add(self.__convert2)
        self.__pipeline.add(self.__capsfilter1)
        self.__pipeline.add(self.__sink)

    def __linkElements(self):
        # Link elements that do not require pad added
        if (
            not self.__jitter.link(self.__depay)
            or not self.__depay.link(self.__parse)
            or not self.__parse.link(self.__decoder)
            or not self.__decoder.link(self.__convert1)
            or not self.__convert1.link(self.__convert2)
            or not self.__convert2.link(self.__capsfilter1)
            or not self.__capsfilter1.link(self.__sink)
        ):
            logger.error(self.__LOGPREFIX + "Elements could not be linked.")
            sys.exit(1)

    def __setPropsOfElements(self):
        # Set Props of elements
        self.__source.set_property("location", self.__rtspAddress)
        # self.__source.set_property('latency', 200)
        # self.__source.set_property('drop-on-latency', True)
        # self.__source.set_property('buffer-mode', 4)
        # self.__jitter.set_property('latency', 200)
        # self.__jitter.set_property('drop-on-latency', True)
        # self.__jitter.set_property('mode', 4)

        # self.__source.set_property('protocols', 0x00000001)
        # self.__source.set_property('buffer-mode', 4)

        # self.__decoder.set_property('low-latency-mode', True)
        self.__sink.set_property("emit-signals", True)
        # self.__depay.set_property('mtu', 60000)

    def __prepareCapsFilters(self):
        # Capfilters' caps
        cap_capsfilter1 = Gst.Caps.from_string("video/x-raw,format=BGR")
        self.__capsfilter1.set_property("caps", cap_capsfilter1)

    def __padAddedToRtsp(self, rtspsrc, pad):
        sinkpad = self.__jitter.get_static_pad("sink")
        try:
            pad.link(sinkpad)
        except Exception as msg:
            logger.error(self.__LOGPREFIX + "Pad link failed in padAddedToRtsp()")

    def __padRemovedFromRtsp(self, rtspsrc, pad):
        sinkpad = self.__jitter.get_static_pad("sink")
        pad.unlink(sinkpad)

    def __appsinkConvertBuffer(self, appsink):
        sample = appsink.emit("pull-sample")  # Gst.Sample

        buffer = sample.get_buffer()  # Gst.Buffer

        caps_format = sample.get_caps().get_structure(0)  # Gst.Structure

        # GstVideo.VideoFormat
        frmt_str = caps_format.get_value("format")
        h = caps_format.get_value("height")
        w = caps_format.get_value("width")
        c = 3
        with self.__LOCK:
            self.__IMAGE = np.ndarray(shape=(h, w, c), buffer=buffer.extract_dup(0, buffer.get_size()), dtype=np.uint8)

            self.__newImageAvailable = True
            self.__LAST_BUFFER_RECEIVED_TIME = time.time()

        return Gst.FlowReturn.OK

    def __busMessages(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            logger.info(self.__LOGPREFIX + "EOS Received")
            self.__EOSRECEIVED = True

        elif t == Gst.MessageType.WARNING:
            pass

        elif t == Gst.MessageType.ERROR:
            err, debug_info = message.parse_error()
            logger.error(self.__LOGPREFIX + f"Error received from element {message.src.get_name()}: {err.message}")
            logger.error(self.__LOGPREFIX + f"Debugging information: {debug_info if debug_info else 'none'}")

            with self.__LOCK:
                self.__ERROR_OCCURED = True

        elif message.type == Gst.MessageType.STATE_CHANGED:
            if isinstance(message.src, Gst.Pipeline):
                old_state, new_state, pending_state = message.parse_state_changed()
                with self.__LOCK:
                    self.__PIPELINE_STATE = new_state.value_nick
                logger.info(self.__LOGPREFIX + f"Pipeline state changed from {old_state.value_nick} to {new_state.value_nick}.")
                # print(str(message.type))
                pass
        else:
            pass

        return True

    def __checkPipelineState(self, state, second=3):
        for _ in range(second * 10):
            temp_state = None
            with self.__LOCK:
                temp_state = self.__PIPELINE_STATE

            if temp_state == state:
                if self.__DEBUG:
                    logger.debug(self.__LOGPREFIX + f"{state} state!")
                break
            time.sleep(0.1)

    def __nullPipeline(self):
        self.__pipeline.set_state(Gst.State.NULL)

    def __pausePipeline(self):
        self.__pipeline.set_state(Gst.State.PAUSED)

    def __playPipeline(self):
        self.__pipeline.set_state(Gst.State.PLAYING)

    def __readyPipeline(self):
        self.__pipeline.set_state(Gst.State.READY)

    def __runStream(self):
        self.__isStarted = True
        with self.__LOCK:
            logger.warning(self.__LOGPREFIX + "Stream Started!")
        try:
            self.__LOOP.run()
        except KeyboardInterrupt:
            self.stopStream()

    def startStream(self):
        if not self.__isStarted:
            with self.__LOCK:
                self.__ERROR_OCCURED = False
            self.__mainLoopThread = threading.Thread(target=self.__runStream, daemon=True)
            self.__mainLoopThread.start()

            self.__playPipeline()
            self.__checkPipelineState("playing", second=5)

        else:
            logger.warning(self.__LOGPREFIX + "Stream Already Started!")

    def stopStream(self):
        if self.__isStarted:
            logger.warning(self.__LOGPREFIX + "Stopping Stream...")

            self.__nullPipeline()
            self.__checkPipelineState("ready")
            self.__LOOP.quit()

            for _ in range(10):
                if not self.__mainLoopThread.is_alive():
                    try:
                        self.__mainLoopThread.join(0.1)
                    except Exception as msg:
                        if self.__DEBUG:
                            print("join() failed: " + str(msg))
                    break
                else:
                    time.sleep(0.1)

            self.__isStarted = False

            logger.warning(self.__LOGPREFIX + "Stream Stopped!")

        else:
            logger.warning(self.__LOGPREFIX + "Stream Already Stopped!")

    def sendEOS(self):
        self.__depay.send_event(Gst.Event.new_eos())

        for _ in range(10):
            if self.__EOSRECEIVED:
                break
            time.sleep(0.1)

        self.__EOSRECEIVED = False

    def isNewFrameAvailable(self):
        tempBool = None
        with self.__LOCK:
            tempBool = self.__newImageAvailable

        if tempBool:
            return True
        else:
            return False

    def getLatestFrame(self):
        tempImage = None
        with self.__LOCK:
            self.__newImageAvailable = False
            tempImage = self.__IMAGE.copy()

        return tempImage

    def lastBufferReceivedTime(self):
        tempTime = None

        with self.__LOCK:
            tempTime = self.__LAST_BUFFER_RECEIVED_TIME

        return time.time() - tempTime

    def isErrorOccured(self):
        tempErr = None

        with self.__LOCK:
            tempErr = self.__ERROR_OCCURED

        return tempErr


# if __name__ == "__main__":
#     import signal

#     STOP = False

#     def signal_handler(a, b):
#         global STOP

#         STOP = True
#         # print("SIGINT!")

#     signal.signal(signal.SIGINT, signal_handler)

#     # imshow = Imshow(windowName="aaa")
#     # imshow.startImshow()

#     stream1 = Streamer(address="rtsp://admin:teknotam2015@192.168.1.64")
#     stream1.startStream()
#     # frame = cv2.imread("./roi/sample_frame_d1.jpg")
#     # cv2.namedWindow("frame", cv2.WINDOW_NORMAL)

#     t1 = time.time()
#     while not STOP:
#         if stream1.isNewFrameAvailable():
#             print(1 / (time.time() - t1))
#             frame = stream1.getLatestFrame()
#             t1 = time.time()
#             # imshow.putFrame(frame=frame)

#         else:
#             time.sleep(0.001)

#     # imshow.stopImshow()
#     stream1.stopStream()
