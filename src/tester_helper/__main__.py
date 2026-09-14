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
# from PySide6.QtWidgets import (
#     QAbstractItemView,
#     QApplication,
#     QDialog,
#     QFileDialog,
#     QMainWindow,
#     QMenu,
#     QMessageBox,
#     QTableWidgetItem,
#     QWidget,
# )
# from PySide6.QtCore import (
#     QCoreApplication,
#     QFile,
#     QMimeData,
#     QPoint,
#     Qt,
# )
# from PySide6.QtGui import (
#     QAction,
#     QCloseEvent,
#     QColor,
#     QDrag,
#     QFontDatabase,
#     QIcon,
#     QImage,
#     QKeySequence,
#     QMouseEvent,
#     QPixmap,
#     QShortcut,
# )


def main_function():
    print(f"Starting helper version {VERSION} (last commit year: {LAST_COMMIT_YEAR})")


if __name__ == "__main__":
    main_function()
