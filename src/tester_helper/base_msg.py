from PySide6.QtCore import QMutex, QObject, Signal, Slot, QThread, QWaitCondition, QMutexLocker
import typing

class MsgSendHelper(QObject):
    pass

class IMsgProcessor(QObject):
    def register_msg_sender(self, start_signal: Signal,
                                result_handler_cb: typing.Callable[[object, str], None]):
        pass

class MsgProcessor(IMsgProcessor):
    # Signals emitted from the message processor thread back to the message sender.
    # Qt discovers signals from the class definition, not from per-instance assignments.
    # Each MsgProcessor instance still has its own independent signal connections.
    result_ready = Signal(object, str)

    def __init__(self):
        super().__init__()
        self.thread = QThread()


    def get_adaptor(self) -> MsgSendHelper:
        return MsgSendHelper(self)  # Return a new message sender helper for this processor


    def start(self):
        self.moveToThread(self.thread)
        self.thread.start()


    def stop(self):
        self.thread.quit()
        self.thread.wait()


    def process_message(self, message: str) -> str:
        # Overwrite this method with actual processing logic
        raise NotImplementedError("Subclasses must implement process_message().")


    @Slot(str)
    def _process_task(self, sender, message: str):
        # Heavy computation or I/O running on worker thread
        result = self.process_message(message)
        # Send result back
        self.result_ready.emit(sender, result)


    def register_msg_sender(self, start_signal: Signal,
                                result_handler_cb: typing.Callable[[object, str], None]):
        start_signal.connect(self._process_task)
        self.result_ready.connect(result_handler_cb)

MSG_PROCESS_TIMEOUT_MS = 5000  # Example timeout value in milliseconds

class MsgSendHelper(QObject):
    # Signal to pass message to the message processor thread
    start_work = Signal(object, str)

    def __init__(self, worker: IMsgProcessor, timeout_ms: int = MSG_PROCESS_TIMEOUT_MS):
        super().__init__()
        self.timeout_ms = timeout_ms
        self.worker = worker
        self.worker.register_msg_sender(self.start_work, self._handle_result)
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self.result = None
        self._result_handler_ext_cb = []  # List of external result handler callbacks


    @Slot(object, str)
    def _handle_result(self, sender, result: str):
        with QMutexLocker(self._mutex):
            if sender is self:
                print(f"_handle_result: {result}")
                self.result = result
                self._condition.wakeAll()
                print(f"_handle_result: Woke up waiting thread with result: {result}")
                for cb in self._result_handler_ext_cb:
                    cb(result)


    def send_msg_sync(self, message: str = "sync msg") -> typing.Optional[str]:
        # Safely send data across thread boundaries
        # print(f"Triggering worker with message: {message}")
        with QMutexLocker(self._mutex):
            print("qt current thread object:", QThread.currentThread())
            # print("qt thread id:", int(QThread.currentThreadId()))
            self.start_work.emit(self, message)
            success = self._condition.wait(self._mutex, self.timeout_ms)
            if not success:
                raise TimeoutError("Timeout waiting for worker response.")
            return self.result


    def send_msg(self, message: str = "async msg"):
        # Asynchronous message sending without waiting for a response
        self.start_work.emit(self, message)


    def register_result_handler_cb(self, result_handler_cb: typing.Callable[[str], None]):
        self._result_handler_ext_cb.append(result_handler_cb)


    def set_timeout(self, timeout_ms: int):
        self.timeout_ms = timeout_ms


