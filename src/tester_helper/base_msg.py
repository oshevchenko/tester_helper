from PySide6.QtCore import QMutex, QObject, Signal, Slot, QThread, QWaitCondition, QMutexLocker
import typing


class MsgSendAdaptor(QObject):
    pass


class MsgProcessor(QObject):
    # Signals emitted from the message processor thread back to the message sender.
    # Qt discovers signals from the class definition, not from per-instance assignments.
    # Each MsgProcessor instance still has its own independent signal connections.
    result_ready = Signal(object, bool, str)

    def __init__(self):
        super().__init__()
        self.thread = QThread()


    def get_adaptor(self) -> MsgSendAdaptor:
        return MsgSendAdaptor(self)  # Return a new message sender helper for current thread.


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
    def _process_task(self, sender: object, is_sync: bool, message: str):
        # Heavy computation or I/O running on worker thread
        result = self.process_message(message)
        # Send result back
        # print(f"_process_task: Emitting result_ready signal with result: {result}")
        self.result_ready.emit(sender, is_sync, result)


    def register_msg_sender(self, start_signal: Signal,
                                result_handler_cb: typing.Callable[[object, bool, str], None]):
        start_signal.connect(self._process_task)
        self.result_ready.connect(result_handler_cb)

MSG_PROCESS_TIMEOUT_MS = 10000  # Example timeout value in milliseconds

class MsgSendAdaptor(QObject):
    # Signal to pass message to the message processor thread
    start_work = Signal(object, bool, str)

    def __init__(self, worker: MsgProcessor, timeout_ms: int = MSG_PROCESS_TIMEOUT_MS):
        super().__init__()
        self.timeout_ms = timeout_ms
        self.worker = worker
        self.worker.register_msg_sender(self.start_work, self._handle_result)
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self.result = None
        self._result_handler_ext_cb = []  # List of external result handler callbacks


    @Slot(object, bool, str)
    def _handle_result(self, sender: object, is_sync: bool, result: str):
        if sender is not self:
            return  # Ignore results not meant for this adaptor
        with QMutexLocker(self._mutex):
            # print(f"_handle_result: {result}")
            if is_sync:
                self.result = result
                self._condition.wakeAll()
                # print(f"_handle_result: Woke up waiting thread with result: {result}")
            else:
                # Asynchronous result handling
                for cb in self._result_handler_ext_cb:
                    cb(result)


    def send_msg_sync(self, message: str = "sync msg") -> typing.Optional[str]:
        # Safely send data across thread boundaries
        # print(f"Triggering worker with message: {message}")
        with QMutexLocker(self._mutex):
            # print("qt current thread object:", QThread.currentThread())
            # print("qt thread id:", int(QThread.currentThreadId()))
            self.start_work.emit(self, True, message)
            success = self._condition.wait(self._mutex, self.timeout_ms)
            if not success:
                raise TimeoutError("Timeout waiting for worker response.")
            return self.result


    def send_msg(self, message: str = "async msg") -> None:
        # Asynchronous message sending without waiting for a response
        self.start_work.emit(self, False, message)


    def register_result_handler_cb(self, result_handler_cb: typing.Callable[[str], None]):
        self._result_handler_ext_cb.append(result_handler_cb)


    def set_timeout(self, timeout_ms: int):
        self.timeout_ms = timeout_ms


