import sys
import signal
from PySide6.QtCore import ClassInfo, QCoreApplication, QObject, Signal, Slot, QTimer
from PySide6.QtDBus import QDBusConnection, QDBusAbstractAdaptor

# 1. Define the D-Bus Adaptor
@ClassInfo({'D-Bus Interface': "com.sapling.MqttDaemon.Control"})
class MqttDaemonAdaptor(QDBusAbstractAdaptor):
    # D-Bus Interface metadata
    # The interface name external clients will target

    # Signal exposed over D-Bus
    messageReceived = Signal(str, str)  # args: topic, payload

    def __init__(self, parent):
        super().__init__(parent)

    @Slot(str, str, result=bool)
    def PublishMessage(self, topic: str, message: str) -> bool:
        """Exposed D-Bus method to publish an MQTT message."""
        return self.parent().publish_mqtt(topic, message)

    @Slot(result=str)
    def GetStatus(self) -> str:
        """Exposed D-Bus method to query daemon status."""
        return self.parent().get_status()


# 2. Main Service Logic
class MqttService(QObject):
    def __init__(self):
        super().__init__()
        self._connected = True
        
        # Instantiate the D-Bus adaptor attached to this parent QObject
        self.adaptor = MqttDaemonAdaptor(self)

        # Simulate receiving an MQTT message every 6 seconds to emit a D-Bus signal
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._simulate_incoming_mqtt)
        self.sim_timer.start(6000)

    def publish_mqtt(self, topic: str, message: str) -> bool:
        print(f"[Daemon] Action: Publishing MQTT -> Topic: {topic} | Body: {message}")
        return True

    def get_status(self) -> str:
        return "CONNECTED" if self._connected else "DISCONNECTED"

    def _simulate_incoming_mqtt(self):
        print("[Daemon] Simulating incoming MQTT payload...")
        # Emit signal through the adaptor onto the D-Bus bus
        self.adaptor.messageReceived.emit("sensor/temperature", "22.5°C")


# 3. Application Setup
def main():
    app = QCoreApplication(sys.argv)

    # Establish connection to the Session Bus (use systemBus() for root services)
    bus = QDBusConnection.sessionBus()

    # Request a unique service name on D-Bus
    service_name = "com.sapling.MqttDaemon"
    if not bus.registerService(service_name):
        print(f"Failed to register D-Bus service '{service_name}'. Is another instance running?")
        sys.exit(1)

    # Register object path on the bus
    service = MqttService()
    object_path = "/com/sapling/MqttDaemon"
    
    if not bus.registerObject(object_path, service):
        print(f"Failed to register D-Bus object path '{object_path}'.")
        sys.exit(1)

    print(f"D-Bus Service '{service_name}' running at '{object_path}'")

    # Handle UNIX signals gracefully
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())
    
    sig_timer = QTimer()
    sig_timer.start(500)
    sig_timer.timeout.connect(lambda: None)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()