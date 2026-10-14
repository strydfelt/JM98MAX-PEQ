"""
Trial screen for testing PEQ settings before persisting.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.logger import Logger

from models.peq_config import PEQConfiguration


class TrialScreen(Screen):
    """Screen for trialing PEQ settings."""
    
    # Callbacks
    on_start_trial = ObjectProperty(None)
    on_stop_trial = ObjectProperty(None)
    on_apply_trial = ObjectProperty(None)
    on_back = ObjectProperty(None)
    
    # State
    is_trial_active = BooleanProperty(False)
    
    # UI Elements
    trial_status_label = ObjectProperty(None)
    start_trial_btn = ObjectProperty(None)
    stop_trial_btn = ObjectProperty(None)
    apply_trial_btn = ObjectProperty(None)
    config_container = ObjectProperty(None)
    message_label = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        """Build the trial screen UI."""
        main_layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        title = Label(
            text='Trial PEQ Settings',
            font_size=dp(20),
            bold=True,
            halign='left'
        )
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        
        # Back button
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
        
        # Status display
        status_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        status_layout.add_widget(Label(text='Status:', font_size=dp(16), size_hint_x=0.25))
        
        self.trial_status_label = Label(
            text='Trial Inactive',
            font_size=dp(16),
            bold=True,
            color=(1, 0.5, 0.5, 1),  # Red
            halign='left'
        )
        self.trial_status_label.bind(size=self.trial_status_label.setter('text_size'))
        status_layout.add_widget(self.trial_status_label)
        main_layout.add_widget(status_layout)
        
        # Trial config preview
        preview_label = Label(
            text='Trial Configuration Preview',
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(30),
            halign='left'
        )
        preview_label.bind(size=preview_label.setter('text_size'))
        main_layout.add_widget(preview_label)
        
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
        
        # Control buttons
        btn_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(180))
        
        self.start_trial_btn = Button(
            text='Start Trial',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.3, 0.7, 0.3, 1)
        )
        self.start_trial_btn.bind(on_press=lambda x: self.on_start_trial() if self.on_start_trial else None)
        btn_layout.add_widget(self.start_trial_btn)
        
        self.stop_trial_btn = Button(
            text='Stop Trial',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.8, 0.4, 0.4, 1),
            disabled=True
        )
        self.stop_trial_btn.bind(on_press=lambda x: self.on_stop_trial() if self.on_stop_trial else None)
        btn_layout.add_widget(self.stop_trial_btn)
        
        self.apply_trial_btn = Button(
            text='Apply Trial Permanently',
            size_hint_y=None,
            height=dp(50),
            background_color=(1, 0.6, 0.2, 1),
            disabled=True
        )
        self.apply_trial_btn.bind(on_press=lambda x: self.on_apply_trial() if self.on_apply_trial else None)
        btn_layout.add_widget(self.apply_trial_btn)
        
        main_layout.add_widget(btn_layout)
        
        # Message area
        self.message_label = Label(
            text='',
            font_size=dp(14),
            size_hint_y=None,
            height=dp(30),
            color=(1, 1, 1, 1)
        )
        main_layout.add_widget(self.message_label)
        
        self.add_widget(main_layout)
    
    def load_config(self, current_config: PEQConfiguration, trial_config: PEQConfiguration):
        """Load configurations for display."""
        self.config_container.clear_widgets()
        
        # Show trial config (what will be trialed)
        for band in trial_config.bands:
            band_layout = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(30),
                spacing=dp(5)
            )
            
            label = Label(
                text=f'{band.index + 1}. {band.get_label()}',
                font_size=dp(12),
                size_hint_x=0.35,
                halign='left'
            )
            label.bind(size=label.setter('text_size'))
            band_layout.add_widget(label)
            
            freq_label = Label(
                text=f'{int(band.freq)} Hz',
                font_size=dp(12),
                size_hint_x=0.2,
                halign='center'
            )
            freq_label.bind(size=freq_label.setter('text_size'))
            band_layout.add_widget(freq_label)
            
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
            
            q_label = Label(
                text=f'Q:{band.q:.2f}',
                font_size=dp(12),
                size_hint_x=0.15,
                halign='center'
            )
            q_label.bind(size=q_label.setter('text_size'))
            band_layout.add_widget(q_label)
            
            type_label = Label(
                text=band.type,
                font_size=dp(12),
                size_hint_x=0.15,
                halign='center'
            )
            type_label.bind(size=type_label.setter('text_size'))
            band_layout.add_widget(type_label)
            
            self.config_container.add_widget(band_layout)
    
    def update_trial_status(self, active: bool):
        """Update trial active status."""
        self.is_trial_active = active
        
        if active:
            self.trial_status_label.text = 'Trial Active'
            self.trial_status_label.color = (0.3, 0.8, 0.3, 1)  # Green
            self.start_trial_btn.disabled = True
            self.stop_trial_btn.disabled = False
            self.apply_trial_btn.disabled = False
        else:
            self.trial_status_label.text = 'Trial Inactive'
            self.trial_status_label.color = (1, 0.5, 0.5, 1)  # Red
            self.start_trial_btn.disabled = False
            self.stop_trial_btn.disabled = True
            self.apply_trial_btn.disabled = True
    
    def show_success(self, message: str):
        """Show success message."""
        self.message_label.text = message
        self.message_label.color = (0.3, 0.8, 0.3, 1)
        Clock.schedule_once(lambda dt: setattr(self.message_label, 'text', ''), 3)
    
    def show_error(self, message: str):
        """Show error message."""
        self.message_label.text = message
        self.message_label.color = (1, 0.3, 0.3, 1)
        Clock.schedule_once(lambda dt: setattr(self.message_label, 'text', ''), 5)