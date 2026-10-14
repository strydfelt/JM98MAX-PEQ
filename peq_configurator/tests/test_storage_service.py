"""
Unit tests for Storage Service.
"""
import sys
import os
import tempfile
import json
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from services.storage_service import StorageService
from models.peq_config import PEQConfiguration, PEQBand


class TestStorageService:
    """Tests for StorageService."""
    
    @pytest.fixture
    def storage(self):
        """Set up test environment with temporary directory."""
        temp_dir = tempfile.mkdtemp()
        storage = StorageService()
        # Override config dir for testing
        storage.config_dir = temp_dir
        storage.config_file = os.path.join(temp_dir, 'peq_config.json')
        storage.global_gain_file = os.path.join(temp_dir, 'global_gain.json')
        yield storage
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_save_and_load_config(self, storage):
        """Test saving and loading PEQ configuration."""
        config = PEQConfiguration.create_default()
        config.bands[0].gain = 3.5
        config.bands[1].gain = -2.0
        config.bands[2].type = "LSQ"
        
        # Save
        result = storage.save_config(config)
        assert result is True
        assert os.path.exists(storage.config_file)
        
        # Load
        loaded = storage.load_config()
        assert loaded is not None
        assert len(loaded.bands) == 8
        assert loaded.bands[0].gain == 3.5
        assert loaded.bands[1].gain == -2.0
        assert loaded.bands[2].type == "LSQ"
    
    def test_load_nonexistent_config(self, storage):
        """Test loading config when file doesn't exist."""
        loaded = storage.load_config()
        assert loaded is None
    
    def test_save_and_load_global_gain(self, storage):
        """Test saving and loading global gain."""
        gain = -4.5
        result = storage.save_global_gain(gain)
        assert result is True
        
        loaded = storage.load_global_gain()
        assert loaded == -4.5
    
    def test_load_global_gain_default(self, storage):
        """Test loading global gain when file doesn't exist."""
        loaded = storage.load_global_gain()
        assert loaded == 0.0
    
    def test_export_json(self, storage):
        """Test exporting configuration as JSON."""
        data = {
            'device': 'JM98MAX',
            'timestamp': '2024-01-01T00:00:00',
            'globalGain': -3.0,
            'bands': [
                {'index': 0, 'freq': 40, 'gain': 2.0, 'q': 1.0, 'type': 'PK', 'enabled': True},
                {'index': 1, 'freq': 100, 'gain': -1.0, 'q': 0.5, 'type': 'PK', 'enabled': True},
            ]
        }
        
        filepath = os.path.join(storage.config_dir, 'export_test.json')
        result = storage.export_config(data, filepath)
        assert result is True
        assert os.path.exists(filepath)
        
        # Verify content
        with open(filepath, 'r') as f:
            loaded = json.load(f)
        assert loaded['globalGain'] == -3.0
        assert len(loaded['bands']) == 2
    
    def test_export_filter_txt(self, storage):
        """Test exporting configuration as Filter.txt (Equalizer APO format)."""
        data = {
            'globalGain': -5.4,
            'bands': [
                {'index': 0, 'freq': 20, 'gain': -0.9, 'q': 2.0, 'type': 'PK', 'enabled': True},
                {'index': 1, 'freq': 29, 'gain': -2.5, 'q': 0.5, 'type': 'PK', 'enabled': True},
                {'index': 2, 'freq': 41, 'gain': 0.5, 'q': 1.4, 'type': 'PK', 'enabled': True},
                {'index': 3, 'freq': 120, 'gain': -1.7, 'q': 1.4, 'type': 'PK', 'enabled': True},
            ]
        }
        
        filepath = os.path.join(storage.config_dir, 'export_test.txt')
        result = storage.export_config(data, filepath)
        assert result is True
        assert os.path.exists(filepath)
        
        # Verify content
        with open(filepath, 'r') as f:
            content = f.read()
        
        lines = content.strip().split('\n')
        assert lines[0] == "Preamp: -5.4 dB"
        assert lines[1] == "Filter 1: ON PK Fc 20 Hz Gain -0.9 dB Q 2.000"
        assert lines[2] == "Filter 2: ON PK Fc 29 Hz Gain -2.5 dB Q 0.500"
        assert lines[3] == "Filter 3: ON PK Fc 41 Hz Gain +0.5 dB Q 1.400"
        assert lines[4] == "Filter 4: ON PK Fc 120 Hz Gain -1.7 dB Q 1.400"
    
    def test_export_filter_txt_with_disabled_band(self, storage):
        """Test exporting with disabled bands."""
        data = {
            'globalGain': 0.0,
            'bands': [
                {'index': 0, 'freq': 40, 'gain': 2.0, 'q': 1.0, 'type': 'PK', 'enabled': True},
                {'index': 1, 'freq': 100, 'gain': -1.0, 'q': 0.5, 'type': 'PK', 'enabled': False},
            ]
        }
        
        filepath = os.path.join(storage.config_dir, 'export_disabled.txt')
        result = storage.export_config(data, filepath)
        assert result is True
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        lines = content.strip().split('\n')
        assert "Filter 1: ON PK" in lines[1]
        assert "Filter 2: OFF PK" in lines[2]
    
    def test_import_json(self, storage):
        """Test importing configuration from JSON."""
        data = {
            'device': 'JM98MAX',
            'timestamp': '2024-01-01T00:00:00',
            'globalGain': -2.0,
            'bands': [
                {'index': 0, 'freq': 40, 'gain': 1.5, 'q': 1.0, 'type': 'PK', 'enabled': True},
                {'index': 1, 'freq': 100, 'gain': -0.5, 'q': 0.8, 'type': 'LSQ', 'enabled': True},
            ]
        }
        
        filepath = os.path.join(storage.config_dir, 'import_test.json')
        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        loaded = storage.import_config(filepath)
        assert loaded is not None
        assert loaded['globalGain'] == -2.0
        assert len(loaded['bands']) == 2
        assert loaded['bands'][0]['gain'] == 1.5
        assert loaded['bands'][1]['type'] == 'LSQ'
    
    def test_import_filter_txt(self, storage):
        """Test importing configuration from Filter.txt format."""
        filter_content = """Preamp: -5.4 dB
Filter 1: ON PK Fc 20 Hz Gain -0.9 dB Q 2.000
Filter 2: ON PK Fc 29 Hz Gain -2.5 dB Q 0.500
Filter 3: ON PK Fc 41 Hz Gain 0.5 dB Q 1.400
Filter 4: ON PK Fc 120 Hz Gain -1.7 dB Q 1.400
Filter 5: ON PK Fc 450 Hz Gain 1.9 dB Q 0.800
Filter 6: ON PK Fc 1700 Hz Gain -2.0 dB Q 2.000
Filter 7: ON PK Fc 4900 Hz Gain 2.5 dB Q 1.100
Filter 8: ON PK Fc 8000 Hz Gain -7.1 dB Q 1.400
"""
        
        filepath = os.path.join(storage.config_dir, 'import_test.txt')
        with open(filepath, 'w') as f:
            f.write(filter_content)
        
        loaded = storage.import_config(filepath)
        assert loaded is not None
        assert loaded['globalGain'] == -5.4
        assert len(loaded['bands']) == 8
        assert loaded['bands'][0]['freq'] == 20
        assert loaded['bands'][0]['gain'] == -0.9
        assert loaded['bands'][0]['q'] == 2.0
        assert loaded['bands'][0]['type'] == 'PK'
        assert loaded['bands'][0]['enabled'] is True
    
    def test_import_filter_txt_with_off_bands(self, storage):
        """Test importing Filter.txt with disabled bands."""
        filter_content = """Preamp: 0 dB
Filter 1: ON PK Fc 40 Hz Gain 2.0 dB Q 1.000
Filter 2: OFF PK Fc 100 Hz Gain -1.0 dB Q 0.500
"""
        
        filepath = os.path.join(storage.config_dir, 'import_off.txt')
        with open(filepath, 'w') as f:
            f.write(filter_content)
        
        loaded = storage.import_config(filepath)
        assert loaded is not None
        assert len(loaded['bands']) == 8  # Padded to 8
        assert loaded['bands'][0]['enabled'] is True
        assert loaded['bands'][1]['enabled'] is False
    
    def test_import_filter_txt_with_ls_hs_types(self, storage):
        """Test importing Filter.txt with LS and HS filter types."""
        filter_content = """Preamp: 0 dB
Filter 1: ON LS Fc 100 Hz Gain 3.0 dB Q 0.707
Filter 2: ON HS Fc 8000 Hz Gain -2.0 dB Q 0.707
"""
        
        filepath = os.path.join(storage.config_dir, 'import_ls_hs.txt')
        with open(filepath, 'w') as f:
            f.write(filter_content)
        
        loaded = storage.import_config(filepath)
        assert loaded is not None
        assert loaded['bands'][0]['type'] == 'LSQ'  # LS -> LSQ
        assert loaded['bands'][1]['type'] == 'HSQ'  # HS -> HSQ
    
    def test_import_invalid_json(self, storage):
        """Test importing invalid JSON file."""
        filepath = os.path.join(storage.config_dir, 'invalid.json')
        with open(filepath, 'w') as f:
            f.write("{ invalid json }")
        
        loaded = storage.import_config(filepath)
        assert loaded is None
    
    def test_import_nonexistent_file(self, storage):
        """Test importing nonexistent file."""
        loaded = storage.import_config(os.path.join(storage.config_dir, 'nonexistent.json'))
        assert loaded is None
    
    def test_import_missing_bands(self, storage):
        """Test importing JSON without bands."""
        data = {'device': 'JM98MAX', 'globalGain': 0}
        filepath = os.path.join(storage.config_dir, 'no_bands.json')
        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        loaded = storage.import_config(filepath)
        assert loaded is None
    
    def test_list_exports(self, storage):
        """Test listing exported files."""
        # Create some test files
        for name in ['test1.json', 'test2.txt', 'peq_config.json', 'global_gain.json', 'readme.md']:
            with open(os.path.join(storage.config_dir, name), 'w') as f:
                f.write('test')
        
        exports = storage.list_exports()
        # Should only include .json and .txt, not the internal files or .md
        names = [e['name'] for e in exports]
        assert 'test1.json' in names
        assert 'test2.txt' in names
        assert 'peq_config.json' not in names
        assert 'global_gain.json' not in names
        assert 'readme.md' not in names
    
    def test_get_timestamp(self, storage):
        """Test timestamp generation."""
        ts = storage.get_timestamp()
        assert isinstance(ts, str)
        # Should be ISO format
        assert 'T' in ts