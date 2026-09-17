from tester_helper.base_msg import MsgProcessor
from PySide6.QtCore import ClassInfo, Signal, Slot
from tester_helper.base_msg import MsgSendAdaptor
from PySide6.QtDBus import QDBusAbstractAdaptor
from tester_helper.workers import child_worker
import time

@ClassInfo({'D-Bus Interface': "com.sapling.ChildWorker"})
class ChildWorkerDbusAdaptor(QDBusAbstractAdaptor):
    """
    Run the following command in a terminal to monitor D-Bus signals:

    busctl --user monitor --match="type='signal',interface='com.sapling.ChildWorker',member='messageProcessed'"

    """
    messageProcessed = Signal(str, str)  # args: topic, payload

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


class DbusChildWorker(MsgProcessor):
    """ D-Bus child worker to send D-Bus messages to 'child_worker'.
        If I add the ChildWorkerDbusAdaptor to the 'child_worker' directly, it will run
        in the same thread as 'process_message' method and block the D-Bus event loop.
    """
    def __init__(self, msg_adaptor: MsgSendAdaptor):
        super().__init__()
        self.dbus_adaptor = ChildWorkerDbusAdaptor(self, msg_adaptor)  # Create the D-Bus adaptor for this worker

    def process_message(self, message: str) -> str:
        """ Called when ChildWorker wants to send a signal back to the D-Bus clients.
        To make it possible, we need to register the D-Bus adaptor with the child_worker and emit a signal from here.
        child_worker.register_dbus_adaptor(dbus_child_worker.get_adaptor())  # Register the adaptor with the child worker
        The child_worker will then call 'send_msg' method, which will be processed here and emit a D-Bus signal to notify external clients.
        <child_worker code>
        if self.dbus_adaptor:
            self.dbus_adaptor.send_msg(message) # <- this message goes to dbus_child_worker
        </child_worker code>
        """

        print(f"received message in DbusChildWorker: {message}")
        self.dbus_adaptor.messageProcessed.emit("dbus/topic", message)  # Emit a D-Bus signal to notify external clients
        return "OK"

dbus_child_worker = DbusChildWorker(child_worker.get_adaptor())  # Create an instance of the D-Bus child worker
child_worker.register_dbus_adaptor(dbus_child_worker.get_adaptor())  # Register the adaptor with the child worker
