"""
Settings screen for the PEQ Configurator app.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.uix.spinner import Spinner
from kivy.properties import ObjectProperty
from kivy.metrics import dp
from kivy.logger import Logger


class SettingsScreen(Screen):
    """Settings screen for app preferences."""
    
    # Callbacks
    on_back = ObjectProperty(None)
    
    # UI Elements
    global_gain_slider = ObjectProperty(None)
    global_gain_label = ObjectProperty(None)
    auto_connect_switch = ObjectProperty(None)
    theme_spinner = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        """Build the settings screen UI."""
        main_layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        title = Label(
            text='Settings',
            font_size=dp(20),
            bold=True,
            halign='left'
        )
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        
        back_btn = Button(
            text='Back',
            size_hint_x=None,
            width=dp(80),
            size_hint_y=None,
            height=dp(40)
        )
        back_btn.bind(on_press=lambda x: self.on_back() if self.on_back else None)
        header.add_widget(back_btn)
        
        main_layout.add_widget(header)
        
        # Audio settings section
        audio_label = Label(
            text='Audio Settings',
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(30),
            halign='left'
        )
        audio_label.bind(size=audio_label.setter('text_size'))
        main_layout.add_widget(audio_label)
        
        # Global gain
        gain_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        gain_layout.add_widget(Label(text='Global Gain:', font_size=dp(16), size_hint_x=0.3))
        
        self.global_gain_slider = Slider(min=-12, max=12, value=0, step=0.5, size_hint_x=0.5)
        self.global_gain_slider.bind(value=self.on_global_gain_change)
        gain_layout.add_widget(self.global_gain_slider)
        
        self.global_gain_label = Label(text='0 dB', font_size=dp(16), size_hint_x=0.2)
        self.global_gain_label.bind(size=self.global_gain_label.setter('text_size'))
        gain_layout.add_widget(self.global_gain_label)
        
        main_layout.add_widget(gain_layout)
        
        # Device settings section
        device_label = Label(
            text='Device Settings',
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(30),
            halign='left'
        )
        device_label.bind(size=device_label.setter('text_size'))
        main_layout.add_widget(device_label)
        
        # Auto-connect
        auto_connect_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        auto_connect_layout.add_widget(Label(text='Auto-connect on startup:', font_size=dp(14), size_hint_x=0.7))
        
        self.auto_connect_switch = Switch(active=True, size_hint_x=0.3)
        auto_connect_layout.add_widget(self.auto_connect_switch)
        
        main_layout.add_widget(auto_connect_layout)
        
        # Theme (placeholder)
        theme_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        theme_layout.add_widget(Label(text='Theme:', font_size=dp(14), size_hint_x=0.3))
        
        self.theme_spinner = Spinner(
            text='System Default',
            values=('System Default', 'Light', 'Dark'),
            size_hint_x=0.7
        )
        theme_layout.add_widget(self.theme_spinner)
        
        main_layout.add_widget(theme_layout)
        
        # About section
        about_label = Label(
            text='About',
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(30),
            halign='left'
        )
        about_label.bind(size=about_label.setter('text_size'))
        main_layout.add_widget(about_label)
        
        version_label = Label(
            text='JM98 Max PEQ Configurator v1.0.0',
            font_size=dp(14),
            size_hint_y=None,
            height=dp(25),
            halign='left'
        )
        version_label.bind(size=version_label.setter('text_size'))
        main_layout.add_widget(version_label)
        
        device_info = Label(
            text='Compatible with Jcally JM98 Max USB-C DAC/AMP',
            font_size=dp(12),
            size_hint_y=None,
            height=dp(25),
            halign='left',
            color=(0.7, 0.7, 0.7, 1)
        )
        device_info.bind(size=device_info.setter('text_size'))
        main_layout.add_widget(device_info)
        
        self.add_widget(main_layout)
    
    def on_global_gain_change(self, slider, value):
        """Handle global gain slider change."""
        gain = round(value * 2) / 2
        self.global_gain_label.text = f'{gain:+.1f} dB'
    
    def load_settings(self, global_gain: float, auto_connect: bool = True):
        """Load current settings."""
        self.global_gain_slider.value = global_gain
        self.global_gain_label.text = f'{global_gain:+.1f} dB'
        self.auto_connect_switch.active = auto_connect
    
def get_settings(self) -> dict:
        """Get current settings as dictionary."""
        return {
            'global_gain': round(self.global_gain_slider.value * 2) / 2,
            'auto_connect': self.auto_connect_switch.active,
            'theme': self.theme_spinner.text
        }