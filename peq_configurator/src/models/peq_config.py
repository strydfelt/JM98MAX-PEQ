"""
PEQ Configuration data models.
Compatible with the existing webdriver implementation data structures.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from copy import deepcopy


@dataclass
class PEQBand:
    """Single PEQ band configuration."""
    index: int
    freq: float
    gain: float
    q: float
    type: str  # PK, LSQ, HSQ
    enabled: bool = True
    
    # Default frequency values matching the webdriver implementation
    DEFAULT_FREQS = [40, 100, 250, 500, 1000, 3000, 8000, 16000]
    DEFAULT_LABELS = [
        "Sub-Bass", "Bass", "Low-Mids", "Mids",
        "Mids", "High-Mids", "Presence", "Air"
    ]
    
    @classmethod
    def create_default(cls, index: int) -> 'PEQBand':
        """Create a default band for the given index."""
        return cls(
            index=index,
            freq=cls.DEFAULT_FREQS[index] if index < len(cls.DEFAULT_FREQS) else 1000,
            gain=0.0,
            q=0.75,
            type="PK",
            enabled=True
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PEQBand':
        """Create PEQBand from dictionary."""
        return cls(
            index=data.get('index', 0),
            freq=float(data.get('freq', 1000)),
            gain=float(data.get('gain', 0.0)),
            q=float(data.get('q', 0.75)),
            type=data.get('type', 'PK'),
            enabled=data.get('enabled', True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'index': self.index,
            'freq': self.freq,
            'gain': self.gain,
            'q': self.q,
            'type': self.type,
            'enabled': self.enabled
        }
    
    def copy(self) -> 'PEQBand':
        """Create a deep copy of this band."""
        return deepcopy(self)
    
    def get_label(self) -> str:
        """Get the display label for this band."""
        if self.index < len(self.DEFAULT_LABELS):
            return self.DEFAULT_LABELS[self.index]
        return f"Band {self.index + 1}"


@dataclass
class PEQConfiguration:
    """Complete PEQ configuration with 8 bands."""
    bands: List[PEQBand] = field(default_factory=list)
    
    NUM_BANDS = 8
    
    @classmethod
    def create_default(cls) -> 'PEQConfiguration':
        """Create a default configuration with all bands at default values."""
        bands = [PEQBand.create_default(i) for i in range(cls.NUM_BANDS)]
        return cls(bands=bands)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PEQConfiguration':
        """Create PEQConfiguration from dictionary."""
        bands = []
        for band_data in data.get('bands', []):
            bands.append(PEQBand.from_dict(band_data))
        
        # Ensure we have exactly NUM_BANDS bands
        while len(bands) < cls.NUM_BANDS:
            bands.append(PEQBand.create_default(len(bands)))
        
        return cls(bands=bands[:cls.NUM_BANDS])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'bands': [band.to_dict() for band in self.bands]
        }
    
    def copy(self) -> 'PEQConfiguration':
        """Create a deep copy of this configuration."""
        return deepcopy(self)
    
    def get_band(self, index: int) -> PEQBand:
        """Get band by index."""
        if 0 <= index < len(self.bands):
            return self.bands[index]
        return None
    
    def set_band(self, index: int, band: PEQBand) -> bool:
        """Set band at index."""
        if 0 <= index < len(self.bands):
            self.bands[index] = band
            return True
        return False