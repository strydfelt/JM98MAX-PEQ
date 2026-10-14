"""
PEQ Configurator Kivy Application.
Main application class and screen management.
"""
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import ObjectProperty, ListProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.logger import Logger

# Import our modules
from models.peq_config import PEQConfiguration, PEQBand
from screens.main_screen import MainScreen
from screens.peq_editor_screen import PEQEditorScreen
from screens.trial_screen import TrialScreen
from screens.export_import_screen import ExportImportScreen
from screens.settings_screen import SettingsScreen
from services.device_service import DeviceService
from services.storage_service import StorageService


class PEQConfiguratorApp(App):
    """Main PEQ Configurator Application."""
    
    # Services
    device_service = ObjectProperty(None)
    storage_service = ObjectProperty(None)
    
    # Current configuration
    current_config = ObjectProperty(None)
    trial_config = ObjectProperty(None)
    
    # Global gain
    global_gain = NumericProperty(0)
    
    def build(self):
        """Build the application UI."""
        Logger.info("PEQConfiguratorApp: Building application")
        
        # Initialize services
        self.device_service = DeviceService()
        self.storage_service = StorageService()
        
        # Load saved configuration
        self.current_config = self.storage_service.load_config()
        if self.current_config is None:
            self.current_config = PEQConfiguration.create_default()
        
        # Create trial config as copy
        self.trial_config = self.current_config.copy()
        
        # Load global gain
        self.global_gain = self.storage_service.load_global_gain()
        
        # Create screen manager
        self.screen_manager = ScreenManager()
        
        # Create and add screens
        self.main_screen = MainScreen(name='main')
        self.peq_editor_screen = PEQEditorScreen(name='peq_editor')
        self.trial_screen = TrialScreen(name='trial')
        self.export_import_screen = ExportImportScreen(name='export_import')
        self.settings_screen = SettingsScreen(name='settings')
        
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.peq_editor_screen)
        self.screen_manager.add_widget(self.trial_screen)
        self.screen_manager.add_widget(self.export_import_screen)
        self.screen_manager.add_widget(self.settings_screen)
        
        # Bind callbacks
        self.main_screen.on_peq_editor = self.show_peq_editor
        self.main_screen.on_trial = self.show_trial
        self.main_screen.on_export_import = self.show_export_import
        self.main_screen.on_settings = self.show_settings
        self.main_screen.on_connect = self.connect_device
        
        self.peq_editor_screen.on_save = self.save_peq_config
        self.peq_editor_screen.on_cancel = self.cancel_peq_edit
        self.peq_editor_screen.on_reset = self.reset_peq_config
        
        self.trial_screen.on_start_trial = self.start_trial
        self.trial_screen.on_stop_trial = self.stop_trial
        self.trial_screen.on_apply_trial = self.apply_trial
        self.trial_screen.on_back = self.back_from_trial
        
        self.export_import_screen.on_export = self.export_config
        self.export_import_screen.on_import = self.import_config
        self.export_import_screen.on_back = self.back_from_export_import
        
        self.settings_screen.on_back = self.back_from_settings
        
        # Load settings
        self.settings_screen.load_settings(self.global_gain)
        
        return self.screen_manager
    
    def on_start(self):
        """Called when app starts."""
        Logger.info("PEQConfiguratorApp: Application started")
        # Try to auto-connect if previously connected
        Clock.schedule_once(lambda dt: self.device_service.auto_connect(), 1)
    
    def on_stop(self):
        """Called when app stops."""
        Logger.info("PEQConfiguratorApp: Application stopping")
        self.device_service.disconnect()
        self.storage_service.save_config(self.current_config)
        self.storage_service.save_global_gain(self.global_gain)
    
    # Screen navigation
    def show_peq_editor(self):
        """Show PEQ editor screen."""
        self.peq_editor_screen.load_config(self.current_config)
        self.screen_manager.current = 'peq_editor'
    
    def show_trial(self):
        """Show trial screen."""
        self.trial_screen.load_config(self.current_config, self.trial_config)
        self.screen_manager.current = 'trial'
    
    def show_export_import(self):
        """Show export/import screen."""
        self.export_import_screen.load_config(self.current_config)
        self.screen_manager.current = 'export_import'
    
    def show_settings(self):
        """Show settings screen."""
        self.settings_screen.load_settings(self.global_gain)
        self.screen_manager.current = 'settings'
    
    def connect_device(self):
        """Connect to JM98 Max device."""
        success = self.device_service.connect()
        if success:
            self.main_screen.update_connection_status(True)
            # Read current device config
            self.read_device_config()
        else:
            self.main_screen.update_connection_status(False)
    
    def read_device_config(self):
        """Read configuration from device."""
        config = self.device_service.read_config()
        if config:
            self.current_config = config
            self.trial_config = config.copy()
            self.main_screen.update_config_display(self.current_config)
            self.storage_service.save_config(self.current_config)
    
    # PEQ Configuration management
    def save_peq_config(self, config):
        """Save PEQ configuration."""
        self.current_config = config
        self.trial_config = config.copy()
        self.main_screen.update_config_display(self.current_config)
        self.storage_service.save_config(self.current_config)
        self.screen_manager.current = 'main'
    
    def cancel_peq_edit(self):
        """Cancel PEQ editing."""
        self.peq_editor_screen.load_config(self.current_config)
        self.screen_manager.current = 'main'
    
    def reset_peq_config(self):
        """Reset PEQ configuration to defaults."""
        self.current_config = PEQConfiguration.create_default()
        self.trial_config = self.current_config.copy()
        self.peq_editor_screen.load_config(self.current_config)
        self.storage_service.save_config(self.current_config)
    
    # Trial functionality
    def start_trial(self):
        """Start trial mode with current trial config."""
        success = self.device_service.apply_config(self.trial_config, trial=True)
        if success:
            self.trial_screen.update_trial_status(True)
        else:
            self.trial_screen.show_error("Failed to apply trial configuration")
    
    def stop_trial(self):
        """Stop trial mode and revert to persistent config."""
        success = self.device_service.apply_config(self.current_config, trial=False)
        if success:
            self.trial_screen.update_trial_status(False)
        else:
            self.trial_screen.show_error("Failed to revert configuration")
    
    def apply_trial(self):
        """Apply trial configuration permanently."""
        self.current_config = self.trial_config.copy()
        success = self.device_service.apply_config(self.current_config, trial=False)
        if success:
            success = self.device_service.save_to_flash()
            if success:
                self.storage_service.save_config(self.current_config)
                self.trial_screen.show_success("Trial configuration applied and saved to flash")
            else:
                self.trial_screen.show_error("Applied but failed to save to flash")
        else:
            self.trial_screen.show_error("Failed to apply trial configuration")
        
        self.main_screen.update_config_display(self.current_config)
    
    def back_from_trial(self):
        """Return from trial screen."""
        # Ensure trial is stopped
        if self.trial_screen.is_trial_active:
            self.stop_trial()
        self.screen_manager.current = 'main'
    
    # Export/Import functionality
    def export_config(self, filepath):
        """Export configuration to file."""
        data = {
            'device': 'JM98MAX',
            'timestamp': self.storage_service.get_timestamp(),
            'globalGain': self.global_gain,
            'bands': [band.to_dict() for band in self.current_config.bands]
        }
        success = self.storage_service.export_config(data, filepath)
        if success:
            self.export_import_screen.show_success(f"Configuration exported to {filepath}")
        else:
            self.export_import_screen.show_error("Failed to export configuration")
    
    def import_config(self, filepath):
        """Import configuration from file."""
        data = self.storage_service.import_config(filepath)
        if data:
            try:
                # Validate imported data
                if 'bands' in data:
                    bands = [PEQBand.from_dict(b) for b in data['bands']]
                    self.current_config = PEQConfiguration(bands=bands)
                    if 'globalGain' in data:
                        self.global_gain = data['globalGain']
                    
                    self.trial_config = self.current_config.copy()
                    self.main_screen.update_config_display(self.current_config)
                    self.storage_service.save_config(self.current_config)
                    self.storage_service.save_global_gain(self.global_gain)
                    self.export_import_screen.show_success("Configuration imported successfully")
                else:
                    self.export_import_screen.show_error("Invalid configuration file format")
            except Exception as e:
                self.export_import_screen.show_error(f"Import error: {str(e)}")
        else:
            self.export_import_screen.show_error("Failed to read configuration file")
    
    def back_from_export_import(self):
        """Return from export/import screen."""
        self.screen_manager.current = 'main'
    
    def back_from_settings(self):
        """Return from settings screen and save settings."""
        settings = self.settings_screen.get_settings()
        self.global_gain = settings['global_gain']
        self.storage_service.save_global_gain(self.global_gain)
        self.main_screen.update_global_gain(self.global_gain)
        self.screen_manager.current = 'main'