"""
Configuration management for UniFi Documenter
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List


class Config:
    """Configuration manager for UniFi Documenter"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Default configuration for service mode
        self.unifi_controllers = []  # List of controller configurations
        self.unifi_timezone = 'UTC'
        self.unifi_schedule_time = '02:00'
        self.unifi_output_dir = '/output'
        
        # Legacy single-controller support (for backward compatibility)
        self.unifi_controller_ip = None
        self.unifi_api_key = None
        self.unifi_username = None
        self.unifi_password = None
        self.output_file = 'unifi-docs.md'
        self.output_format = 'markdown'
        
        # Feature flags
        self.include_networks = True
        self.include_wifi_networks = True
        self.include_devices = True
        self.include_clients = True
        self.include_firewall_rules = True
        self.include_nat_rules = True
        self.include_settings = True
        self.include_ip_addressing = True
        
        # SSL verification (defaults to True for security)
        self.unifi_verify_ssl = True
        
        # Load from config file if provided
        if config_file:
            self._load_from_file(config_file)
        
        # Override with environment variables
        self._load_from_env()
    
    def _load_from_file(self, config_file: str) -> None:
        """Load configuration from file (JSON or YAML)"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            self.logger.warning(f"Configuration file not found: {config_file}")
            return
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            self._update_from_dict(config_data)
            self.logger.info(f"Loaded configuration from {config_file}")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration file {config_file}: {e}")
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables"""
        # Service-specific environment variables
        unifi_controllers_json = os.getenv('UNIFI_CONTROLLERS')
        if unifi_controllers_json:
            try:
                self.unifi_controllers = json.loads(unifi_controllers_json)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing UNIFI_CONTROLLERS JSON: {e}")
                self.unifi_controllers = []
        
        # Service configuration
        if os.getenv('UNIFI_TIMEZONE'):
            self.unifi_timezone = os.getenv('UNIFI_TIMEZONE')
        
        if os.getenv('UNIFI_SCHEDULE_TIME'):
            self.unifi_schedule_time = os.getenv('UNIFI_SCHEDULE_TIME')
        
        if os.getenv('UNIFI_OUTPUT_DIR'):
            self.unifi_output_dir = os.getenv('UNIFI_OUTPUT_DIR')
        
        # Legacy environment variables (for backward compatibility)
        env_mappings = {
            'UNIFI_CONTROLLER_IP': 'unifi_controller_ip',
            'UNIFI_API_KEY': 'unifi_api_key',
            'UNIFI_USERNAME': 'unifi_username',
            'UNIFI_PASSWORD': 'unifi_password',
            'UNIFI_OUTPUT_FILE': 'output_file',
            'UNIFI_OUTPUT_FORMAT': 'output_format',
        }
        
        for env_var, attr_name in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                setattr(self, attr_name, value)
        
        # Boolean environment variables
        bool_mappings = {
            'UNIFI_INCLUDE_NETWORKS': 'include_networks',
            'UNIFI_INCLUDE_WIFI_NETWORKS': 'include_wifi_networks',
            'UNIFI_INCLUDE_DEVICES': 'include_devices',
            'UNIFI_INCLUDE_CLIENTS': 'include_clients',
            'UNIFI_INCLUDE_FIREWALL_RULES': 'include_firewall_rules',
            'UNIFI_INCLUDE_NAT_RULES': 'include_nat_rules',
            'UNIFI_INCLUDE_SETTINGS': 'include_settings',
            'UNIFI_INCLUDE_IP_ADDRESSING': 'include_ip_addressing',
            'UNIFI_VERIFY_SSL': 'unifi_verify_ssl',
        }
        
        for env_var, attr_name in bool_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                setattr(self, attr_name, value.lower() in ['true', '1', 'yes', 'on'])
        
        # Convert legacy single-controller config to multi-controller format if needed
        self._convert_legacy_config()
    
    def _convert_legacy_config(self) -> None:
        """Convert legacy single-controller configuration to multi-controller format"""
        if not self.unifi_controllers and self.unifi_controller_ip:
            controller_config = {
                'name': 'default',
                'host': self.unifi_controller_ip,
                'port': 443,
                'verify_ssl': self.unifi_verify_ssl,
            }
            
            if self.unifi_api_key:
                controller_config['api_key'] = self.unifi_api_key
            elif self.unifi_username:
                controller_config['username'] = self.unifi_username
                if self.unifi_password:
                    controller_config['password'] = self.unifi_password
            
            self.unifi_controllers = [controller_config]
            self.logger.info("Converted legacy single-controller config to multi-controller format")
    
    def get_controllers(self) -> List[Dict[str, Any]]:
        """Get list of configured UniFi controllers"""
        return self.unifi_controllers
    
    def has_multiple_controllers(self) -> bool:
        """Check if multiple controllers are configured"""
        return len(self.unifi_controllers) > 1
    
    def validate_controller_config(self, controller_config: Dict[str, Any]) -> bool:
        """Validate a single controller configuration"""
        if not controller_config.get('host'):
            self.logger.error(f"Controller configuration missing 'host': {controller_config}")
            return False
        
        # Check for authentication method
        has_api_key = controller_config.get('api_key')
        has_credentials = controller_config.get('username') and controller_config.get('password')
        
        if not has_api_key and not has_credentials:
            self.logger.error(f"Controller configuration missing authentication: {controller_config}")
            return False
        
        return True
    
    def _update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update configuration from dictionary"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'unifi_controllers': self.unifi_controllers,
            'unifi_timezone': self.unifi_timezone,
            'unifi_schedule_time': self.unifi_schedule_time,
            'unifi_output_dir': self.unifi_output_dir,
            'unifi_controller_ip': self.unifi_controller_ip,
            'output_file': self.output_file,
            'output_format': self.output_format,
            'include_networks': self.include_networks,
            'include_wifi_networks': self.include_wifi_networks,
            'include_devices': self.include_devices,
            'include_clients': self.include_clients,
            'include_firewall_rules': self.include_firewall_rules,
            'include_nat_rules': self.include_nat_rules,
            'include_settings': self.include_settings,
            'include_ip_addressing': self.include_ip_addressing,
            'unifi_verify_ssl': self.unifi_verify_ssl,
        }
    
    def save_to_file(self, file_path: str) -> None:
        """Save configuration to file"""
        config_path = Path(file_path)
        config_data = self.to_dict()
        
        # Remove sensitive information before saving
        sanitized_data = config_data.copy()
        if 'unifi_controllers' in sanitized_data:
            for controller in sanitized_data['unifi_controllers']:
                controller.pop('api_key', None)
                controller.pop('password', None)
        
        try:
            with open(config_path, 'w') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    yaml.dump(sanitized_data, f, default_flow_style=False)
                else:
                    json.dump(sanitized_data, f, indent=2)
            
            self.logger.info(f"Configuration saved to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration to {file_path}: {e}")
    
    def validate(self) -> bool:
        """Validate configuration"""
        # Check if we have any controllers configured
        if not self.unifi_controllers:
            self.logger.error("No UniFi controllers configured")
            return False
        
        # Validate each controller configuration
        for i, controller_config in enumerate(self.unifi_controllers):
            if not self.validate_controller_config(controller_config):
                self.logger.error(f"Invalid configuration for controller {i}")
                return False
        
        if self.output_format not in ['markdown', 'json']:
            self.logger.error("Output format must be 'markdown' or 'json'")
            return False
        
        # Validate schedule time format
        try:
            from datetime import datetime
            datetime.strptime(self.unifi_schedule_time, '%H:%M')
        except ValueError:
            self.logger.error(f"Invalid schedule time format: {self.unifi_schedule_time}. Use HH:MM format.")
            return False
        
        return True