"""
Storage service for persisting PEQ configurations and user preferences.
Supports JSON and Equalizer APO Filter.txt formats.
"""
from kivy.logger import Logger
from kivy.utils import platform
import json
import os
import re
from datetime import datetime
from models.peq_config import PEQConfiguration, PEQBand


class StorageService:
    """Service for saving/loading PEQ configurations and settings."""
    
    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.config_file = os.path.join(self.config_dir, 'peq_config.json')
        self.global_gain_file = os.path.join(self.config_dir, 'global_gain.json')
        self.ensure_config_dir()
    
    def _get_config_dir(self) -> str:
        """Get the configuration directory path."""
        if platform == 'android':
            # On Android, use app-specific storage
            from android import mActivity  # type: ignore
            context = mActivity.getApplicationContext()
            files_dir = context.getFilesDir()
            return files_dir.getAbsolutePath()
        else:
            # On desktop, use local config directory
            home = os.path.expanduser('~')
            config_dir = os.path.join(home, '.peq_configurator')
            return config_dir
    
    def ensure_config_dir(self):
        """Ensure configuration directory exists."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            Logger.info(f"StorageService: Config directory: {self.config_dir}")
        except Exception as e:
            Logger.error(f"StorageService: Failed to create config directory: {e}")
    
    def save_config(self, config: PEQConfiguration) -> bool:
        """Save PEQ configuration to file (JSON format)."""
        try:
            data = config.to_dict()
            data['version'] = 1
            data['saved_at'] = self.get_timestamp()
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            Logger.info(f"StorageService: Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            Logger.error(f"StorageService: Failed to save config: {e}")
            return False
    
    def load_config(self) -> PEQConfiguration:
        """Load PEQ configuration from file (JSON format)."""
        try:
            if not os.path.exists(self.config_file):
                Logger.info("StorageService: No saved config found")
                return None
            
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            config = PEQConfiguration.from_dict(data)
            Logger.info(f"StorageService: Configuration loaded from {self.config_file}")
            return config
        except Exception as e:
            Logger.error(f"StorageService: Failed to load config: {e}")
            return None
    
    def save_global_gain(self, gain: float) -> bool:
        """Save global gain setting."""
        try:
            data = {
                'global_gain': gain,
                'saved_at': self.get_timestamp()
            }
            
            with open(self.global_gain_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            Logger.info(f"StorageService: Global gain saved: {gain} dB")
            return True
        except Exception as e:
            Logger.error(f"StorageService: Failed to save global gain: {e}")
            return False
    
    def load_global_gain(self) -> float:
        """Load global gain setting."""
        try:
            if not os.path.exists(self.global_gain_file):
                return 0.0
            
            with open(self.global_gain_file, 'r') as f:
                data = json.load(f)
            
            gain = data.get('global_gain', 0.0)
            Logger.info(f"StorageService: Global gain loaded: {gain} dB")
            return float(gain)
        except Exception as e:
            Logger.error(f"StorageService: Failed to load global gain: {e}")
            return 0.0
    
    def export_config(self, data: dict, filepath: str) -> bool:
        """Export configuration to specified file path (auto-detect format by extension)."""
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(filepath)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Determine format by extension
            _, ext = os.path.splitext(filepath)
            ext = ext.lower()
            
            if ext == '.txt':
                return self._export_filter_txt(data, filepath)
            else:
                # Default to JSON
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            
            Logger.info(f"StorageService: Configuration exported to {filepath}")
            return True
        except Exception as e:
            Logger.error(f"StorageService: Failed to export config: {e}")
            return False
    
    def _export_filter_txt(self, data: dict, filepath: str) -> bool:
        """Export configuration in Equalizer APO Filter.txt format."""
        try:
            bands = data.get('bands', [])
            global_gain = data.get('globalGain', 0)
            
            lines = []
            # Preamp line (global gain as preamp)
            lines.append(f"Preamp: {global_gain:+.1f} dB")
            
            # Filter lines
            for i, band in enumerate(bands):
                # Determine if band is enabled
                enabled = band.get('enabled', True)
                status = "ON" if enabled else "OFF"
                
                freq = band.get('freq', 1000)
                gain = band.get('gain', 0)
                q = band.get('q', 0.75)
                ftype = band.get('type', 'PK')
                
                # Map type to filter format (PK, LSQ, HSQ -> PK, LS, HS)
                filter_type = ftype
                if ftype == 'LSQ':
                    filter_type = 'LS'
                elif ftype == 'HSQ':
                    filter_type = 'HS'
                
                lines.append(f"Filter {i+1}: {status} {filter_type} Fc {int(freq)} Hz Gain {gain:+.1f} dB Q {q:.3f}")
            
            with open(filepath, 'w') as f:
                f.write('\n'.join(lines))
            
            Logger.info(f"StorageService: Configuration exported to Filter.txt format: {filepath}")
            return True
        except Exception as e:
            Logger.error(f"StorageService: Failed to export Filter.txt: {e}")
            return False
    
    def import_config(self, filepath: str) -> dict:
        """Import configuration from file (auto-detect format by extension)."""
        try:
            if not os.path.exists(filepath):
                Logger.error(f"StorageService: File not found: {filepath}")
                return None
            
            # Determine format by extension
            _, ext = os.path.splitext(filepath)
            ext = ext.lower()
            
            if ext == '.txt':
                return self._import_filter_txt(filepath)
            else:
                # Default to JSON
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Validate basic structure
                if 'bands' not in data:
                    Logger.error("StorageService: Invalid config file - missing 'bands'")
                    return None
                
                Logger.info(f"StorageService: Configuration imported from {filepath}")
                return data
        except json.JSONDecodeError as e:
            Logger.error(f"StorageService: Invalid JSON in config file: {e}")
            return None
        except Exception as e:
            Logger.error(f"StorageService: Failed to import config: {e}")
            return None
    
    def _import_filter_txt(self, filepath: str) -> dict:
        """Import configuration from Equalizer APO Filter.txt format."""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            bands = []
            global_gain = 0.0
            
            # Regex patterns
            preamp_pattern = re.compile(r'Preamp:\s*([+-]?\d+\.?\d*)\s*dB', re.IGNORECASE)
            filter_pattern = re.compile(
                r'Filter\s+(\d+):\s*(ON|OFF)\s+(PK|LS|HS|LSQ|HSQ)\s+Fc\s+(\d+\.?\d*)\s*Hz\s+Gain\s+([+-]?\d+\.?\d*)\s*dB\s+Q\s+(\d+\.?\d*)',
                re.IGNORECASE
            )
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Check for preamp
                preamp_match = preamp_pattern.match(line)
                if preamp_match:
                    global_gain = float(preamp_match.group(1))
                    continue
                
                # Check for filter
                filter_match = filter_pattern.match(line)
                if filter_match:
                    filter_num = int(filter_match.group(1))
                    status = filter_match.group(2).upper()
                    ftype = filter_match.group(3).upper()
                    freq = float(filter_match.group(4))
                    gain = float(filter_match.group(5))
                    q = float(filter_match.group(6))
                    
                    # Map filter type back to internal format
                    if ftype == 'LS':
                        ftype = 'LSQ'
                    elif ftype == 'HS':
                        ftype = 'HSQ'
                    elif ftype == 'PK':
                        ftype = 'PK'
                    
                    enabled = status == 'ON'
                    
                    band = {
                        'index': filter_num - 1,
                        'freq': freq,
                        'gain': gain,
                        'q': q,
                        'type': ftype,
                        'enabled': enabled
                    }
                    bands.append(band)
            
            # Sort by index to ensure correct order
            bands.sort(key=lambda b: b['index'])
            
            # Ensure we have at least the default number of bands (8)
            while len(bands) < 8:
                idx = len(bands)
                bands.append({
                    'index': idx,
                    'freq': PEQBand.DEFAULT_FREQS[idx] if idx < len(PEQBand.DEFAULT_FREQS) else 1000,
                    'gain': 0.0,
                    'q': 0.75,
                    'type': 'PK',
                    'enabled': True
                })
            
            data = {
                'device': 'JM98MAX',
                'timestamp': self.get_timestamp(),
                'globalGain': global_gain,
                'bands': bands[:8]  # Limit to 8 bands
            }
            
            Logger.info(f"StorageService: Configuration imported from Filter.txt format: {filepath}")
            return data
        except Exception as e:
            Logger.error(f"StorageService: Failed to import Filter.txt: {e}")
            return None
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()
    
    def list_exports(self) -> list:
        """List exported configuration files."""
        try:
            if not os.path.exists(self.config_dir):
                return []
            
            files = []
            for fname in os.listdir(self.config_dir):
                if (fname.endswith('.json') or fname.endswith('.txt')) and fname not in ['peq_config.json', 'global_gain.json']:
                    fpath = os.path.join(self.config_dir, fname)
                    stat = os.stat(fpath)
                    files.append({
                        'name': fname,
                        'path': fpath,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return sorted(files, key=lambda x: x['modified'], reverse=True)
        except Exception as e:
            Logger.error(f"StorageService: Failed to list exports: {e}")
            return []


# For the Filter.txt import, we need PEQBand.DEFAULT_FREQS
from models.peq_config import PEQBand