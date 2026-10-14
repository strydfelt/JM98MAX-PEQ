"""
Export/Import screen for PEQ configuration files.
Supports JSON and Equalizer APO Filter.txt formats.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.spinner import Spinner
from kivy.properties import ObjectProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.logger import Logger

import os


class ExportImportScreen(Screen):
    """Screen for exporting and importing PEQ configurations."""
    
    # Callbacks
    on_export = ObjectProperty(None)
    on_import = ObjectProperty(None)
    on_back = ObjectProperty(None)
    
    # UI Elements
    export_path_input = ObjectProperty(None)
    export_format_spinner = ObjectProperty(None)
    import_filechooser = ObjectProperty(None)
    message_label = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        """Build the export/import screen UI."""
        main_layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        title = Label(
            text='Export / Import Configuration',
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
        
        # Export section
        export_label = Label(
            text='Export Configuration',
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(30),
            halign='left'
        )
        export_label.bind(size=export_label.setter('text_size'))
        main_layout.add_widget(export_label)
        
        # Export format selector
        format_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        format_layout.add_widget(Label(text='Format:', size_hint_x=0.15))
        
        self.export_format_spinner = Spinner(
            text='JSON',
            values=('JSON', 'Filter.txt (Equalizer APO)'),
            size_hint_x=0.35
        )
        self.export_format_spinner.bind(text=self.on_format_change)
        format_layout.add_widget(self.export_format_spinner)
        
        format_layout.add_widget(Label(text='Filename:', size_hint_x=0.15))
        
        self.export_path_input = TextInput(
            text='eq_profile.json',
            multiline=False,
            size_hint_x=0.35
        )
        format_layout.add_widget(self.export_path_input)
        
        main_layout.add_widget(format_layout)
        
        export_btn = Button(
            text='Export',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.3, 0.7, 0.3, 1)
        )
        export_btn.bind(on_press=self.on_export_pressed)
        main_layout.add_widget(export_btn)
        
        # Import section
        import_label = Label(
            text='Import Configuration',
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(30),
            halign='left'
        )
        import_label.bind(size=import_label.setter('text_size'))
        main_layout.add_widget(import_label)
        
        import_desc = Label(
            text='Select a JSON or Filter.txt configuration file to import',
            font_size=dp(12),
            size_hint_y=None,
            height=dp(25),
            halign='left',
            color=(0.7, 0.7, 0.7, 1)
        )
        import_desc.bind(size=import_desc.setter('text_size'))
        main_layout.add_widget(import_desc)
        
        # File chooser - support both .json and .txt
        self.import_filechooser = FileChooserListView(
            filters=['*.json', '*.txt'],
            path=os.path.expanduser('~'),
            size_hint_y=0.4
        )
        main_layout.add_widget(self.import_filechooser)
        
        import_btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        
        import_btn = Button(
            text='Import Selected File',
            background_color=(0.2, 0.6, 1, 1)
        )
        import_btn.bind(on_press=self.on_import_pressed)
        import_btn_layout.add_widget(import_btn)
        
        main_layout.add_widget(import_btn_layout)
        
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
    
    def on_format_change(self, spinner, text):
        """Update default filename based on selected format."""
        if 'Filter.txt' in text:
            if self.export_path_input.text.endswith('.json'):
                self.export_path_input.text = self.export_path_input.text.replace('.json', '.txt')
        else:
            if self.export_path_input.text.endswith('.txt'):
                self.export_path_input.text = self.export_path_input.text.replace('.txt', '.json')
    
    def load_config(self, config):
        """Load current config (for reference)."""
        pass
    
    def on_export_pressed(self, button):
        """Handle export button press."""
        filepath = self.export_path_input.text.strip()
        if not filepath:
            self.show_error('Please enter a filename')
            return
        
        # Ensure correct extension based on format
        if 'Filter.txt' in self.export_format_spinner.text:
            if not filepath.endswith('.txt'):
                filepath += '.txt'
        else:
            if not filepath.endswith('.json'):
                filepath += '.json'
        
        if self.on_export:
            self.on_export(filepath)
    
    def on_import_pressed(self, button):
        """Handle import button press."""
        selection = self.import_filechooser.selection
        if not selection:
            self.show_error('Please select a file to import')
            return
        
        filepath = selection[0]
        if self.on_import:
            self.on_import(filepath)
    
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