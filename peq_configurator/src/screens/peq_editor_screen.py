"""
PEQ Editor screen for editing PEQ band parameters.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.properties import ObjectProperty, ListProperty
from kivy.metrics import dp
from kivy.logger import Logger

from models.peq_config import PEQConfiguration, PEQBand


class PEQBandEditor(BoxLayout):
    """Editor for a single PEQ band."""
    
    def __init__(self, band: PEQBand, on_change_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(180)
        self.padding = dp(10)
        self.spacing = dp(5)
        
        self.band = band
        self.on_change_callback = on_change_callback
        
        self.build_ui()
    
    def build_ui(self):
        """Build the band editor UI."""
        # Header with band number and label
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
        
        label = Label(
            text=f'Band {self.band.index + 1}: {self.band.get_label()}',
            font_size=dp(16),
            bold=True,
            halign='left'
        )
        label.bind(size=label.setter('text_size'))
        header.add_widget(label)
        
        # Enabled checkbox
        self.enabled_checkbox = CheckBox(active=self.band.enabled, size_hint_x=None, width=dp(50))
        self.enabled_checkbox.bind(active=self.on_enabled_change)
        header.add_widget(Label(text='Enabled', size_hint_x=None, width=dp(60)))
        header.add_widget(self.enabled_checkbox)
        
        self.add_widget(header)
        
        # Frequency
        freq_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=dp(10))
        freq_layout.add_widget(Label(text='Freq (Hz):', size_hint_x=0.25))
        
        self.freq_slider = Slider(
            min=20, max=20000, value=self.band.freq,
            size_hint_x=0.5
        )
        self.freq_slider.bind(value=self.on_freq_change)
        freq_layout.add_widget(self.freq_slider)
        
        self.freq_input = TextInput(
            text=str(int(self.band.freq)),
            multiline=False,
            input_filter='int',
            size_hint_x=0.25
        )
        self.freq_input.bind(text=self.on_freq_input_change)
        freq_layout.add_widget(self.freq_input)
        
        self.add_widget(freq_layout)
        
        # Gain
        gain_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=dp(10))
        gain_layout.add_widget(Label(text='Gain (dB):', size_hint_x=0.25))
        
        self.gain_slider = Slider(
            min=-12, max=12, value=self.band.gain, step=0.5,
            size_hint_x=0.5
        )
        self.gain_slider.bind(value=self.on_gain_change)
        gain_layout.add_widget(self.gain_slider)
        
        self.gain_input = TextInput(
            text=str(self.band.gain),
            multiline=False,
            input_filter='float',
            size_hint_x=0.25
        )
        self.gain_input.bind(text=self.on_gain_input_change)
        gain_layout.add_widget(self.gain_input)
        
        self.add_widget(gain_layout)
        
        # Q Factor
        q_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=dp(10))
        q_layout.add_widget(Label(text='Q Factor:', size_hint_x=0.25))
        
        self.q_slider = Slider(
            min=0.1, max=10, value=self.band.q, step=0.05,
            size_hint_x=0.5
        )
        self.q_slider.bind(value=self.on_q_change)
        q_layout.add_widget(self.q_slider)
        
        self.q_input = TextInput(
            text=str(self.band.q),
            multiline=False,
            input_filter='float',
            size_hint_x=0.25
        )
        self.q_input.bind(text=self.on_q_input_change)
        q_layout.add_widget(self.q_input)
        
        self.add_widget(q_layout)
        
        # Type
        type_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=dp(10))
        type_layout.add_widget(Label(text='Type:', size_hint_x=0.25))
        
        self.type_spinner = Spinner(
            text=self.band.type,
            values=('PK', 'LSQ', 'HSQ'),
            size_hint_x=0.75
        )
        self.type_spinner.bind(text=self.on_type_change)
        type_layout.add_widget(self.type_spinner)
        
        self.add_widget(type_layout)
    
    def on_enabled_change(self, checkbox, value):
        """Handle enabled checkbox change."""
        self.band.enabled = value
        if self.on_change_callback:
            self.on_change_callback(self.band)
    
    def on_freq_change(self, slider, value):
        """Handle frequency slider change."""
        self.band.freq = value
        self.freq_input.text = str(int(value))
        if self.on_change_callback:
            self.on_change_callback(self.band)
    
    def on_freq_input_change(self, input_widget, text):
        """Handle frequency text input change."""
        try:
            value = int(text)
            if 20 <= value <= 20000:
                self.band.freq = value
                self.freq_slider.value = value
                if self.on_change_callback:
                    self.on_change_callback(self.band)
        except ValueError:
            pass
    
    def on_gain_change(self, slider, value):
        """Handle gain slider change."""
        self.band.gain = round(value * 2) / 2  # Round to 0.5
        self.gain_input.text = str(self.band.gain)
        if self.on_change_callback:
            self.on_change_callback(self.band)
    
    def on_gain_input_change(self, input_widget, text):
        """Handle gain text input change."""
        try:
            value = float(text)
            if -12 <= value <= 12:
                self.band.gain = round(value * 2) / 2
                self.gain_slider.value = self.band.gain
                self.gain_input.text = str(self.band.gain)
                if self.on_change_callback:
                    self.on_change_callback(self.band)
        except ValueError:
            pass
    
    def on_q_change(self, slider, value):
        """Handle Q factor slider change."""
        self.band.q = round(value * 20) / 20  # Round to 0.05
        self.q_input.text = str(self.band.q)
        if self.on_change_callback:
            self.on_change_callback(self.band)
    
    def on_q_input_change(self, input_widget, text):
        """Handle Q factor text input change."""
        try:
            value = float(text)
            if 0.1 <= value <= 10:
                self.band.q = round(value * 20) / 20
                self.q_slider.value = self.band.q
                self.q_input.text = str(self.band.q)
                if self.on_change_callback:
                    self.on_change_callback(self.band)
        except ValueError:
            pass
    
    def on_type_change(self, spinner, text):
        """Handle type spinner change."""
        self.band.type = text
        if self.on_change_callback:
            self.on_change_callback(self.band)
    
    def get_band(self) -> PEQBand:
        """Get the current band configuration."""
        return self.band


class PEQEditorScreen(Screen):
    """Screen for editing PEQ parameters."""
    
    # Callbacks
    on_save = ObjectProperty(None)
    on_cancel = ObjectProperty(None)
    on_reset = ObjectProperty(None)
    
    # UI Elements
    bands_container = ObjectProperty(None)
    global_gain_slider = ObjectProperty(None)
    global_gain_label = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.band_editors = []
        self.config = None
        self.build_ui()
    
    def build_ui(self):
        """Build the PEQ editor screen UI."""
        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        title = Label(
            text='Edit PEQ Parameters',
            font_size=dp(20),
            bold=True,
            halign='left'
        )
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        main_layout.add_widget(header)
        
        # Global gain
        gain_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        gain_layout.add_widget(Label(text='Global Gain:', font_size=dp(16), size_hint_x=0.25))
        
        self.global_gain_slider = Slider(min=-12, max=12, value=0, step=0.5, size_hint_x=0.5)
        self.global_gain_slider.bind(value=self.on_global_gain_change)
        gain_layout.add_widget(self.global_gain_slider)
        
        self.global_gain_label = Label(text='0 dB', font_size=dp(16), size_hint_x=0.25)
        self.global_gain_label.bind(size=self.global_gain_label.setter('text_size'))
        gain_layout.add_widget(self.global_gain_label)
        
        main_layout.add_widget(gain_layout)
        
        # Bands list
        bands_label = Label(
            text='PEQ Bands (8 bands)',
            font_size=dp(14),
            bold=True,
            size_hint_y=None,
            height=dp(30),
            halign='left'
        )
        bands_label.bind(size=bands_label.setter('text_size'))
        main_layout.add_widget(bands_label)
        
        # Scrollable bands
        scroll = ScrollView()
        self.bands_container = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(8)
        )
        self.bands_container.bind(minimum_height=self.bands_container.setter('height'))
        scroll.add_widget(self.bands_container)
        main_layout.add_widget(scroll)
        
        # Action buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        
        reset_btn = Button(text='Reset to Defaults', background_color=(0.8, 0.4, 0.4, 1))
        reset_btn.bind(on_press=lambda x: self.on_reset() if self.on_reset else None)
        btn_layout.add_widget(reset_btn)
        
        cancel_btn = Button(text='Cancel', background_color=(0.6, 0.6, 0.6, 1))
        cancel_btn.bind(on_press=lambda x: self.on_cancel() if self.on_cancel else None)
        btn_layout.add_widget(cancel_btn)
        
        save_btn = Button(text='Save', background_color=(0.3, 0.7, 0.3, 1))
        save_btn.bind(on_press=self.on_save_pressed)
        btn_layout.add_widget(save_btn)
        
        main_layout.add_widget(btn_layout)
        
        self.add_widget(main_layout)
    
    def load_config(self, config: PEQConfiguration):
        """Load configuration into editors."""
        self.config = config
        self.bands_container.clear_widgets()
        self.band_editors = []
        
        for band in config.bands:
            # Create a copy for editing
            band_copy = band.copy()
            editor = PEQBandEditor(band_copy, on_change_callback=self.on_band_change)
            self.band_editors.append(editor)
            self.bands_container.add_widget(editor)
        
        # Update global gain if available
        # This would come from the app
    
    def on_global_gain_change(self, slider, value):
        """Handle global gain slider change."""
        gain = round(value * 2) / 2
        self.global_gain_label.text = f'{gain:+.1f} dB'
    
    def on_band_change(self, band):
        """Handle band parameter change."""
        # Validation is done in real-time via the editors
        pass
    
    def on_save_pressed(self, button):
        """Handle save button press."""
        if self.on_save and self.config:
            # Collect edited bands
            edited_bands = [editor.get_band() for editor in self.band_editors]
            
            # Get global gain
            global_gain = round(self.global_gain_slider.value * 2) / 2
            
            # Create new config with edited bands
            new_config = PEQConfiguration(bands=edited_bands)
            
            self.on_save(new_config)
    
    def validate_config(self) -> tuple:
        """Validate the current configuration."""
        errors = []
        
        for editor in self.band_editors:
            band = editor.band
            if band.freq < 20 or band.freq > 20000:
                errors.append(f'Band {band.index + 1}: Frequency out of range (20-20000 Hz)')
            if band.gain < -12 or band.gain > 12:
                errors.append(f'Band {band.index + 1}: Gain out of range (-12 to +12 dB)')
            if band.q < 0.1 or band.q > 10:
                errors.append(f'Band {band.index + 1}: Q factor out of range (0.1-10)')
        
        return len(errors) == 0, errors