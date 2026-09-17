
from tester_helper.base_msg import MsgProcessor
from PySide6.QtCore import QObject, QThread
import time
from datetime import datetime

class ChildWorker(MsgProcessor):
    def __init__(self):
        super().__init__()


    def process_message(self, message: str) ->  str:
        """ Called either on pressing the button 1 
        or when triggered by the grandchild worker.
        """
        print(f"received message in ChildWorker: {message}")
        time.sleep(1)  # Simulate slow task
        # add time to message
        message = f"{message} at {datetime.now().strftime('%H:%M:%S')}"
        print(f"Child Processed: {message.lower()}")
        return f"Child Processed: {message.lower()}"

child_worker = ChildWorker()  # Create an instance of the child worker


class GrandChildWorker(MsgProcessor):
    def __init__(self, parent_worker: ChildWorker):
        super().__init__()
        self.parent_worker_adaptor = parent_worker.get_adaptor()  # Get the adaptor for the parent worker
        self.parent_worker_adaptor.register_result_handler_cb(self.handle_parent_async_result)  # Register a callback to handle results from the parent worker

    def handle_parent_async_result(self, result: str):
        print(f"GrandChildWorker received async result from parent worker: {result}")
        # You can add additional logic here to handle the result if needed

    def process_message(self, message: str) ->  str:
        """ Called on pressing the button 2."""
        # print(f"received message in grandchild worker: {message}")
        time.sleep(1)  # Simulate slow task
        # print(f"Calling child worker from grandchild worker with message: {message}")
        print("1")
        self.parent_worker_adaptor.send_msg("async message")  # Trigger the child worker
        self.parent_worker_adaptor.send_msg("async message")  # Trigger the child worker
        print("2")
        result = self.parent_worker_adaptor.send_msg_sync(message)  # Trigger the child worker
        print("3")

        return f"Grandchild Processed sync: {result.lower()}"

grandchild_worker = GrandChildWorker(child_worker)  # Create an instance of the grandchild worker
grandchild_worker2 = GrandChildWorker(child_worker)  # Create an instance of the grandchild worker
