"""
Main screen for the PEQ Configurator app.
Shows connection status, current config overview, and navigation.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, ListProperty
from kivy.metrics import dp
from kivy.logger import Logger


class MainScreen(Screen):
    """Main screen showing overview and navigation."""
    
    # Callbacks
    on_peq_editor = ObjectProperty(None)
    on_trial = ObjectProperty(None)
    on_export_import = ObjectProperty(None)
    on_settings = ObjectProperty(None)
    on_connect = ObjectProperty(None)
    
    # UI Elements
    connection_status_label = ObjectProperty(None)
    connect_button = ObjectProperty(None)
    config_container = ObjectProperty(None)
    global_gain_label = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        """Build the main screen UI."""
        main_layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        title = Label(
            text='JM98 Max PEQ Configurator',
            font_size=dp(20),
            bold=True,
            halign='left',
            valign='middle',
            size_hint_x=0.7
        )
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        
        # Connection status
        self.connection_status_label = Label(
            text='Disconnected',
            font_size=dp(14),
            color=(1, 0.5, 0.5, 1),  # Red for disconnected
            halign='right',
            valign='middle',
            size_hint_x=0.3
        )
        self.connection_status_label.bind(size=self.connection_status_label.setter('text_size'))
        header.add_widget(self.connection_status_label)
        main_layout.add_widget(header)
        
        # Connect button
        self.connect_button = Button(
            text='Connect to JM98 Max',
            size_hint_y=None,
            height=dp(48),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.connect_button.bind(on_press=lambda x: self.on_connect() if self.on_connect else None)
        main_layout.add_widget(self.connect_button)
        
        # Global gain display
        gain_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        gain_layout.add_widget(Label(text='Global Gain:', font_size=dp(16), size_hint_x=0.4))
        self.global_gain_label = Label(text='0 dB', font_size=dp(16), bold=True, halign='left')
        self.global_gain_label.bind(size=self.global_gain_label.setter('text_size'))
        gain_layout.add_widget(self.global_gain_label)
        main_layout.add_widget(gain_layout)
        
        # Current config overview
        config_label = Label(
            text='Current PEQ Configuration',
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(30),
            halign='left'
        )
        config_label.bind(size=config_label.setter('text_size'))
        main_layout.add_widget(config_label)
        
        # Scrollable config display
        scroll = ScrollView()
        self.config_container = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(8)
        )
        self.config_container.bind(minimum_height=self.config_container.setter('height'))
        scroll.add_widget(self.config_container)
        main_layout.add_widget(scroll)
        
        # Navigation buttons
        nav_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(200))
        
        peq_btn = Button(
            text='Edit PEQ Parameters',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.3, 0.7, 0.3, 1)
        )
        peq_btn.bind(on_press=lambda x: self.on_peq_editor() if self.on_peq_editor else None)
        nav_layout.add_widget(peq_btn)
        
        trial_btn = Button(
            text='Trial PEQ Settings',
            size_hint_y=None,
            height=dp(50),
            background_color=(1, 0.6, 0.2, 1)
        )
        trial_btn.bind(on_press=lambda x: self.on_trial() if self.on_trial else None)
        nav_layout.add_widget(trial_btn)
        
        export_btn = Button(
            text='Export / Import Config',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.6, 0.4, 0.8, 1)
        )
        export_btn.bind(on_press=lambda x: self.on_export_import() if self.on_export_import else None)
        nav_layout.add_widget(export_btn)
        
        settings_btn = Button(
            text='Settings',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        settings_btn.bind(on_press=lambda x: self.on_settings() if self.on_settings else None)
        nav_layout.add_widget(settings_btn)
        
        main_layout.add_widget(nav_layout)
        
        self.add_widget(main_layout)
    
    def update_connection_status(self, connected: bool):
        """Update connection status display."""
        if connected:
            self.connection_status_label.text = 'Connected'
            self.connection_status_label.color = (0.3, 0.8, 0.3, 1)  # Green
            self.connect_button.text = 'Disconnect'
            self.connect_button.background_color = (0.8, 0.3, 0.3, 1)
        else:
            self.connection_status_label.text = 'Disconnected'
            self.connection_status_label.color = (1, 0.5, 0.5, 1)  # Red
            self.connect_button.text = 'Connect to JM98 Max'
            self.connect_button.background_color = (0.2, 0.6, 1, 1)
    
    def update_config_display(self, config):
        """Update the configuration display."""
        self.config_container.clear_widgets()
        
        for band in config.bands:
            band_layout = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(30),
                spacing=dp(5)
            )
            
            # Band number and label
            label = Label(
                text=f'{band.index + 1}. {band.get_label()}',
                font_size=dp(12),
                size_hint_x=0.35,
                halign='left'
            )
            label.bind(size=label.setter('text_size'))
            band_layout.add_widget(label)
            
            # Frequency
            freq_label = Label(
                text=f'{int(band.freq)} Hz',
                font_size=dp(12),
                size_hint_x=0.2,
                halign='center'
            )
            freq_label.bind(size=freq_label.setter('text_size'))
            band_layout.add_widget(freq_label)
            
            # Gain
            gain_color = (0.3, 0.8, 0.3, 1) if band.gain >= 0 else (0.8, 0.3, 0.3, 1)
            gain_label = Label(
                text=f'{band.gain:+.1f} dB',
                font_size=dp(12),
                size_hint_x=0.15,
                halign='center',
                color=gain_color
            )
            gain_label.bind(size=gain_label.setter('text_size'))
            band_layout.add_widget(gain_label)
            
            # Q
            q_label = Label(
                text=f'Q:{band.q:.2f}',
                font_size=dp(12),
                size_hint_x=0.15,
                halign='center'
            )
            q_label.bind(size=q_label.setter('text_size'))
            band_layout.add_widget(q_label)
            
            # Type
            type_label = Label(
                text=band.type,
                font_size=dp(12),
                size_hint_x=0.15,
                halign='center'
            )
            type_label.bind(size=type_label.setter('text_size'))
            band_layout.add_widget(type_label)
            
            self.config_container.add_widget(band_layout)
        
        # Update global gain if available
        if hasattr(self, 'global_gain_label') and self.global_gain_label:
            # This would be set by the app when global gain changes
            pass
    
    def update_global_gain(self, gain: float):
        """Update global gain display."""
        self.global_gain_label.text = f'{gain:+.1f} dB'