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
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel

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


# 2. Main Window managing the thread lifecycle
class MainWindow(QMainWindow):
    # Signal to pass work to the worker thread
    start_work = Signal(object, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt Python Thread Communication")
        self.setGeometry(100, 100, 300, 150)

        # UI Setup
        self.label = QLabel("Status: Idle", self)
        self.button = QPushButton("Start Background Work", self)
        self.button.clicked.connect(self.trigger_worker)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Thread & Worker Setup
        self.setup_thread()

    def setup_thread(self):
        # self.thread = QThread()
        self.worker = Worker()

        # Connect Worker signals -> UI slots
        self.worker.register_client(self.start_work, self.handle_result)
        # self.worker.result_ready.connect(self.handle_result)
        # self.worker.finished.connect(self.handle_finished)
        self.worker.start()  # Start the worker thread
        # Start thread event loop
        # self.thread.start()

    def trigger_worker(self):
        self.button.setEnabled(False)
        self.label.setText("Status: Processing in thread...")
        
        # Safely send data across thread boundaries
        self.start_work.emit(self, "hello from main thread")

    @Slot(object, str)
    def handle_result(self, sender, result: str):
        if sender is self:
            self.label.setText(f"Result: {result}")
            self.button.setEnabled(True)
        # self.label.setText(f"Result: {result}")

    # @Slot()
    # def handle_finished(self):
    #     self.button.setEnabled(True)

    def closeEvent(self, event):
        # Clean shutdown when closing the window
        # self.thread.quit()
        # self.thread.wait()
        self.worker.stop()
        super().closeEvent(event)



def main_function():
    print(f"Starting helper version {VERSION} (last commit year: {LAST_COMMIT_YEAR})")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main_function()
