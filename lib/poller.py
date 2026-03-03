# Polling and threading logic for DWD forecast
import threading
import time
import logging

class PollerThread(threading.Thread):
    def __init__(self, queue, poll_func, interval=60):
        super().__init__()
        self.queue = queue
        self.poll_func = poll_func
        self.interval = interval
        self.event = threading.Event()
        self.myinit = 0

    def run(self):
        while not self.event.is_set():
            if self.myinit == 0:
                temptimestamp = time.time()
                logging.info("PollerThread initial queue population %s", temptimestamp)
                self.queue.put(temptimestamp)
                self.myinit = 1
            time.sleep(1)
            try:
                result = self.poll_func()
                self.queue.put(result)
            except Exception as e:
                logging.error("PollerThread polling error: %s", e)
            time.sleep(self.interval)
        logging.info("PollerThread is going down ...")

