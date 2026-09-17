from tester_helper.base_msg import MsgProcessor
from PySide6.QtCore import ClassInfo, QCoreApplication, QObject, Signal, Slot, QTimer, QThread
from tester_helper.base_msg import MsgSendAdaptor
from PySide6.QtDBus import QDBusConnection, QDBusAbstractAdaptor
from tester_helper.workers import child_worker
import sys

# from tester_helper.workers import child_worker



# 1. Define the D-Bus Adaptor

@ClassInfo({'D-Bus Interface': "com.sapling.ChildWorker"})
class ChildWorkerDbusAdaptor(QDBusAbstractAdaptor):
    # D-Bus Interface metadata
    # The interface name external clients will target

    # Signal exposed over D-Bus
    messageReceived = Signal(str, str)  # args: topic, payload

    def __init__(self, parent, msg_adaptor: MsgSendAdaptor):
        super().__init__(parent)
        self.parent_msg_adaptor = msg_adaptor  # Get the message sender adaptor for the parent worker

    @Slot(str, result=str)
    def SendMessageSync(self, message: str) -> str:
        """
        Exposed D-Bus method to send a synchronous message to the ChildWorker and return the result.
busctl --user call \
  com.sapling.ChildWorker \
  /com/sapling/ChildWorker \
  com.sapling.ChildWorker \
  SendMessageSync \
  s "DBus Command"
        """
        return self.parent_msg_adaptor.send_msg_sync(message)

    @Slot(str, result=str)
    def SendMessage(self, message: str) -> str:
        """
        Exposed D-Bus method to send an asynchronous message to the ChildWorker.
busctl --user call \
  com.sapling.ChildWorker \
  /com/sapling/ChildWorker \
  com.sapling.ChildWorker \
  SendMessage \
  s "DBus Command"
        """
        self.parent_msg_adaptor.send_msg(message)
        return "OK"


class DbusWorker(QObject):
    def __init__(self):
        super().__init__()
        self.thread = QThread()


    def start(self):
        self.moveToThread(self.thread)
        self.thread.start()


    def stop(self):
        self.thread.quit()
        self.thread.wait()


class DbusChildWorker(DbusWorker):
    """ D-Bus child worker to send D-Bus messages to 'child_worker'.
        If I add the ChildWorkerDbusAdaptor to the 'child_worker' directly, it will run
        in the same thread as 'process_message' method and block the D-Bus event loop.
    """
    def __init__(self, msg_adaptor: MsgSendAdaptor):
        super().__init__()
        self.dbus_adaptor = ChildWorkerDbusAdaptor(self, msg_adaptor)  # Create the D-Bus adaptor for this worker


dbus_child_worker = DbusChildWorker(child_worker.get_adaptor())  # Create an instance of the D-Bus child worker