"""
UniFi Controller API Client

This module provides a client for connecting to UniFi Controllers and retrieving network information.
"""

import json
import logging
import requests
import urllib3
from typing import Dict, Any, List, Optional, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Disable SSL warnings if verify_ssl is False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
    """UniFi Controller API Client"""
    
    def __init__(self, host: str, port: int = 443, verify_ssl: bool = True):
        self.host = host
        self.port = port
        self.verify_ssl = verify_ssl
        self.logger = logging.getLogger(__name__)
        
        # Session management
        self.session = requests.Session()
        self.session.verify = verify_ssl
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # API endpoints
        self.base_url = f"https://{host}:{port}"
        self.api_url = f"{self.base_url}/api"
        
        # Authentication state
        self.authenticated = False
        self.api_key = None
        self.username = None
        self.csrf_token = None
        
    def authenticate_with_api_key(self, api_key: str) -> bool:
        """Authenticate using API key"""
        try:
            self.api_key = api_key
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
            
            # Test authentication by getting controller info
            response = self._make_request('GET', '/api/self')
            if response.status_code == 200:
                self.authenticated = True
                self.logger.info(f"Successfully authenticated to {self.host} using API key")
                return True
            else:
                self.logger.error(f"API key authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"API key authentication error: {e}")
            return False
    
    def authenticate_with_credentials(self, username: str, password: str) -> bool:
        """Authenticate using username and password"""
        try:
            self.username = username
            
            # Login request
            login_data = {
                'username': username,
                'password': password,
                'remember': True
            }
            
            response = self._make_request('POST', '/api/auth/login', data=login_data)
            
            if response.status_code == 200:
                self.authenticated = True
                # Extract CSRF token if present
                if 'X-CSRF-Token' in response.headers:
                    self.csrf_token = response.headers['X-CSRF-Token']
                    self.session.headers.update({'X-CSRF-Token': self.csrf_token})
                
                self.logger.info(f"Successfully authenticated to {self.host} as {username}")
                return True
            else:
                self.logger.error(f"Credential authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Credential authentication error: {e}")
            return False
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> requests.Response:
        """Make HTTP request to UniFi controller"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise UniFiConnectionError(f"Failed to connect to {self.host}: {e}")
    
    def get_sites(self) -> List[Dict[str, Any]]:
        """Get list of sites"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', '/api/self/sites')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get sites: {response.status_code}")
    
    def get_networks(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get network configurations"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/rest/networkconf')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get networks: {response.status_code}")
    
    def get_wlan_groups(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get WLAN groups"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/rest/wlangroup')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get WLAN groups: {response.status_code}")
    
    def get_wireless_networks(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get wireless network configurations"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/rest/wlanconf')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get wireless networks: {response.status_code}")
    
    def get_devices(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get UniFi devices"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/stat/device')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get devices: {response.status_code}")
    
    def get_clients(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get active clients"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/stat/sta')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get clients: {response.status_code}")
    
    def get_known_clients(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get known/configured clients"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/rest/user')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get known clients: {response.status_code}")
    
    def get_firewall_groups(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get firewall groups"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/rest/firewallgroup')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get firewall groups: {response.status_code}")
    
    def get_firewall_rules(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get firewall rules"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/rest/firewallrule')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get firewall rules: {response.status_code}")
    
    def get_port_forwards(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get port forward rules"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/rest/portforward')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get port forwards: {response.status_code}")
    
    def get_site_settings(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get site settings"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/get/setting')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get site settings: {response.status_code}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get controller system information"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', '/api/system')
        if response.status_code == 200:
            return response.json()
        else:
            raise UniFiAPIError(f"Failed to get system info: {response.status_code}")
    
    def get_health(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get site health information"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/stat/health')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get health info: {response.status_code}")
    
    def get_dpi_stats(self, site_id: str = 'default') -> List[Dict[str, Any]]:
        """Get DPI statistics"""
        if not self.authenticated:
            raise UniFiAuthenticationError("Not authenticated")
        
        response = self._make_request('GET', f'/api/s/{site_id}/stat/dpi')
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise UniFiAPIError(f"Failed to get DPI stats: {response.status_code}")
    
    def disconnect(self) -> None:
        """Disconnect from controller"""
        if self.authenticated and not self.api_key:
            # Only logout if using username/password authentication
            try:
                self._make_request('POST', '/api/auth/logout')
            except Exception:
                pass  # Ignore logout errors
        
        self.authenticated = False
        self.session.close()
        self.logger.info(f"Disconnected from {self.host}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()