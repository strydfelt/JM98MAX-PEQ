"""
Device service for communicating with JM98 Max DAC/AMP via USB HID.
Based on the existing webdriver implementation.
Supports both Desktop (hidapi) and Android (pyjnius/Android USB Host API).
"""
import math
import sys
import platform
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

# Known VID/PIDs for JM98 Max and compatible devices
KNOWN_DEVICES = [
    (0x0661, None),   # JCally / Generic Savitech
    (0x0666, None),   # JCally JM98 MAX
    (0x262A, None),   # Savitech Official (Fosi, iBasso, Fiio KA series)
    (0x2FC6, None),   # Comtrue CT7601 (Moondrop, Tanchjim)
]

# Check platform
IS_ANDROID = 'android' in sys.platform or hasattr(sys, 'android')


class USBBackend:
    """Abstract base class for USB HID backends."""
    
    def __init__(self):
        self.device = None
        self.connected = False
    
    def connect(self) -> bool:
        raise NotImplementedError
    
    def disconnect(self):
        raise NotImplementedError
    
    def send_packet(self, packet: list) -> bool:
        raise NotImplementedError
    
    def read_packet(self, timeout: int = 1000) -> list:
        raise NotImplementedError
    
    def is_connected(self) -> bool:
        return self.connected


class DesktopUSBBackend(USBBackend):
    """USB HID backend for desktop using hidapi."""
    
    def __init__(self):
        super().__init__()
        self._hid = None
        self._load_hidapi()
    
    def _load_hidapi(self):
        """Load hidapi module."""
        try:
            import hid
            self._hid = hid
            Logger.info("DeviceService: hidapi loaded successfully")
        except ImportError as e:
            Logger.error(f"DeviceService: Failed to load hidapi: {e}")
            self._hid = None
    
    def connect(self) -> bool:
        """Connect to JM98 Max device using hidapi."""
        if not self._hid:
            Logger.error("DeviceService: hidapi not available")
            return False
        
        Logger.info("DeviceService: Scanning for JM98 Max device...")
        
        # Try each known VID
        for vid, pid in KNOWN_DEVICES:
            try:
                if pid is not None:
                    devices = self._hid.enumerate(vid, pid)
                else:
                    devices = self._hid.enumerate(vid)
                
                for dev in devices:
                    # Check if it's a HID device (interface class 3)
                    if dev.get('interface_number') is not None:
                        Logger.info(f"DeviceService: Found device VID=0x{dev['vendor_id']:04X}, "
                                  f"PID=0x{dev['product_id']:04X}, Path={dev['path']}")
                        
                        self.device = self._hid.device()
                        self.device.open_path(dev['path'])
                        self.device.set_nonblocking(1)
                        self.connected = True
                        Logger.info(f"DeviceService: Connected to {dev.get('product_string', 'Unknown')}")
                        return True
            except Exception as e:
                Logger.debug(f"DeviceService: Error scanning VID=0x{vid:04X}: {e}")
                continue
        
        Logger.warning("DeviceService: No JM98 Max device found")
        return False
    
    def disconnect(self):
        """Disconnect from device."""
        if self.device:
            try:
                self.device.close()
            except Exception as e:
                Logger.warning(f"DeviceService: Error closing device: {e}")
            self.device = None
        self.connected = False
    
    def send_packet(self, packet: list) -> bool:
        """Send packet to device (Report ID + data)."""
        if not self.connected or not self.device:
            Logger.warning("DeviceService: Cannot send - not connected")
            return False
        
        # Build full report: Report ID + packet padded to PACKET_SIZE
        report = [REPORT_ID] + packet
        while len(report) < PACKET_SIZE + 1:
            report.append(0x00)
        
        try:
            # hidapi write expects bytes
            data = bytes(report)
            bytes_written = self.device.write(data)
            Logger.debug(f"DeviceService: Sent {bytes_written} bytes: {[hex(b) for b in report[:10]]}...")
            return bytes_written > 0
        except Exception as e:
            Logger.error(f"DeviceService: Send error: {e}")
            self.connected = False
            return False
    
    def read_packet(self, timeout: int = 1000) -> list:
        """Read packet from device."""
        if not self.connected or not self.device:
            return []
        
        try:
            data = self.device.read(PACKET_SIZE + 1, timeout_ms=timeout)
            if data:
                return list(data)
        except Exception as e:
            Logger.debug(f"DeviceService: Read error: {e}")
        return []


class AndroidUSBBackend(USBBackend):
    """USB HID backend for Android using pyjnius (Android USB Host API)."""
    
    def __init__(self):
        super().__init__()
        self._usb_manager = None
        self._device_connection = None
        self._interface = None
        self._endpoint_in = None
        self._endpoint_out = None
        self._pending_intent = None
        self._load_android_classes()
    
    def _load_android_classes(self):
        """Load Android USB classes via pyjnius."""
        try:
            from jnius import autoclass
            
            self.UsbManager = autoclass('android.hardware.usb.UsbManager')
            self.UsbDevice = autoclass('android.hardware.usb.UsbDevice')
            self.UsbDeviceConnection = autoclass('android.hardware.usb.UsbDeviceConnection')
            self.UsbInterface = autoclass('android.hardware.usb.UsbInterface')
            self.UsbEndpoint = autoclass('android.hardware.usb.UsbEndpoint')
            self.UsbConstants = autoclass('android.hardware.usb.UsbConstants')
            self.PendingIntent = autoclass('android.app.PendingIntent')
            self.Intent = autoclass('android.content.Intent')
            self.Context = autoclass('android.content.Context')
            self.PythonActivity = autoclass('org.kivy.android.PythonActivity')
            
            Logger.info("DeviceService: Android USB classes loaded")
            self._android_loaded = True
        except Exception as e:
            Logger.error(f"DeviceService: Failed to load Android USB classes: {e}")
            self._android_loaded = False
    
    def connect(self) -> bool:
        """Connect to JM98 Max device using Android USB Host API."""
        if not self._android_loaded:
            Logger.error("DeviceService: Android USB classes not available")
            return False
        
        try:
            # Get USB Manager
            activity = self.PythonActivity.mActivity
            usb_manager = activity.getSystemService(self.Context.USB_SERVICE)
            
            # Get device list
            device_list = usb_manager.getDeviceList()
            if device_list.isEmpty():
                Logger.warning("DeviceService: No USB devices found")
                return False
            
            # Find matching device
            target_device = None
            for device in device_list.values():
                vid = device.getVendorId()
                pid = device.getProductId()
                
                # Check against known VIDs
                for known_vid, _ in KNOWN_DEVICES:
                    if vid == known_vid:
                        target_device = device
                        Logger.info(f"DeviceService: Found device VID=0x{vid:04X}, PID=0x{pid:04X}, "
                                  f"Name={device.getDeviceName()}")
                        break
                if target_device:
                    break
            
            if not target_device:
                Logger.warning("DeviceService: No compatible JM98 Max device found")
                return False
            
            # Check permission
            if not usb_manager.hasPermission(target_device):
                Logger.info("DeviceService: Requesting USB permission...")
                # Create pending intent for permission request
                intent = self.Intent("com.jm98.USB_PERMISSION")
                self._pending_intent = self.PendingIntent.getBroadcast(
                    activity, 0, intent, self.PendingIntent.FLAG_IMMUTABLE
                )
                usb_manager.requestPermission(target_device, self._pending_intent)
                # Note: Permission is granted asynchronously via broadcast receiver
                # For now, we'll return False and retry on next connect attempt
                return False
            
            # Open device connection
            self._device_connection = usb_manager.openDevice(target_device)
            if not self._device_connection:
                Logger.error("DeviceService: Failed to open device connection")
                return False
            
            # Find HID interface and endpoints
            if not self._claim_interface(target_device):
                return False
            
            self.device = target_device
            self.connected = True
            Logger.info("DeviceService: Android USB connection established")
            return True
            
        except Exception as e:
            Logger.error(f"DeviceService: Android connect error: {e}")
            return False
    
    def _claim_interface(self, usb_device) -> bool:
        """Claim HID interface and find endpoints."""
        try:
            interface_count = usb_device.getInterfaceCount()
            for i in range(interface_count):
                interface = usb_device.getInterface(i)
                if interface.getInterfaceClass() == self.UsbConstants.USB_CLASS_HID:
                    self._interface = interface
                    
                    # Claim interface
                    if not self._device_connection.claimInterface(interface, True):
                        Logger.error("DeviceService: Failed to claim HID interface")
                        return False
                    
                    # Find endpoints
                    endpoint_count = interface.getEndpointCount()
                    for j in range(endpoint_count):
                        endpoint = interface.getEndpoint(j)
                        if endpoint.getType() == self.UsbConstants.USB_ENDPOINT_XFER_INT:
                            if endpoint.getDirection() == self.UsbConstants.USB_DIR_IN:
                                self._endpoint_in = endpoint
                            elif endpoint.getDirection() == self.UsbConstants.USB_DIR_OUT:
                                self._endpoint_out = endpoint
                    
                    if self._endpoint_in and self._endpoint_out:
                        Logger.info("DeviceService: HID interface claimed, endpoints found")
                        return True
                    else:
                        Logger.error("DeviceService: Could not find IN/OUT endpoints")
                        return False
            
            Logger.error("DeviceService: No HID interface found on device")
            return False
            
        except Exception as e:
            Logger.error(f"DeviceService: Error claiming interface: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from device."""
        if self._device_connection and self._interface:
            try:
                self._device_connection.releaseInterface(self._interface)
            except Exception as e:
                Logger.warning(f"DeviceService: Error releasing interface: {e}")
        
        if self._device_connection:
            try:
                self._device_connection.close()
            except Exception as e:
                Logger.warning(f"DeviceService: Error closing connection: {e}")
        
        self._device_connection = None
        self._interface = None
        self._endpoint_in = None
        self._endpoint_out = None
        self.device = None
        self.connected = False
    
    def send_packet(self, packet: list) -> bool:
        """Send packet to device via USB interrupt endpoint."""
        if not self.connected or not self._device_connection or not self._endpoint_out:
            Logger.warning("DeviceService: Cannot send - not connected")
            return False
        
        # Build full report: Report ID + packet padded to PACKET_SIZE
        report = [REPORT_ID] + packet
        while len(report) < PACKET_SIZE + 1:
            report.append(0x00)
        
        try:
            # Convert to byte array
            byte_array = bytearray(report)
            
            # Send via control transfer (HID SET_REPORT) or interrupt endpoint
            # Using interrupt OUT endpoint
            result = self._device_connection.bulkTransfer(
                self._endpoint_out, byte_array, len(byte_array), 1000
            )
            
            if result > 0:
                Logger.debug(f"DeviceService: Sent {result} bytes: {[hex(b) for b in report[:10]]}...")
                return True
            else:
                Logger.error(f"DeviceService: Send failed, result={result}")
                return False
                
        except Exception as e:
            Logger.error(f"DeviceService: Android send error: {e}")
            self.connected = False
            return False
    
    def read_packet(self, timeout: int = 1000) -> list:
        """Read packet from device via USB interrupt endpoint."""
        if not self.connected or not self._device_connection or not self._endpoint_in:
            return []
        
        try:
            buffer = bytearray(PACKET_SIZE + 1)
            result = self._device_connection.bulkTransfer(
                self._endpoint_in, buffer, len(buffer), timeout
            )
            
            if result > 0:
                return list(buffer[:result])
        except Exception as e:
            Logger.debug(f"DeviceService: Android read error: {e}")
        return []


class MockUSBBackend(USBBackend):
    """Mock USB backend for testing without hardware."""
    
    def connect(self) -> bool:
        Logger.info("MockUSBBackend: Mock connecting")
        self.connected = True
        return True
    
    def disconnect(self):
        Logger.info("MockUSBBackend: Mock disconnecting")
        self.connected = False
    
    def send_packet(self, packet: list) -> bool:
        Logger.debug(f"MockUSBBackend: Mock send: {[hex(b) for b in packet[:10]]}...")
        return True
    
    def read_packet(self, timeout: int = 1000) -> list:
        return []


class DeviceService:
    """Service for communicating with JM98 Max device via USB HID."""
    
    def __init__(self, use_mock: bool = False):
        self._backend = None
        self.connected = False
        self._use_mock = use_mock
        self._init_backend()
    
    def _init_backend(self):
        """Initialize appropriate USB backend based on platform."""
        if self._use_mock:
            self._backend = MockUSBBackend()
            Logger.info("DeviceService: Using Mock USB backend")
        elif IS_ANDROID:
            self._backend = AndroidUSBBackend()
            Logger.info("DeviceService: Using Android USB backend")
        else:
            self._backend = DesktopUSBBackend()
            Logger.info("DeviceService: Using Desktop USB backend")
    
    def connect(self) -> bool:
        """
        Connect to JM98 Max device.
        Returns True if successful, False otherwise.
        """
        Logger.info("DeviceService: Attempting to connect to JM98 Max")
        
        if not self._backend:
            Logger.error("DeviceService: No USB backend available")
            return False
        
        success = self._backend.connect()
        self.connected = success
        
        if success:
            Logger.info("DeviceService: Successfully connected to JM98 Max")
        else:
            Logger.warning("DeviceService: Failed to connect to JM98 Max")
        
        return success
    
    def disconnect(self):
        """Disconnect from device."""
        Logger.info("DeviceService: Disconnecting")
        if self._backend:
            self._backend.disconnect()
        self.connected = False
    
    def auto_connect(self):
        """Attempt to auto-connect to previously paired device."""
        # On Android, this would check for previously granted permissions
        # On desktop, just try to connect
        if not self.connected:
            self.connect()
    
    def is_connected(self) -> bool:
        """Check if device is connected."""
        if self._backend:
            return self._backend.is_connected()
        return False
    
    def read_config(self) -> PEQConfiguration:
        """
        Read current PEQ configuration from device.
        Returns PEQConfiguration if successful, None if failed.
        """
        if not self.connected:
            Logger.warning("DeviceService: Cannot read config - not connected")
            return None
        
        Logger.info("DeviceService: Reading device configuration")
        
        try:
            # Read Version
            self._send_command([CMD['READ'], CMD['VERSION'], CMD['END']])
            
            # Read Global Gain
            self._send_command([CMD['READ'], CMD['GAIN'], CMD['END']])
            
            # Request all bands
            bands = []
            for i in range(NUM_BANDS):
                self._send_command([CMD['READ'], CMD['PEQ'], 0x00, 0x00, i, CMD['END']])
                
                # Read response
                response = self._read_response()
                if response and len(response) >= 34:
                    band = self._parse_band_response(response, i)
                    if band:
                        bands.append(band)
            
            if bands:
                config = PEQConfiguration(bands=bands)
                Logger.info(f"DeviceService: Read {len(bands)} bands from device")
                return config
            
        except Exception as e:
            Logger.error(f"DeviceService: Error reading config: {e}")
        
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
        
        try:
            # Write Global Gain
            global_gain = config.global_gain if hasattr(config, 'global_gain') else 0
            self._send_command([
                CMD['WRITE'], CMD['GAIN'], 0x02, 0x00,
                global_gain & 0xFF, CMD['END']
            ])
            
            # Write each band
            for band in config.bands:
                if not self._write_band(band):
                    return False
            
            # Commit to device RAM (TEMP command)
            self._send_command([
                CMD['WRITE'], CMD['TEMP'], 0x04, 0x00,
                0x00, 0xFF, 0xFF, CMD['END']
            ])
            
            Logger.info("DeviceService: Config applied successfully")
            return True
            
        except Exception as e:
            Logger.error(f"DeviceService: Error applying config: {e}")
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
        
        try:
            # Flash command: WRITE, FLASH, 0x01, 0x00, END
            self._send_command([CMD['WRITE'], CMD['FLASH'], 0x01, 0x00, CMD['END']])
            
            # Wait for flash to complete
            import time
            time.sleep(0.5)
            
            Logger.info("DeviceService: Flash save command sent")
            return True
            
        except Exception as e:
            Logger.error(f"DeviceService: Error saving to flash: {e}")
            return False
    
    def _write_band(self, band: PEQBand) -> bool:
        """Write a single band to device."""
        # Effective gain: if band is disabled, use 0 for DSP but keep original gain in state
        effective_gain = band.gain if band.enabled else 0
        
        # Compute IIR filter coefficients
        coeffs = self._compute_iir_filter(band.freq, effective_gain, band.q)
        
        # Convert values to bytes
        freq_bytes = self._to_bytes(int(band.freq), 2)
        q_bytes = self._to_bytes(int(band.q * 256), 2)
        gain_bytes = self._to_bytes(int(effective_gain * 256), 2)
        
        type_code = TYPE_MAP.get(band.type, 2)  # Default to PK
        
        # Build packet (mirrors webdriver writeBand logic)
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
        
        return self._send_command(packet)
    
    def _send_command(self, packet: list) -> bool:
        """Send command packet and wait briefly."""
        if not self._backend.send_packet(packet):
            return False
        
        # Small delay between commands
        import time
        time.sleep(0.03)
        return True
    
    def _read_response(self) -> list:
        """Read response from device."""
        if self._backend:
            return self._backend.read_packet(1000)
        return []
    
    def _parse_band_response(self, data: list, index: int) -> PEQBand:
        """Parse band response from device (mirrors webdriver logic)."""
        try:
            # data[0] = Report ID, data[1] = CMD['PEQ']
            if len(data) < 34 or data[1] != CMD['PEQ']:
                return None
            
            idx = data[4]
            if idx != index:
                return None
            
            # Parse using little-endian
            freq = data[27] | (data[28] << 8)
            q_raw = data[29] | (data[30] << 8)
            gain_raw = data[31] | (data[32] << 8)
            type_code = data[33]
            
            # Convert back from fixed-point
            q = round(q_raw / 256.0, 2)
            gain = round(gain_raw / 256.0, 1)
            
            # Handle signed gain
            if gain_raw & 0x8000:
                gain = -round((0x10000 - gain_raw) / 256.0, 1)
            
            type_str = 'PK'
            if type_code == 1:
                type_str = 'LSQ'
            elif type_code == 3:
                type_str = 'HSQ'
            
            return PEQBand(
                index=index,
                freq=freq if freq > 0 else DEFAULT_FREQS[index],
                gain=gain,
                q=q if q > 0 else 1.0,
                type=type_str,
                enabled=gain != 0
            )
        except Exception as e:
            Logger.error(f"DeviceService: Error parsing band response: {e}")
            return None
    
    def _compute_iir_filter(self, freq: float, gain: float, q: float):
        """Compute IIR filter coefficients (Q30 format). Mirrors webdriver computeIIRFilter."""
        fs = 96000
        A = 10 ** (gain / 20)
        w0 = (freq * 2 * math.pi) / fs
        alpha = math.sin(w0) / (2 * q)
        sqrtA = math.sqrt(A)
        d4 = alpha * sqrtA
        d5 = alpha / sqrtA
        inv_a0 = 1 / (d5 + 1)
        
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
    
    def get_device_info(self) -> dict:
        """Get device information for debugging."""
        info = {
            'connected': self.connected,
            'backend': type(self._backend).__name__ if self._backend else 'None',
            'platform': platform.system(),
            'is_android': IS_ANDROID,
        }
        if self._backend and hasattr(self._backend, 'device') and self._backend.device:
            if IS_ANDROID and hasattr(self._backend.device, 'getDeviceName'):
                info['device_name'] = self._backend.device.getDeviceName()
                info['vid'] = f"0x{self._backend.device.getVendorId():04X}"
                info['pid'] = f"0x{self._backend.device.getProductId():04X}"
            elif hasattr(self._backend.device, 'get_product_string'):
                info['device_name'] = self._backend.device.get_product_string()
        return info


# For testing on desktop without actual device
class MockDeviceService(DeviceService):
    """Mock device service for testing without hardware."""
    
    def __init__(self):
        super().__init__(use_mock=True)
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
    
    def is_connected(self) -> bool:
        """Check if mock device is connected."""
        return self.mock_connected
    
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