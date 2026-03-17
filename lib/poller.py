# Polling and threading logic for DWD forecast
import threading
import time
import logging

class PollerThread(threading.Thread):
    def __init__(self, queue, poll_func, interval=60, cooldown=3600):
        super().__init__()
        self.queue = queue
        self.poll_func = poll_func
        self.interval = interval
        self.cooldown = cooldown  # seconds to wait after successful fetch
        self.event = threading.Event()
        self.myinit = 0
        self.last_success_time = 0
        self.last_result = None

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
                if result is not None and result != self.last_result:
                    self.last_success_time = time.time()
                    self.last_result = result
                    self.queue.put(result)
                    logging.info("PollerThread: new data found, entering cooldown for %d seconds", self.cooldown)
                    # Wait cooldown period after new data
                    for _ in range(int(self.cooldown)):
                        if self.event.is_set():
                            break
                        time.sleep(1)
                else:
                    # No new data, wait normal interval
                    logging.info("PollerThread: no new data, waiting %d seconds", self.interval)
                    for _ in range(int(self.interval)):
                        if self.event.is_set():
                            break
                        time.sleep(1)
            except Exception as e:
                logging.error("PollerThread polling error: %s", e)
                for _ in range(int(self.interval)):
                    if self.event.is_set():
                        break
                    time.sleep(1)
        logging.info("PollerThread is going down ...")
