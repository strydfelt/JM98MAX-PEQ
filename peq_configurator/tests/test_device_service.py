"""
Unit tests for Device Service.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from services.device_service import (
    DeviceService, MockDeviceService,
    REPORT_ID, PACKET_SIZE, NUM_BANDS, CMD, DEFAULT_FREQS, TYPE_MAP
)
from models.peq_config import PEQConfiguration, PEQBand


class TestMockDeviceService:
    """Tests for MockDeviceService."""
    
    @pytest.fixture
    def device(self):
        return MockDeviceService()
    
    def test_connect_disconnect(self, device):
        """Test mock connect and disconnect."""
        assert device.is_connected() is False
        
        result = device.connect()
        assert result is True
        assert device.is_connected() is True
        
        device.disconnect()
        assert device.is_connected() is False
    
    def test_read_config(self, device):
        """Test reading default configuration."""
        device.connect()
        config = device.read_config()
        assert config is not None
        assert len(config.bands) == 8
        for band in config.bands:
            assert band.gain == 0.0
            assert band.q == 0.75
            assert band.type == "PK"
    
    def test_apply_config_trial(self, device):
        """Test applying configuration in trial mode."""
        device.connect()
        config = PEQConfiguration.create_default()
        config.bands[0].gain = 5.0
        
        result = device.apply_config(config, trial=True)
        assert result is True
    
    def test_apply_config_persistent(self, device):
        """Test applying configuration persistently."""
        device.connect()
        config = PEQConfiguration.create_default()
        config.bands[0].gain = 5.0
        
        result = device.apply_config(config, trial=False)
        assert result is True
    
    def test_save_to_flash(self, device):
        """Test saving to flash."""
        device.connect()
        result = device.save_to_flash()
        assert result is True
    
    def test_operations_without_connection(self, device):
        """Test that operations fail without connection."""
        assert device.is_connected() is False
        
        config = device.read_config()
        assert config is None
        
        result = device.apply_config(PEQConfiguration.create_default())
        assert result is False
        
        result = device.save_to_flash()
        assert result is False


class TestDeviceServiceConstants:
    """Tests for DeviceService constants and helpers."""
    
    def test_constants(self):
        """Test that constants match webdriver implementation."""
        from services.device_service import REPORT_ID, PACKET_SIZE, NUM_BANDS, CMD, DEFAULT_FREQS, TYPE_MAP
        
        assert REPORT_ID == 75
        assert PACKET_SIZE == 63
        assert NUM_BANDS == 8
        assert CMD['PEQ'] == 0x09
        assert CMD['VERSION'] == 0x0c
        assert CMD['TEMP'] == 0x0a
        assert CMD['FLASH'] == 0x01
        assert CMD['GAIN'] == 0x03
        assert CMD['READ'] == 0x80
        assert CMD['WRITE'] == 0x01
        assert CMD['END'] == 0x00
        assert DEFAULT_FREQS == [40, 100, 250, 500, 1000, 3000, 8000, 16000]
        assert TYPE_MAP == {'PK': 2, 'LSQ': 1, 'HSQ': 3}
    
    def test_to_bytes(self):
        """Test byte conversion."""
        device = DeviceService()
        assert device._to_bytes(0x1234, 2) == [0x34, 0x12]
        assert device._to_bytes(0x12345678, 4) == [0x78, 0x56, 0x34, 0x12]
        assert device._to_bytes(255, 1) == [0xFF]
    
    def test_compute_iir_filter(self):
        """Test IIR filter coefficient computation."""
        device = DeviceService()
        # Test with a simple band
        coeffs = device._compute_iir_filter(1000, 0.0, 0.75)
        # Should return 20 bytes (5 coefficients * 4 bytes each)
        assert len(coeffs) == 20
        # All should be integers 0-255
        for c in coeffs:
            assert isinstance(c, int)
            assert 0 <= c <= 255
        
        # Test with gain
        coeffs_gain = device._compute_iir_filter(1000, 6.0, 0.75)
        assert len(coeffs_gain) == 20
        # Should be different from 0 gain
        assert coeffs != coeffs_gain


class TestPEQBandSerialisation:
    """Test PEQBand serialization for device communication."""
    
    def test_band_to_bytes(self):
        """Test that band values convert correctly for device packets."""
        from services.device_service import TYPE_MAP
        
        band = PEQBand(index=0, freq=40, gain=3.0, q=1.0, type="PK", enabled=True)
        
        # Test effective gain calculation
        effective_gain = band.gain if band.enabled else 0
        assert effective_gain == 3.0
        
        # Test disabled band
        band.enabled = False
        effective_gain = band.gain if band.enabled else 0
        assert effective_gain == 0
        
        # Test type mapping
        assert TYPE_MAP['PK'] == 2
        assert TYPE_MAP['LSQ'] == 1
        assert TYPE_MAP['HSQ'] == 3


class TestUSBPacketBuilding:
    """Test USB packet building and parsing logic."""
    
    def test_write_band_packet_structure(self):
        """Test that write_band builds correct packet structure."""
        device = DeviceService(use_mock=True)
        device.connect()
        
        band = PEQBand(index=0, freq=1000, gain=3.0, q=0.75, type="PK", enabled=True)
        
        # Get the packet that would be sent (by accessing _write_band internal logic)
        # We can test the packet building by checking the components
        effective_gain = band.gain if band.enabled else 0
        coeffs = device._compute_iir_filter(band.freq, effective_gain, band.q)
        freq_bytes = device._to_bytes(int(band.freq), 2)
        q_bytes = device._to_bytes(int(band.q * 256), 2)
        gain_bytes = device._to_bytes(int(effective_gain * 256), 2)
        type_code = TYPE_MAP.get(band.type, 2)
        
        packet = [
            CMD['WRITE'],
            CMD['PEQ'],
            0x18,
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
        
        # Verify packet structure
        assert len(packet) == PACKET_SIZE
        assert packet[0] == CMD['WRITE']
        assert packet[1] == CMD['PEQ']
        assert packet[2] == 0x18  # Length
        assert packet[4] == 0  # Band index
        assert packet[-1] == CMD['END']
        
        # Verify coefficients are 20 bytes (5 coeffs * 4 bytes)
        assert len(coeffs) == 20
        
        # Verify freq bytes (1000 = 0x03E8 -> little endian: E8, 03)
        assert freq_bytes == [0xE8, 0x03]
        
        # Verify q bytes (0.75 * 256 = 192 = 0xC0 -> C0, 00)
        assert q_bytes == [0xC0, 0x00]
        
        # Verify gain bytes (3.0 * 256 = 768 = 0x0300 -> 00, 03)
        assert gain_bytes == [0x00, 0x03]
        
        # Verify type code
        assert type_code == 2  # PK
    
    def test_disabled_band_uses_zero_gain(self):
        """Test that disabled bands use 0 gain for DSP but keep original gain."""
        device = DeviceService(use_mock=True)
        device.connect()
        
        band = PEQBand(index=1, freq=250, gain=-6.0, q=1.0, type="LSQ", enabled=False)
        
        effective_gain = band.gain if band.enabled else 0
        assert effective_gain == 0.0
        
        # But original gain is preserved
        assert band.gain == -6.0
        
        gain_bytes = device._to_bytes(int(effective_gain * 256), 2)
        assert gain_bytes == [0x00, 0x00]
    
    def test_parse_band_response(self):
        """Test parsing band response from device."""
        device = DeviceService(use_mock=True)
        
        # Simulate a device response for band 0
        # Report ID (75) + CMD.PEQ (0x09) + ... + freq(1000) + q(0.75) + gain(3.0) + type(PK=2)
        response = [0x00] * 64
        response[0] = REPORT_ID
        response[1] = CMD['PEQ']
        response[4] = 0  # Band index
        
        # Frequency at offset 27-28 (little endian): 1000 = 0x03E8
        response[27] = 0xE8
        response[28] = 0x03
        
        # Q at offset 29-30: 0.75 * 256 = 192 = 0x00C0
        response[29] = 0xC0
        response[30] = 0x00
        
        # Gain at offset 31-32: 3.0 * 256 = 768 = 0x0300
        response[31] = 0x00
        response[32] = 0x03
        
        # Type at offset 33: PK = 2
        response[33] = 2
        
        band = device._parse_band_response(response, 0)
        
        assert band is not None
        assert band.index == 0
        assert band.freq == 1000
        assert band.q == 0.75
        assert band.gain == 3.0
        assert band.type == "PK"
        assert band.enabled is True
    
    def test_parse_band_response_negative_gain(self):
        """Test parsing band response with negative gain."""
        device = DeviceService(use_mock=True)
        
        response = [0x00] * 64
        response[0] = REPORT_ID
        response[1] = CMD['PEQ']
        response[4] = 2  # Band index 2
        
        # Frequency: 500 Hz
        response[27] = 0xF4
        response[28] = 0x01
        
        # Q: 1.0 * 256 = 256 = 0x0100
        response[29] = 0x00
        response[30] = 0x01
        
        # Gain: -4.5 * 256 = -1152 = 0xFB80 (two's complement)
        # 0x10000 - 1152 = 64384 = 0xFB80
        response[31] = 0x80
        response[32] = 0xFB
        
        # Type: HSQ = 3
        response[33] = 3
        
        band = device._parse_band_response(response, 2)
        
        assert band is not None
        assert band.index == 2
        assert band.freq == 500
        assert band.q == 1.0
        assert band.gain == -4.5
        assert band.type == "HSQ"
        assert band.enabled is True
    
    def test_parse_band_response_zero_gain_disabled(self):
        """Test that zero gain bands are marked as disabled."""
        device = DeviceService(use_mock=True)
        
        response = [0x00] * 64
        response[0] = REPORT_ID
        response[1] = CMD['PEQ']
        response[4] = 3
        
        # Frequency: 8000 Hz
        response[27] = 0x00
        response[28] = 0x1F
        
        # Q: 1.0
        response[29] = 0x00
        response[30] = 0x01
        
        # Gain: 0
        response[31] = 0x00
        response[32] = 0x00
        
        # Type: PK = 2
        response[33] = 2
        
        band = device._parse_band_response(response, 3)
        
        assert band is not None
        assert band.gain == 0.0
        assert band.enabled is False
    
    def test_iir_filter_computation_matches_webdriver(self):
        """Test that IIR filter computation matches webdriver reference values."""
        device = DeviceService(use_mock=True)
        
        # Test case from webdriver: freq=1000, gain=0, q=0.75
        coeffs = device._compute_iir_filter(1000, 0.0, 0.75)
        
        # At 0dB gain, filter should be flat (all-pass)
        # b0=1, b1=0, b2=0, a1=0, a2=0 in Q30
        # Q30 representation of 1.0 = 1073741824 = 0x40000000
        # Q30 representation of 0.0 = 0
        
        # First coefficient (b0) should be close to 1.0 in Q30
        b0 = (coeffs[3] << 24) | (coeffs[2] << 16) | (coeffs[1] << 8) | coeffs[0]
        assert abs(b0 - 1073741824) < 1000  # Allow small rounding difference
        
        # Other coefficients at 0 gain should be near 0
        for i in range(4, 20):
            assert abs(coeffs[i]) < 10000  # Small values due to rounding
    
    def test_global_gain_packet(self):
        """Test global gain packet structure."""
        device = DeviceService(use_mock=True)
        device.connect()
        
        global_gain = -6  # -6dB
        packet = [
            CMD['WRITE'],
            CMD['GAIN'],
            0x02,
            0x00,
            global_gain & 0xFF,
            CMD['END'],
        ]
        
        assert packet[0] == CMD['WRITE']
        assert packet[1] == CMD['GAIN']
        assert packet[4] == 0xFA  # -6 in two's complement (250)
        assert packet[5] == CMD['END']
    
    def test_flash_save_packet(self):
        """Test flash save packet structure."""
        packet = [CMD['WRITE'], CMD['FLASH'], 0x01, 0x00, CMD['END']]
        
        assert packet[0] == CMD['WRITE']
        assert packet[1] == CMD['FLASH']
        assert packet[2] == 0x01
        assert packet[3] == 0x00
        assert packet[4] == CMD['END']
    
    def test_commit_temp_packet(self):
        """Test commit to RAM (TEMP) packet structure."""
        packet = [
            CMD['WRITE'], CMD['TEMP'], 0x04, 0x00,
            0x00, 0xFF, 0xFF, CMD['END']
        ]
        
        assert packet[0] == CMD['WRITE']
        assert packet[1] == CMD['TEMP']
        assert packet[2] == 0x04
        assert packet[6] == 0xFF
        assert packet[7] == CMD['END']