"""
Unit tests for Device Service.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from services.device_service import DeviceService, MockDeviceService
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