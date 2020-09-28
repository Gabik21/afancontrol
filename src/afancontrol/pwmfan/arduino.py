from afancontrol.arduino import ArduinoConnection, ArduinoPin
from afancontrol.pwmfan.base import (
    BaseFanPWMRead,
    BaseFanPWMWrite,
    BaseFanSpeed,
    FanValue,
    PWMValue,
)


class ArduinoFanSpeed(BaseFanSpeed):
    __slots__ = "_conn", "_tacho_pin"

    def __init__(
        self, arduino_connection: ArduinoConnection, *, tacho_pin: ArduinoPin
    ) -> None:
        self._conn = arduino_connection
        self._tacho_pin = tacho_pin

    def get_speed(self) -> FanValue:
        return FanValue(self._conn.get_rpm(self._tacho_pin))

    def __enter__(self):  # reusable
        self._conn.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._conn.__exit__(exc_type, exc_value, exc_tb)


class ArduinoFanPWMRead(BaseFanPWMRead):
    __slots__ = "_conn", "_pwm_pin"

    max_pwm = PWMValue(255)
    min_pwm = PWMValue(0)

    def __init__(
        self, arduino_connection: ArduinoConnection, *, pwm_pin: ArduinoPin
    ) -> None:
        self._conn = arduino_connection
        self._pwm_pin = pwm_pin

    def get(self) -> PWMValue:
        return PWMValue(int(self._conn.get_pwm(self._pwm_pin)))

    def __enter__(self):  # reusable
        self._conn.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._conn.__exit__(exc_type, exc_value, exc_tb)


class ArduinoFanPWMWrite(BaseFanPWMWrite):
    __slots__ = "_conn", "_pwm_pin"

    read_cls = ArduinoFanPWMRead

    def __init__(
        self, arduino_connection: ArduinoConnection, *, pwm_pin: ArduinoPin
    ) -> None:
        self._conn = arduino_connection
        self._pwm_pin = pwm_pin

    def _set_raw(self, pwm: PWMValue) -> None:
        self._conn.set_pwm(self._pwm_pin, pwm)

    def __enter__(self):  # reusable
        self._conn.__enter__()
        self.set_full_speed()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        try:
            self.set_full_speed()
            self._conn.wait_for_status()

            if int(self._conn.get_pwm(self._pwm_pin)) >= self.read_cls.max_pwm:
                return

            raise RuntimeError("Couldn't disable PWM on the fan %r" % self)
        finally:
            self._conn.__exit__(exc_type, exc_value, exc_tb)
