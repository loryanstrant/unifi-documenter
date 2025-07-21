"""
UniFi Controller API Client using pyunifi library

This module provides a client for connecting to UniFi Controllers and retrieving network information
using the pyunifi library with the TNWare UniFi Controller API documentation configuration format.
"""

import logging
import urllib.parse
from typing import Dict, Any, List, Optional
from pyunifi.controller import Controller, APIError


class UniFiAPIError(Exception):
    """Base exception for UniFi API errors"""
    pass


class UniFiConnectionError(UniFiAPIError):
    """Exception raised when unable to connect to UniFi controller"""
    pass


class UniFiAuthenticationError(UniFiAPIError):
    """Exception raised when authentication fails"""
    pass


class UniFiClient:
    """UniFi Controller API Client using pyunifi library"""
    
    def __init__(self, controller_url: str, username: str, password: str, 
                 is_udm_pro: bool = False, verify_ssl: bool = True, api_version: str = None):
        """
        Initialize UniFi client using pyunifi library
        
        Args:
            controller_url: Full URL to UniFi controller (e.g., https://unifi.example.com:8443)
            username: Local admin username
            password: Password for authentication
            is_udm_pro: True if using UniFi OS based controller (UDM Pro, etc.)
            verify_ssl: SSL certificate verification (True/False or path to CA bundle)
            api_version: UniFi API version to use (None for auto-detection)
        """
        self.controller_url = controller_url
        self.username = username
        self.password = password
        self.is_udm_pro = is_udm_pro
        self.verify_ssl = verify_ssl
        self.api_version = api_version
        self.logger = logging.getLogger(__name__)
        
        # Parse the controller URL
        parsed_url = urllib.parse.urlparse(controller_url)
        self.host = parsed_url.hostname
        self.port = parsed_url.port or (8443 if not is_udm_pro else 443)
        
        # Adjust port for UDM Pro if needed
        if is_udm_pro and self.port == 8443:
            self.port = 443
            self.logger.info(f"Adjusted port to 443 for UDM Pro controller: {self.host}")
        
        self.controller = None
        self.authenticated = False
        self.successful_api_version = None
        
    def _get_api_versions_to_try(self) -> List[str]:
        """Get list of API versions to try in order of preference"""
        versions = []
        
        # If specific version is configured, try it first
        if self.api_version:
            versions.append(self.api_version)
            self.logger.info(f"Will try specified API version first: {self.api_version}")
        
        # Common API versions to try as fallback
        fallback_versions = ['v5', 'unifiOS', 'v4', 'v6']
        
        # Add fallback versions that aren't already in the list
        for version in fallback_versions:
            if version not in versions:
                versions.append(version)
        
        return versions
    
    def _try_authenticate_with_version(self, version: str) -> bool:
        """Try to authenticate with a specific API version"""
        try:
            self.logger.info(f"Attempting authentication with API version: {version}")
            
            # Create pyunifi Controller instance with specific version
            controller = Controller(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                version=version,
                site_id='default',
                ssl_verify=self.verify_ssl
            )
            
            # Test authentication by getting sites
            sites = controller.get_sites()
            
            # If we get here, authentication was successful
            self.controller = controller
            self.successful_api_version = version
            self.logger.info(f"Successfully authenticated using API version: {version}")
            self.logger.info(f"Found {len(sites)} sites")
            return True
            
        except APIError as e:
            self.logger.debug(f"Authentication failed with API version {version}: {e}")
            return False
        except Exception as e:
            self.logger.debug(f"Authentication error with API version {version}: {e}")
            return False
    
    def authenticate(self) -> bool:
        """Authenticate with the UniFi controller using username/password with automatic API version detection"""
        self.logger.info(f"Connecting to UniFi controller at {self.host}:{self.port}")
        
        versions_to_try = self._get_api_versions_to_try()
        self.logger.info(f"Will attempt authentication with API versions: {', '.join(versions_to_try)}")
        
        for version in versions_to_try:
            if self._try_authenticate_with_version(version):
                self.authenticated = True
                self.logger.info(f"Successfully authenticated to {self.host} as {self.username} using API version {self.successful_api_version}")
                return True
        
        # If we get here, all versions failed
        self.logger.error(f"Authentication failed with all attempted API versions: {', '.join(versions_to_try)}")
        self.logger.error("Please check your credentials and controller configuration.")
        if self.is_udm_pro:
            self.logger.error("For UDM Pro controllers, ensure UNIFI_IS_UDM_PRO=true is set.")
        return False
    
    def get_sites(self) -> List[Dict[str, Any]]:
        """Get list of sites"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            return self.controller.get_sites()
        except APIError as e:
            raise UniFiAPIError(f"Failed to get sites: {e}")
    
    def get_networks(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get network configurations"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            # Get network settings using the generic get_setting method
            settings = self.controller.get_setting('networks')
            return settings if isinstance(settings, list) else [settings] if settings else []
        except APIError as e:
            raise UniFiAPIError(f"Failed to get networks: {e}")
    
    def get_wlan_groups(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get WLAN groups"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            # Get WLAN group settings
            settings = self.controller.get_setting('wlangroup')
            return settings if isinstance(settings, list) else [settings] if settings else []
        except APIError as e:
            raise UniFiAPIError(f"Failed to get WLAN groups: {e}")
    
    def get_wireless_networks(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get wireless network configurations"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            return self.controller.get_wlan_conf()
        except APIError as e:
            raise UniFiAPIError(f"Failed to get wireless networks: {e}")
    
    def get_devices(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get UniFi devices"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            return self.controller.get_aps()
        except APIError as e:
            raise UniFiAPIError(f"Failed to get devices: {e}")
    
    def get_clients(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get active clients"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            return self.controller.get_clients()
        except APIError as e:
            raise UniFiAPIError(f"Failed to get clients: {e}")
    
    def get_known_clients(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get known/configured clients"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            return self.controller.get_users()
        except APIError as e:
            raise UniFiAPIError(f"Failed to get known clients: {e}")
    
    def get_firewall_groups(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get firewall groups"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            # Get firewall settings
            settings = self.controller.get_setting('firewallgroup')
            return settings if isinstance(settings, list) else [settings] if settings else []
        except APIError as e:
            raise UniFiAPIError(f"Failed to get firewall groups: {e}")
    
    def get_firewall_rules(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get firewall rules"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            # Get firewall settings
            settings = self.controller.get_setting('firewallrule')
            return settings if isinstance(settings, list) else [settings] if settings else []
        except APIError as e:
            raise UniFiAPIError(f"Failed to get firewall rules: {e}")
    
    def get_port_forwards(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get port forward rules"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            # Get port forward settings
            settings = self.controller.get_setting('portforward')
            return settings if isinstance(settings, list) else [settings] if settings else []
        except APIError as e:
            raise UniFiAPIError(f"Failed to get port forwards: {e}")
    
    def get_site_settings(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get site settings"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            settings = self.controller.get_setting()
            return settings if isinstance(settings, list) else [settings] if settings else []
        except APIError as e:
            raise UniFiAPIError(f"Failed to get site settings: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get controller system information"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            return self.controller.get_sysinfo()
        except APIError as e:
            raise UniFiAPIError(f"Failed to get system info: {e}")
    
    def get_health(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get site health information"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            health_info = self.controller.get_healthinfo()
            return health_info if isinstance(health_info, list) else [health_info] if health_info else []
        except APIError as e:
            raise UniFiAPIError(f"Failed to get health info: {e}")
    
    def get_dpi_stats(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get DPI statistics"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        try:
            # Switch to the specified site
            self.controller.switch_site(site_id)
            # DPI stats might not be available in pyunifi, return empty list
            return []
        except APIError as e:
            self.logger.warning(f"DPI stats not available: {e}")
            return []
    
    def disconnect(self) -> None:
        """Disconnect from controller"""
        if self.controller:
            # pyunifi handles disconnection automatically
            self.authenticated = False
            self.controller = None
            self.logger.info(f"Disconnected from {self.host}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()