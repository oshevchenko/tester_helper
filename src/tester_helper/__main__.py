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

from tester_helper.base_msg import MsgSendHelper, MsgProcessor



class ChildWorker(MsgProcessor):
    def __init__(self):
        super().__init__()

    def process_message(self, message: str) ->  str:
        # Overwrite this method with actual processing logic for child worker
        # result = self.ext_send_message_sync(message)  # Trigger the other worker
        print(f"received message in child worker: {message}")
        time.sleep(1)  # Simulate slow task

        return f"Child Processed: {message.lower()}"

child_worker = ChildWorker()  # Create an instance of the child worker

class GrandChildWorker(MsgProcessor):
    def __init__(self, parent_worker: ChildWorker):
        super().__init__()
        self.parent_worker = parent_worker
        self.parent_worker_adaptor = parent_worker.get_adaptor()  # Get the adaptor for the parent worker

    def process_message(self, message: str) ->  str:
        # Overwrite this method with actual processing logic for child worker
        # result = self.ext_send_message_sync(message)  # Trigger the other worker
        print(f"received message in grandchild worker: {message}")
        time.sleep(1)  # Simulate slow task
        print(f"Calling child worker from grandchild worker with message: {message}")
        result = self.parent_worker_adaptor.send_msg_sync(message)  # Trigger the child worker

        return f"Grandchild Processed: {result.lower()}"

grandchild_worker = GrandChildWorker(child_worker)  # Create an instance of the grandchild worker
# 2. Main Window managing the thread lifecycle
class MainWindow(QMainWindow):
    # Signal to pass work to the worker thread
    # start_work = Signal(object, str)
    # start_work2 = Signal(object, str)

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
        self.child_worker_adaptor = child_worker.get_adaptor()
        self.grandchild_worker_adaptor = grandchild_worker.get_adaptor()
        self.setup_thread()


    def setup_thread(self):
        # Connect Worker signals -> UI slots
        self.child_worker_adaptor.register_result_handler_cb(self.handle_result)
        self.grandchild_worker_adaptor.register_result_handler_cb(self.handle_result2)
        # grandchild_worker.start()  # Start the worker thread
        child_worker.start()  # Start the child worker thread
        grandchild_worker.start()  # Start the grandchild worker thread

        print("id for worker1:", id(child_worker.result_ready))
        print("id for worker2:", id(grandchild_worker.result_ready))

    def trigger_worker(self):
        self.button.setEnabled(False)
        self.label.setText("Status: Processing in thread...")
        # Safely send data across thread boundaries
        # self.start_work.emit(self, "hello from main thread")
        self.child_worker_adaptor.send_msg("hello from main thread")  # Trigger the first worker

    def trigger_worker2(self):
        self.button2.setEnabled(False)
        self.label2.setText("Status: Processing in thread2...")

        # Safely send data across thread boundaries
        self.grandchild_worker_adaptor.send_msg("hello from main thread2")  # Trigger the second worker

    # @Slot(object, str)
    def handle_result(self, result: str):
        self.label.setText(f"Result: {result}")
        self.button.setEnabled(True)
        # self.label.setText(f"Result: {result}")
    # @Slot(object, str)
    def handle_result2(self, result: str):
        self.label2.setText(f"Result: {result}")
        self.button2.setEnabled(True)

    # @Slot()
    # def handle_finished(self):
    #     self.button.setEnabled(True)

    def closeEvent(self, event):
        # Clean shutdown when closing the window
        # self.thread.quit()
        # self.thread.wait()
        child_worker.stop()
        grandchild_worker.stop()
        super().closeEvent(event)



def main_function():
    print(f"Starting helper version {VERSION} (last commit year: {LAST_COMMIT_YEAR})")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main_function()
