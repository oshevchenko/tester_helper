import os
import re
import csv
import sys
import json
import fnmatch
import typing
import argparse
import webbrowser
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from tester_helper.resources.version import VERSION, LAST_COMMIT_YEAR, RESET_SETTINGS
import sys
import time
from PySide6.QtCore import QObject, QThread, Signal, Slot, QMutex, QWaitCondition, QMutexLocker
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel

class MessageHelper(QObject):
    # Signal to pass work to the worker thread
    start_work = Signal(object, str)

    def __init__(self, worker: QObject):
        super().__init__()
        self.worker = worker
        # Connect Worker signals -> UI slots
        self.worker.register_client(self.start_work, self.handle_result)
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self.result = None


    @Slot(object, str)
    def handle_result(self, sender, result: str):
        if sender is self:
            with QMutexLocker(self._mutex):
                print(f"MessageHelper: Result from worker: {result}")
                self.result = result
                self._condition.wakeAll()


    def send_message_sync(self, message: str = "hello trigger_worker") -> typing.Optional[str]:
        # Safely send data across thread boundaries
        print(f"Triggering worker with message: {message}")
        with QMutexLocker(self._mutex):
            self.start_work.emit(self, message)
            timeout_ms = 5000  # Example timeout value in milliseconds
            success = self._condition.wait(self._mutex, timeout_ms)
            if not success:
                # raise TimeoutError("Timeout waiting for worker response.")
                raise TimeoutError("Timeout waiting for worker response.")
            return self.result

# 1. Define the Worker class containing heavy tasks
class Worker(QObject):
    # Signals emitted from the worker thread back to the UI thread
    result_ready = Signal(object, str)

    def __init__(self):
        super().__init__()
        self.thread = QThread()


    def start(self):
        self.moveToThread(self.thread)
        self.thread.start()


    def stop(self):
        self.thread.quit()
        self.thread.wait()


    def process_message(self, message: str) -> str:
        # Overwrite this method with actual processing logic
        time.sleep(2)  # Simulate slow task
        return f"Processed: {message.upper()}"


    @Slot(str)
    def process_task(self, sender, message: str):
        # Heavy computation or I/O running on worker thread
        result = self.process_message(message)
        # Send result back
        self.result_ready.emit(sender, result)
        # self.finished.emit()


    def register_client(self, start_signal: Signal,
                                result_handler_cb: typing.Callable[[object, str], None]):
        start_signal.connect(self.process_task)
        self.result_ready.connect(result_handler_cb)



class ChildWorker(Worker):
    def __init__(self):
        self.msg_sender = None
        super().__init__()


    def register_message_sender(self, msg_sender: MessageHelper):
        self.msg_sender = msg_sender


    def ext_send_message_sync(self, message: str) -> typing.Optional[str]:
        if self.msg_sender:
            return self.msg_sender.send_message_sync(message)
        else:
            return "None"


    def process_message(self, message: str) ->  str:
        # Overwrite this method with actual processing logic for child worker
        result = self.ext_send_message_sync(message)  # Trigger the other worker
        time.sleep(1)  # Simulate slow task

        return f"Child Processed: {message.lower()} | Other worker result: {result}"

# 2. Main Window managing the thread lifecycle
class MainWindow(QMainWindow):
    # Signal to pass work to the worker thread
    start_work = Signal(object, str)
    start_work2 = Signal(object, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt Python Thread Communication")
        self.setGeometry(100, 100, 300, 150)

        # UI Setup
        self.label = QLabel("Status: Idle", self)
        self.button = QPushButton("Start Background Work", self)
        self.button.clicked.connect(self.trigger_worker)

        self.label2 = QLabel("Status: Idle2", self)
        self.button2 = QPushButton("Start Background Work2", self)
        self.button2.clicked.connect(self.trigger_worker2)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.addWidget(self.label2)
        layout.addWidget(self.button2)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Thread & Worker Setup
        self.setup_thread()

    def setup_thread(self):
        # self.thread = QThread()
        self.worker = ChildWorker()
        # Connect Worker signals -> UI slots
        self.worker.register_client(self.start_work, self.handle_result)
        self.worker.start()  # Start the worker thread

        self.worker2 = ChildWorker()  # Second worker that can trigger the first worker
        self.worker2.register_message_sender(MessageHelper(self.worker))
        # Connect Worker signals -> UI slots
        self.worker2.register_client(self.start_work2, self.handle_result2)
        self.worker2.start()  # Start the worker thread

        print("id for worker1:", id(self.worker.result_ready))
        print("id for worker2:", id(self.worker2.result_ready))

    def trigger_worker(self):
        self.button.setEnabled(False)
        self.label.setText("Status: Processing in thread...")
        
        # Safely send data across thread boundaries
        self.start_work.emit(self, "hello from main thread")

    def trigger_worker2(self):
        self.button2.setEnabled(False)
        self.label2.setText("Status: Processing in thread2...")

        # Safely send data across thread boundaries
        self.start_work2.emit(self, "hello from main thread2")

    @Slot(object, str)
    def handle_result(self, sender, result: str):
        if sender is self:
            self.label.setText(f"Result: {result}")
            self.button.setEnabled(True)
        # self.label.setText(f"Result: {result}")
    @Slot(object, str)
    def handle_result2(self, sender, result: str):
        if sender is self:
            self.label2.setText(f"Result: {result}")
            self.button2.setEnabled(True)
        # self.label2.setText(f"Result: {result}")

    # @Slot()
    # def handle_finished(self):
    #     self.button.setEnabled(True)

    def closeEvent(self, event):
        # Clean shutdown when closing the window
        # self.thread.quit()
        # self.thread.wait()
        self.worker.stop()
        self.worker2.stop()
        super().closeEvent(event)



def main_function():
    print(f"Starting helper version {VERSION} (last commit year: {LAST_COMMIT_YEAR})")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main_function()
