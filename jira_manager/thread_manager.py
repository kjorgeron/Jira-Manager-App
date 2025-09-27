import threading
import time
from os import cpu_count


class SmartThread(threading.Thread):
    active_count = 0
    count_lock = threading.Lock()
    total_allotment = max(1, (cpu_count() or 4) - 1)  # Always leave 1 for main thread

    def start(self, *args, **kwargs):
        # Wait until there is a slot available
        while True:
            with SmartThread.count_lock:
                if SmartThread.active_count < SmartThread.total_allotment:
                    SmartThread.active_count += 1
                    break
                else:
                    sleep_time = (
                        SmartThread.active_count / SmartThread.total_allotment
                    )  # Distribute wait time
                    print(
                        f"[SmartThread] active_count ({SmartThread.active_count}) is greater than or equal to total_allotment ({SmartThread.total_allotment}), waiting for {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)  # Sleep briefly and try again
        super().start(*args, **kwargs)

    def run(self):
        try:
            super().run()
        finally:
            with SmartThread.count_lock:
                SmartThread.active_count -= 1

    @classmethod
    def get_active_count(cls):
        with cls.count_lock:
            return cls.active_count

    @classmethod
    def get_total_allotment(cls):
        return cls.total_allotment
