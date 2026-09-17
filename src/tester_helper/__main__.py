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

from tester_helper.base_msg import MsgSendAdaptor, MsgProcessor
from tester_helper.dbus_adaptor import main as dbus_main
from tester_helper.workers import child_worker, grandchild_worker, grandchild_worker2
from tester_helper.dbus_api import dbus_child_worker
from PySide6.QtDBus import QDBusConnection, QDBusAbstractAdaptor

# 2. Main Window managing the thread lifecycle
class MainWindow(QMainWindow):

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
        self.grandchild_worker2_adaptor = grandchild_worker2.get_adaptor()
        self.setup_thread()



    def setup_thread(self):
        # Connect Worker signals -> UI slots
        self.child_worker_adaptor.register_result_handler_cb(self.handle_result)
        self.grandchild_worker_adaptor.register_result_handler_cb(self.handle_result2)
        # grandchild_worker.start()  # Start the worker thread


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
        self.grandchild_worker_adaptor.send_msg("hello to gch1 from main thread2")  # Trigger the second worker
        self.grandchild_worker2_adaptor.send_msg("hello to gch2 from main thread2")  # Trigger the second worker


    def handle_result(self, result: str):
        self.label.setText(f"Result: {result}")
        self.button.setEnabled(True)
        # self.label.setText(f"Result: {result}")


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

    bus = QDBusConnection.sessionBus()
    service_name = "com.sapling.ChildWorker"
    if not bus.registerService(service_name):
        print(f"Failed to register D-Bus service '{service_name}'. Is another instance running?")
        sys.exit(1)

    # Register object path on the bus

    object_path = "/com/sapling/ChildWorker"
    # child_worker_dbus_adaptor = ChildWorkerDbusAdaptor(child_worker)
    # child_worker.register_dbus_adaptor(child_worker_dbus_adaptor)  # Register the adaptor with the worker

    if not bus.registerObject(object_path, dbus_child_worker):
        print(f"Failed to register D-Bus object path '{object_path}'.")
        sys.exit(1)

    print(f"D-Bus Service '{service_name}' running at '{object_path}'")
    child_worker.start()  # Start the child worker thread
    grandchild_worker.start()  # Start the grandchild worker thread
    grandchild_worker2.start()  # Start the grandchild worker thread
    dbus_child_worker.start()  # Start the D-Bus child worker thread

    sys.exit(app.exec())

if __name__ == "__main__":
    main_function()
    # dbus_main()
