"""
Device service for communicating with JM98 Max DAC/AMP via USB HID.
Based on the existing webdriver implementation.
"""
import math
from kivy.logger import Logger
from models.peq_config import PEQConfiguration, PEQBand

# Constants from the webdriver implementation
REPORT_ID = 75
PACKET_SIZE = 63
NUM_BANDS = 8

# Command Codes
CMD = {
    'PEQ': 0x09,
    'VERSION': 0x0c,
    'TEMP': 0x0a,
    'FLASH': 0x01,
    'GAIN': 0x03,
    'READ': 0x80,
    'WRITE': 0x01,
    'END': 0x00,
}

# Default frequencies
DEFAULT_FREQS = [40, 100, 250, 500, 1000, 3000, 8000, 16000]

# Type mapping
TYPE_MAP = {'PK': 2, 'LSQ': 1, 'HSQ': 3}


class DeviceService:
    """Service for communicating with JM98 Max device via USB HID."""
    
    def __init__(self):
        self.device = None
        self.connected = False
        self._device_handle = None
        
    def connect(self) -> bool:
        """
        Connect to JM98 Max device.
        On Android, this would use USB Host API.
        For now, this is a stub that returns False.
        """
        Logger.info("DeviceService: Attempting to connect to JM98 Max")
        
        # TODO: Implement actual USB HID connection for Android
        # This would use:
        # - android.hardware.usb.UsbManager
        # - android.hardware.usb.UsbDevice
        # - android.hardware.usb.UsbDeviceConnection
        # - android.hardware.usb.UsbInterface
        # - android.hardware.usb.UsbEndpoint
        
        # Vendor/Product IDs for JM98 Max
        # VID: 0x661 (JCally / Generic Savitech)
        # PID: Need to verify
        
        Logger.warning("DeviceService: USB HID connection not yet implemented for Android")
        return False
    
    def disconnect(self):
        """Disconnect from device."""
        Logger.info("DeviceService: Disconnecting")
        if self._device_handle:
            # Close device connection
            self._device_handle = None
        self.connected = False
        self.device = None
    
    def auto_connect(self):
        """Attempt to auto-connect to previously paired device."""
        # TODO: Implement auto-connect logic
        pass
    
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self.connected
    
    def read_config(self) -> PEQConfiguration:
        """
        Read current PEQ configuration from device.
        Returns None if failed.
        """
        if not self.connected:
            Logger.warning("DeviceService: Cannot read config - not connected")
            return None
        
        Logger.info("DeviceService: Reading device configuration")
        
        # TODO: Implement actual reading from device
        # This would send READ commands for each band and parse responses
        
        return None
    
    def apply_config(self, config: PEQConfiguration, trial: bool = False) -> bool:
        """
        Apply PEQ configuration to device.
        
        Args:
            config: PEQConfiguration to apply
            trial: If True, apply to temporary RAM only; if False, apply persistently
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            Logger.warning("DeviceService: Cannot apply config - not connected")
            return False
        
        Logger.info(f"DeviceService: Applying config (trial={trial})")
        
        # TODO: Implement actual writing to device
        # This would:
        # 1. Write global gain
        # 2. Write each band using write_band logic
        # 3. If not trial, commit to device RAM
        
        return False
    
    def save_to_flash(self) -> bool:
        """
        Save current device configuration to flash memory.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            Logger.warning("DeviceService: Cannot save to flash - not connected")
            return False
        
        Logger.info("DeviceService: Saving configuration to flash")
        
        # TODO: Implement flash save command
        # This would send: [CMD.WRITE, CMD.FLASH, 0x01, 0x00, CMD.END]
        
        return False
    
    def _write_band(self, band: PEQBand) -> bool:
        """Write a single band to device."""
        # This mirrors the logic from the webdriver's writeBand function
        
        # Effective gain: if band is disabled, use 0 for DSP but keep original gain in state
        effective_gain = band.gain if band.enabled else 0
        
        # Compute IIR filter coefficients
        coeffs = self._compute_iir_filter(band.freq, effective_gain, band.q)
        
        # Convert values to bytes
        freq_bytes = self._to_bytes(int(band.freq), 2)
        q_bytes = self._to_bytes(int(band.q * 256), 2)
        gain_bytes = self._to_bytes(int(effective_gain * 256), 2)
        
        type_code = TYPE_MAP.get(band.type, 2)  # Default to PK
        
        # Build packet
        packet = [
            CMD['WRITE'],
            CMD['PEQ'],
            0x18,  # Length
            0x00,
            band.index,
            0x00,
            0x00,
            *coeffs,
            *freq_bytes,
            *q_bytes,
            *gain_bytes,
            type_code,
            0x00,
            0x00,
            CMD['END'],
        ]
        
        # Pad to packet size
        while len(packet) < PACKET_SIZE:
            packet.append(0x00)
        
        # TODO: Send packet to device
        # await self._send_packet(packet)
        
        return False
    
    def _compute_iir_filter(self, freq: float, gain: float, q: float):
        """Compute IIR filter coefficients (Q30 format)."""
        # This mirrors the computeIIRFilter function from the webdriver
        fs = 96000
        A = 10 ** (gain / 20)
        w0 = (freq * 2 * math.pi) / fs
        alpha = math.sin(w0) / (2 * q)
        sqrtA = math.sqrt(A)
        d4 = alpha * sqrtA
        d5 = alpha / sqrtA
        inv_a0 = 1 / (d5 + 1)
        
        # Coefficients: b0, b1, b2, -a1, -a2
        cos_w0 = math.cos(w0)
        coeffs = [
            (1 + d4) * inv_a0,
            -2 * cos_w0 * inv_a0,
            (1 - d4) * inv_a0,
            -(-2 * cos_w0 * inv_a0),
            -((1 - d5) * inv_a0),
        ]
        
        # Convert to Q30 bytes (4 bytes each, little-endian)
        s = 1073741824  # 2^30
        result = []
        for c in coeffs:
            q30 = int(round(c * s))
            result.extend([
                q30 & 0xFF,
                (q30 >> 8) & 0xFF,
                (q30 >> 16) & 0xFF,
                (q30 >> 24) & 0xFF,
            ])
        
        return result
    
    def _to_bytes(self, n: int, count: int):
        """Convert integer to little-endian bytes."""
        return [(n >> (8 * i)) & 0xFF for i in range(count)]
    
    def _send_packet(self, packet) -> bool:
        """Send packet to device."""
        # TODO: Implement actual USB HID send
        Logger.debug(f"DeviceService: Sending packet: {[hex(b) for b in packet[:10]]}...")
        return False


# For testing on desktop without actual device
class MockDeviceService(DeviceService):
    """Mock device service for testing without hardware."""
    
    def __init__(self):
        super().__init__()
        self.mock_connected = False
    
    def connect(self) -> bool:
        """Mock connect - always succeeds."""
        Logger.info("MockDeviceService: Mock connecting")
        self.mock_connected = True
        self.connected = True
        return True
    
    def disconnect(self):
        """Mock disconnect."""
        Logger.info("MockDeviceService: Mock disconnecting")
        self.mock_connected = False
        self.connected = False
    
    def read_config(self) -> PEQConfiguration:
        """Mock read config - returns default if connected, None otherwise."""
        Logger.info("MockDeviceService: Mock reading config")
        if not self.connected:
            return None
        return PEQConfiguration.create_default()
    
    def apply_config(self, config: PEQConfiguration, trial: bool = False) -> bool:
        """Mock apply config."""
        Logger.info(f"MockDeviceService: Mock applying config (trial={trial})")
        if not self.connected:
            return False
        return True
    
    def save_to_flash(self) -> bool:
        """Mock save to flash."""
        Logger.info("MockDeviceService: Mock saving to flash")
        if not self.connected:
            return False
        return True