# SPDX-FileCopyrightText: Copyright (c) 2024 Liz Clark for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_ina3221`
================================================================================

CircuitPython driver for the INA3221 Triple 0-26 VDC, ±3.2 Amp Power Monitor

* Author(s): Liz Clark

Implementation Notes
--------------------

**Hardware:**

* `Adafruit INA3221 - Triple 0-26 VDC, ±3.2 Amp Power Monitor <https://www.adafruit.com/product/6062>`_"

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

try:
    from typing import Any, List
except ImportError:
    pass
from adafruit_bus_device.i2c_device import I2CDevice

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_INA3221.git"

DEFAULT_ADDRESS = 0x40
MANUFACTURER_ID = 0x5449
DIE_ID = 0x3220

# Register Definitions
CONFIGURATION = 0x00
SHUNTVOLTAGE_CH1 = 0x01
BUSVOLTAGE_CH1 = 0x02
SHUNTVOLTAGE_CH2 = 0x03
BUSVOLTAGE_CH2 = 0x04
SHUNTVOLTAGE_CH3 = 0x05
BUSVOLTAGE_CH3 = 0x06
CRITICAL_ALERT_LIMIT_CH1 = 0x07
WARNING_ALERT_LIMIT_CH1 = 0x08
CRITICAL_ALERT_LIMIT_CH2 = 0x09
WARNING_ALERT_LIMIT_CH2 = 0x0A
CRITICAL_ALERT_LIMIT_CH3 = 0x0B
WARNING_ALERT_LIMIT_CH3 = 0x0C
SHUNTVOLTAGE_SUM = 0x0D
SHUNTVOLTAGE_SUM_LIMIT = 0x0E
MASK_ENABLE = 0x0F
POWERVALID_UPPERLIMIT = 0x10
POWERVALID_LOWERLIMIT = 0x11
MANUFACTURER_ID_REG = 0xFE
DIE_ID_REG = 0xFF

# Mask/Enable Register bit flags
CONV_READY = 1 << 0
TIMECONT_ALERT = 1 << 1
POWER_VALID = 1 << 2
WARN_CH3 = 1 << 3
WARN_CH2 = 1 << 4
WARN_CH1 = 1 << 5
SUMMATION = 1 << 6
CRITICAL_CH3 = 1 << 7
CRITICAL_CH2 = 1 << 8
CRITICAL_CH1 = 1 << 9


class AVG_MODE:
    """Enumeration for the averaging mode options in INA3221.

    Attributes:
        AVG_1_SAMPLE (int): Average 1 sample.
        AVG_4_SAMPLES (int): Average 4 samples.
        AVG_16_SAMPLES (int): Average 16 samples.
        AVG_64_SAMPLES (int): Average 64 samples.
        AVG_128_SAMPLES (int): Average 128 samples.
        AVG_256_SAMPLES (int): Average 256 samples.
        AVG_512_SAMPLES (int): Average 512 samples.
        AVG_1024_SAMPLES (int): Average 1024 samples.
    """

    AVG_1_SAMPLE: int = 0b000
    AVG_4_SAMPLES: int = 0b001
    AVG_16_SAMPLES: int = 0b010
    AVG_64_SAMPLES: int = 0b011
    AVG_128_SAMPLES: int = 0b100
    AVG_256_SAMPLES: int = 0b101
    AVG_512_SAMPLES: int = 0b110
    AVG_1024_SAMPLES: int = 0b111


class CONV_TIME:
    """Enumeration for conversion time options in INA3221.

    Attributes:
        CONV_TIME_140US (int): Conversion time 140µs.
        CONV_TIME_204US (int): Conversion time 204µs.
        CONV_TIME_332US (int): Conversion time 332µs.
        CONV_TIME_588US (int): Conversion time 588µs.
        CONV_TIME_1MS (int): Conversion time 1ms.
        CONV_TIME_2MS (int): Conversion time 2ms.
        CONV_TIME_4MS (int): Conversion time 4ms.
        CONV_TIME_8MS (int): Conversion time 8ms.
    """

    CONV_TIME_140US: int = 0b000
    CONV_TIME_204US: int = 0b001
    CONV_TIME_332US: int = 0b010
    CONV_TIME_588US: int = 0b011
    CONV_TIME_1MS: int = 0b100
    CONV_TIME_2MS: int = 0b101
    CONV_TIME_4MS: int = 0b110
    CONV_TIME_8MS: int = 0b111


class MODE:
    """Enumeration for operating modes in INA3221.

    Attributes:
        POWER_DOWN (int): Power down mode.
        SHUNT_TRIG (int): Trigger shunt voltage measurement.
        BUS_TRIG (int): Trigger bus voltage measurement.
        SHUNT_BUS_TRIG (int): Trigger both shunt and bus voltage measurements.
        POWER_DOWN2 (int): Alternate power down mode.
        SHUNT_CONT (int): Continuous shunt voltage measurement.
        BUS_CONT (int): Continuous bus voltage measurement.
        SHUNT_BUS_CONT (int): Continuous shunt and bus voltage measurements.
    """

    POWER_DOWN: int = 0b000
    SHUNT_TRIG: int = 0b001
    BUS_TRIG: int = 0b010
    SHUNT_BUS_TRIG: int = 0b011
    POWER_DOWN2: int = 0b100
    SHUNT_CONT: int = 0b101
    BUS_CONT: int = 0b110
    SHUNT_BUS_CONT: int = 0b111


class INA3221Channel:
    """Represents a single channel of the INA3221.

    Args:
        device (Any): The device INA3221 instance managing the I2C communication.
        channel (int): The channel number (1, 2, or 3) for this instance.
    """

    def __init__(self, device: Any, channel: int) -> None:
        self._device = device
        self._channel = channel
        self._shunt_resistance = 0.5

    def enable(self) -> None:
        """Enable this channel"""
        config = self._device._read_register(CONFIGURATION, 2)
        config_value = (config[0] << 8) | config[1]
        config_value |= 1 << (14 - self._channel)  # Set the bit for the specific channel
        high_byte = (config_value >> 8) & 0xFF
        low_byte = config_value & 0xFF
        self._device._write_register(CONFIGURATION, bytes([high_byte, low_byte]))

    @property
    def bus_voltage(self) -> float:
        """Bus voltage in volts."""
        reg_address = [BUSVOLTAGE_CH1, BUSVOLTAGE_CH2, BUSVOLTAGE_CH3][self._channel]
        result = self._device._read_register(reg_address, 2)
        raw_value = int.from_bytes(result, "big")
        voltage = (raw_value >> 3) * 8e-3
        return voltage

    @property
    def shunt_voltage(self) -> float:
        """Shunt voltage in millivolts."""
        reg_address = [SHUNTVOLTAGE_CH1, SHUNTVOLTAGE_CH2, SHUNTVOLTAGE_CH3][self._channel]
        result = self._device._read_register(reg_address, 2)
        raw_value = int.from_bytes(result, "big")
        raw_value = raw_value - 0x10000 if raw_value & 0x8000 else raw_value # convert to signed int16
        return (raw_value >> 3) * 40e-6

    @property
    def shunt_resistance(self) -> float:
        """Shunt resistance in ohms."""
        return self._shunt_resistance

    @shunt_resistance.setter
    def shunt_resistance(self, value: float) -> None:
        self._shunt_resistance = value

    @property
    def current_amps(self) -> float:
        """Returns the current in amperes.

        The current is calculated using the formula: I = Vshunt / Rshunt.
        If the shunt voltage is NaN (e.g., no valid measurement), it returns NaN.
        """
        shunt_voltage = self.shunt_voltage
        if shunt_voltage != shunt_voltage:  # Check for NaN
            return float("nan")
        return shunt_voltage / self._shunt_resistance

    @property
    def critical_alert_threshold(self) -> float:
        """Critical-Alert threshold in amperes

        Returns:
            float: The current critical alert threshold in amperes.
        """
        reg_addr = CRITICAL_ALERT_LIMIT_CH1 + 2 * self._channel
        result = self._device._read_register(reg_addr, 2)
        threshold = int.from_bytes(result, "big")
        return (threshold >> 3) * 40e-6 / self._shunt_resistance

    @critical_alert_threshold.setter
    def critical_alert_threshold(self, current: float) -> None:
        threshold = int(current * self._shunt_resistance / 40e-6 * 8)
        reg_addr = CRITICAL_ALERT_LIMIT_CH1 + 2 * self._channel
        threshold_bytes = threshold.to_bytes(2, "big")
        self._device._write_register(reg_addr, threshold_bytes)

    @property
    def warning_alert_threshold(self) -> float:
        """Warning-Alert threshold in amperes

        Returns:
            float: The current warning alert threshold in amperes.
        """
        reg_addr = WARNING_ALERT_LIMIT_CH1 + self._channel
        result = self._device._read_register(reg_addr, 2)
        threshold = int.from_bytes(result, "big")
        return threshold / (self._shunt_resistance * 8)

    @warning_alert_threshold.setter
    def warning_alert_threshold(self, current: float) -> None:
        threshold = int(current * self._shunt_resistance * 8)
        reg_addr = WARNING_ALERT_LIMIT_CH1 + self._channel
        threshold_bytes = threshold.to_bytes(2, "big")
        self._device._write_register(reg_addr, threshold_bytes)


class INA3221:
    """Driver for the INA3221 device with three channels."""

    def __init__(self, i2c, address: int = DEFAULT_ADDRESS, enable: List = [0,1,2]) -> None:
        """Initializes the INA3221 class over I2C
        Args:
            i2c (I2C): The I2C bus to which the INA3221 is connected.
            address (int, optional): The I2C address of the INA3221. Defaults to DEFAULT_ADDRESS.
        """
        self.i2c_dev = I2CDevice(i2c, address)
        self.reset()

        self.channels: List[INA3221Channel] = [INA3221Channel(self, i) for i in range(3)]
        for i in enable:
            self.channels[i].enable()
        self.mode: int = MODE.SHUNT_BUS_CONT
        self.shunt_voltage_conv_time: int = CONV_TIME.CONV_TIME_8MS
        self.bus_voltage_conv_time: int = CONV_TIME.CONV_TIME_8MS
        # Set the default sampling rate (averaging mode) to 64 samples
        self.averaging_mode: int = AVG_MODE.AVG_64_SAMPLES

    def __getitem__(self, channel: int) -> INA3221Channel:
        """Allows access to channels via index, e.g., ina[0].bus_voltage.

        Args:
            channel (int): The channel index (0, 1, or 2).

        Raises:
            IndexError: If the channel index is out of range (must be 0, 1, or 2).
        """
        if channel < 0 or channel >= 3:
            raise IndexError("Channel must be 0, 1, or 2.")
        return self.channels[channel]

    def reset(self) -> None:
        """Perform a soft reset on the INA3221.

        Returns:
            None
        """
        config = self._read_register(CONFIGURATION, 2)
        config = bytearray(config)
        config[0] |= 0x80  # Set the reset bit
        return self._write_register(CONFIGURATION, config)

    @property
    def die_id(self) -> int:
        """Die ID of the INA3221.

        Returns:
            int: The Die ID in integer format.
        """
        return int.from_bytes(self._read_register(DIE_ID_REG, 2), "big")

    @property
    def manufacturer_id(self) -> int:
        """Manufacturer ID of the INA3221.

        Returns:
            int: The Manufacturer ID in integer format.
        """
        return int.from_bytes(self._read_register(MANUFACTURER_ID_REG, 2), "big")

    @property
    def mode(self) -> int:
        """Operating mode of the INA3221.

        Returns:
            int: The current mode value.
            0: Power down mode, 1: Trigger shunt voltage measurement,
            2: Trigger bus voltage measurement, 3: Trigger both shunt and bus voltage measurements,
            4: Alternate power down mode, 5: Continuous shunt voltage measurement,
            6: Continuous bus voltage measurement, 7: Continuous shunt and bus voltage measurements
        """
        config = self._read_register(CONFIGURATION, 2)
        return config[1] & 0x07

    @mode.setter
    def mode(self, value: int) -> None:
        if not 0 <= value <= 7:
            raise ValueError("Mode must be a 3-bit value (0-7).")
        config = self._read_register(CONFIGURATION, 2)
        config = bytearray(config)
        config[1] = (config[1] & 0xF8) | value
        self._write_register(CONFIGURATION, config)

    @property
    def shunt_voltage_conv_time(self) -> int:
        """Shunt voltage conversion time.

        Returns:
            int: The current shunt voltage conversion time (0-7).
            0: 140µs, 1: 204µs, 2: 332µs, 3: 588µs,
            4: 1ms, 5: 2ms, 6: 4ms, 7: 8ms
        """
        config = self._read_register(CONFIGURATION, 2)
        return (config[1] >> 4) & 0x07

    @shunt_voltage_conv_time.setter
    def shunt_voltage_conv_time(self, conv_time: int) -> None:
        if conv_time < 0 or conv_time > 7:
            raise ValueError("Conversion time must be between 0 and 7")
        config = self._read_register(CONFIGURATION, 2)
        config = bytearray(config)
        config[1] = (config[1] & 0x8F) | (conv_time << 4)
        self._write_register(CONFIGURATION, config)

    @property
    def bus_voltage_conv_time(self) -> int:
        """Bus voltage conversion time.

        Returns:
            int: The current bus voltage conversion time (0-7).
            0: 140µs, 1: 204µs, 2: 332µs, 3: 588µs,
            4: 1ms, 5: 2ms, 6: 4ms, 7: 8ms
        """
        config = self._read_register(CONFIGURATION, 2)
        return (config[0] >> 3) & 0x07  # Bits 12-14 are the bus voltage conversion time

    @bus_voltage_conv_time.setter
    def bus_voltage_conv_time(self, conv_time: int) -> None:
        if conv_time < 0 or conv_time > 7:
            raise ValueError("Conversion time must be between 0 and 7")

        config = self._read_register(CONFIGURATION, 2)
        config = bytearray(config)
        config[0] = config[0] & 0xC7
        config[0] = config[0] | (conv_time << 3)
        self._write_register(CONFIGURATION, config)

    @property
    def averaging_mode(self) -> int:
        """Averaging mode.

        Returns:
            int: The current averaging mode (0-7).
            0: 1 SAMPLE, 1: 4_SAMPLES, 2: 16_SAMPLES,
            3: 64_SAMPLES, 4: 128_SAMPLES, 5: 256_SAMPLES,
            6: 512_SAMPLES, 7: 1024_SAMPLES
        """
        config = self._read_register(CONFIGURATION, 2)
        return (config[1] >> 1) & 0x07

    @averaging_mode.setter
    def averaging_mode(self, mode: int) -> None:
        config = self._read_register(CONFIGURATION, 2)
        config = bytearray(config)
        config[1] = (config[1] & 0xF1) | (mode << 1)
        self._write_register(CONFIGURATION, config)

    @property
    def flags(self) -> int:
        """Flag indicators from the Mask/Enable register.

        Returns:
            int: The current flag indicators from the Mask/Enable register,
            masked for relevant flag bits.
        """
        result = self._read_register(MASK_ENABLE, 2)
        flags = int.from_bytes(result, "big")

        # Mask to keep only relevant flag bits
        mask = (
            CONV_READY
            | TIMECONT_ALERT
            | POWER_VALID
            | WARN_CH3
            | WARN_CH2
            | WARN_CH1
            | SUMMATION
            | CRITICAL_CH3
            | CRITICAL_CH2
            | CRITICAL_CH1
        )

        return flags & mask

    @property
    def summation_channels(self) -> tuple:
        """Status of summation channels (ch1, ch2, ch3)

        Returns:
            tuple: A tuple of three boolean values indicating the status
            of summation channels (ch1, ch2, ch3).
        """
        result = self._read_register(MASK_ENABLE, 2)
        mask_enable = int.from_bytes(result, "big")
        ch1 = bool((mask_enable >> 14) & 0x01)
        ch2 = bool((mask_enable >> 13) & 0x01)
        ch3 = bool((mask_enable >> 12) & 0x01)

        return ch1, ch2, ch3

    @summation_channels.setter
    def summation_channels(self, channels: tuple) -> None:
        if len(channels) != 3:
            raise ValueError("Must pass a tuple of three boolean values (ch1, ch2, ch3)")
        ch1, ch2, ch3 = channels
        scc_value = (ch1 << 2) | (ch2 << 1) | (ch3 << 0)
        result = self._read_register(MASK_ENABLE, 2)
        mask_enable = int.from_bytes(result, "big")
        mask_enable = (mask_enable & ~(0x07 << 12)) | (scc_value << 12)
        self._write_register(MASK_ENABLE, mask_enable.to_bytes(2, "big"))

    @property
    def power_valid_limits(self) -> tuple:
        """Power-Valid upper and lower voltage limits in volts.

        Returns:
            tuple: A tuple containing the lower and upper voltage limits
            in volts as (vlimitlow, vlimithigh).
        """
        low_limit_result = self._read_register(POWERVALID_LOWERLIMIT, 2)
        vlimitlow = int.from_bytes(low_limit_result, "big") * 8e-3
        high_limit_result = self._read_register(POWERVALID_UPPERLIMIT, 2)
        vlimithigh = int.from_bytes(high_limit_result, "big") * 8e-3
        return vlimitlow, vlimithigh

    @power_valid_limits.setter
    def power_valid_limits(self, limits: tuple) -> None:
        if len(limits) != 2:
            raise ValueError("Must provide both lower and upper voltage limits.")
        vlimitlow, vlimithigh = limits
        low_limit_value = int(vlimitlow * 1000)
        high_limit_value = int(vlimithigh * 1000)
        low_limit_bytes = low_limit_value.to_bytes(2, "big")
        self._write_register(POWERVALID_LOWERLIMIT, low_limit_bytes)
        high_limit_bytes = high_limit_value.to_bytes(2, "big")
        self._write_register(POWERVALID_UPPERLIMIT, high_limit_bytes)

    def _to_signed(self, val, bits):
        if val & (1 << (bits - 1)):
            val -= 1 << bits
        return val

    def _write_register(self, reg, data):
        with self.i2c_dev:
            self.i2c_dev.write(bytes([reg]) + data)

    def _read_register(self, reg, length):
        result = bytearray(length)
        try:
            with self.i2c_dev:
                self.i2c_dev.write(bytes([reg]))
                self.i2c_dev.readinto(result)
        except OSError as ex:
            print(f"I2C error: {ex}")
            return None
        return result
