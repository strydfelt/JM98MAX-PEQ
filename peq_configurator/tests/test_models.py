"""
Unit tests for PEQ Configuration models.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from models.peq_config import PEQBand, PEQConfiguration


class TestPEQBand:
    """Tests for PEQBand model."""
    
    def test_create_default(self):
        """Test creating a default band."""
        band = PEQBand.create_default(0)
        assert band.index == 0
        assert band.freq == 40
        assert band.gain == 0.0
        assert band.q == 0.75
        assert band.type == "PK"
        assert band.enabled is True
    
    @pytest.mark.parametrize("index,expected_freq", [
        (0, 40), (1, 100), (2, 250), (3, 500),
        (4, 1000), (5, 3000), (6, 8000), (7, 16000),
    ])
    def test_create_default_all_indices(self, index, expected_freq):
        """Test creating default bands for all 8 indices."""
        band = PEQBand.create_default(index)
        assert band.index == index
        assert band.freq == expected_freq
        assert band.get_label() == PEQBand.DEFAULT_LABELS[index]
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        band = PEQBand(index=2, freq=250, gain=3.5, q=1.2, type="LSQ", enabled=False)
        data = band.to_dict()
        assert data['index'] == 2
        assert data['freq'] == 250
        assert data['gain'] == 3.5
        assert data['q'] == 1.2
        assert data['type'] == "LSQ"
        assert data['enabled'] is False
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {'index': 3, 'freq': 500, 'gain': -2.0, 'q': 0.8, 'type': 'HSQ', 'enabled': True}
        band = PEQBand.from_dict(data)
        assert band.index == 3
        assert band.freq == 500
        assert band.gain == -2.0
        assert band.q == 0.8
        assert band.type == "HSQ"
        assert band.enabled is True
    
    def test_copy(self):
        """Test deep copy."""
        band = PEQBand(index=1, freq=100, gain=1.5, q=1.0, type="PK", enabled=True)
        band_copy = band.copy()
        assert band.index == band_copy.index
        assert band.freq == band_copy.freq
        assert band.gain == band_copy.gain
        assert band.q == band_copy.q
        assert band.type == band_copy.type
        assert band.enabled == band_copy.enabled
        # Ensure it's a different object
        assert band is not band_copy
    
    def test_get_label(self):
        """Test getting band label."""
        band = PEQBand.create_default(0)
        assert band.get_label() == "Sub-Bass"
        band = PEQBand.create_default(7)
        assert band.get_label() == "Air"
        # Out of range
        band = PEQBand(index=10, freq=1000, gain=0, q=1, type="PK")
        assert band.get_label() == "Band 11"


class TestPEQConfiguration:
    """Tests for PEQConfiguration model."""
    
    def test_create_default(self):
        """Test creating default configuration."""
        config = PEQConfiguration.create_default()
        assert len(config.bands) == 8
        for i, band in enumerate(config.bands):
            assert band.index == i
            assert band.freq == PEQBand.DEFAULT_FREQS[i]
            assert band.gain == 0.0
            assert band.q == 0.75
            assert band.type == "PK"
            assert band.enabled is True
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = PEQConfiguration.create_default()
        config.bands[0].gain = 3.0
        data = config.to_dict()
        assert 'bands' in data
        assert len(data['bands']) == 8
        assert data['bands'][0]['gain'] == 3.0
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'bands': [
                {'index': 0, 'freq': 40, 'gain': 2.0, 'q': 1.0, 'type': 'PK', 'enabled': True},
                {'index': 1, 'freq': 100, 'gain': -1.0, 'q': 0.5, 'type': 'LSQ', 'enabled': False},
            ]
        }
        config = PEQConfiguration.from_dict(data)
        assert len(config.bands) == 8  # Should pad to 8 bands
        assert config.bands[0].gain == 2.0
        assert config.bands[1].gain == -1.0
        assert config.bands[1].type == "LSQ"
        assert config.bands[1].enabled is False
        # Default bands for remaining
        assert config.bands[2].gain == 0.0
    
    def test_from_dict_more_than_8_bands(self):
        """Test that extra bands are truncated."""
        bands = [{'index': i, 'freq': 1000, 'gain': 0, 'q': 1, 'type': 'PK', 'enabled': True} for i in range(10)]
        data = {'bands': bands}
        config = PEQConfiguration.from_dict(data)
        assert len(config.bands) == 8
    
    def test_copy(self):
        """Test deep copy of configuration."""
        config = PEQConfiguration.create_default()
        config.bands[0].gain = 5.0
        config_copy = config.copy()
        assert config_copy.bands[0].gain == 5.0
        # Modify original, copy should be unaffected
        config.bands[0].gain = 10.0
        assert config_copy.bands[0].gain == 5.0
    
    def test_get_band(self):
        """Test getting band by index."""
        config = PEQConfiguration.create_default()
        band = config.get_band(3)
        assert band.index == 3
        assert band.freq == 500
        # Out of range
        assert config.get_band(-1) is None
        assert config.get_band(10) is None
    
    def test_set_band(self):
        """Test setting band by index."""
        config = PEQConfiguration.create_default()
        new_band = PEQBand(index=2, freq=300, gain=2.0, q=1.5, type="HSQ", enabled=False)
        result = config.set_band(2, new_band)
        assert result is True
        assert config.bands[2].freq == 300
        assert config.bands[2].type == "HSQ"
        # Out of range
        assert config.set_band(-1, new_band) is False
        assert config.set_band(10, new_band) is False