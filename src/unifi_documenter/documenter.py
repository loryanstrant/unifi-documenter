"""
UniFi Network Documentation Generator

This module generates comprehensive documentation for UniFi networks.
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .client import UniFiClient, UniFiAPIError, UniFiConnectionError, UniFiAuthenticationError


class UniFiDocumenter:
    """Main documentation generator for UniFi networks"""
    
    def __init__(self, output_dir: str = '/output', output_format: str = 'markdown'):
        self.output_dir = Path(output_dir)
        self.output_format = output_format.lower()
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_documentation(self, controller_config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Generate documentation for a single UniFi controller
        
        Returns:
            Tuple of (success: bool, output_file: str)
        """
        controller_name = controller_config.get('name', 'default')
        self.logger.info(f"Generating documentation for controller: {controller_name}")
        
        try:
            # Connect to controller
            client = self._connect_to_controller(controller_config)
            
            # Gather all data
            documentation_data = self._gather_controller_data(client, controller_config)
            
            # Generate output
            output_file = self._generate_output_file(documentation_data, controller_name)
            
            # Cleanup
            client.disconnect()
            
            self.logger.info(f"Documentation generated successfully: {output_file}")
            return True, output_file
            
        except Exception as e:
            self.logger.error(f"Failed to generate documentation for {controller_name}: {e}")
            return False, str(e)
    
    def _connect_to_controller(self, controller_config: Dict[str, Any]) -> UniFiClient:
        """Connect to UniFi controller using pyunifi library"""
        controller_url = controller_config['controller_url']
        username = controller_config['username']
        password = controller_config['password']
        is_udm_pro = controller_config.get('is_udm_pro', False)
        verify_ssl = controller_config.get('verify_ssl', True)
        
        client = UniFiClient(
            controller_url=controller_url,
            username=username,
            password=password,
            is_udm_pro=is_udm_pro,
            verify_ssl=verify_ssl
        )
        
        # Authenticate (only username/password supported)
        success = client.authenticate()
        
        if not success:
            raise UniFiAuthenticationError("Authentication failed")
        
        return client
    
    def _gather_controller_data(self, client: UniFiClient, controller_config: Dict[str, Any]) -> Dict[str, Any]:
        """Gather all data from the controller"""
        data = {
            'controller': {
                'name': controller_config.get('name', 'default'),
                'host': controller_config['host'],
                'port': controller_config.get('port', 443),
                'generated_at': datetime.now().isoformat(),
            },
            'sites': [],
            'system_info': None,
        }
        
        try:
            # Get system information
            data['system_info'] = client.get_system_info()
        except Exception as e:
            self.logger.warning(f"Failed to get system info: {e}")
            data['system_info'] = {}
        
        # Get sites
        try:
            sites = client.get_sites()
            self.logger.info(f"Found {len(sites)} sites")
            
            for site in sites:
                site_id = site.get('name', 'default')
                site_data = self._gather_site_data(client, site_id, site)
                data['sites'].append(site_data)
                
        except Exception as e:
            self.logger.error(f"Failed to get sites: {e}")
            # Try with default site
            try:
                site_data = self._gather_site_data(client, 'default', {'name': 'default', 'desc': 'Default Site'})
                data['sites'].append(site_data)
            except Exception as e2:
                self.logger.error(f"Failed to get default site data: {e2}")
        
        return data
    
    def _gather_site_data(self, client: UniFiClient, site_id: str, site_info: Dict[str, Any]) -> Dict[str, Any]:
        """Gather data for a single site"""
        site_data = {
            'info': site_info,
            'networks': [],
            'wireless_networks': [],
            'wlan_groups': [],
            'devices': [],
            'clients': [],
            'known_clients': [],
            'firewall_groups': [],
            'firewall_rules': [],
            'port_forwards': [],
            'settings': [],
            'health': [],
            'dpi_stats': [],
        }
        
        # Define data gathering methods
        data_methods = [
            ('networks', 'get_networks'),
            ('wireless_networks', 'get_wireless_networks'),
            ('wlan_groups', 'get_wlan_groups'),
            ('devices', 'get_devices'),
            ('clients', 'get_clients'),
            ('known_clients', 'get_known_clients'),
            ('firewall_groups', 'get_firewall_groups'),
            ('firewall_rules', 'get_firewall_rules'),
            ('port_forwards', 'get_port_forwards'),
            ('settings', 'get_site_settings'),
            ('health', 'get_health'),
            ('dpi_stats', 'get_dpi_stats'),
        ]
        
        for data_key, method_name in data_methods:
            try:
                method = getattr(client, method_name)
                site_data[data_key] = method(site_id)
                self.logger.debug(f"Retrieved {len(site_data[data_key])} {data_key} for site {site_id}")
            except Exception as e:
                self.logger.warning(f"Failed to get {data_key} for site {site_id}: {e}")
                site_data[data_key] = []
        
        return site_data
    
    def _generate_output_file(self, data: Dict[str, Any], controller_name: str) -> str:
        """Generate the output documentation file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.output_format == 'json':
            output_file = self.output_dir / f"unifi-{controller_name}-{timestamp}.json"
            self._generate_json_output(data, output_file)
        else:
            output_file = self.output_dir / f"unifi-{controller_name}-{timestamp}.md"
            self._generate_markdown_output(data, output_file)
        
        # Create a symlink to the latest file
        latest_file = self.output_dir / f"unifi-{controller_name}-latest.{self.output_format}"
        if latest_file.exists():
            latest_file.unlink()
        latest_file.symlink_to(output_file.name)
        
        return str(output_file)
    
    def _generate_json_output(self, data: Dict[str, Any], output_file: Path) -> None:
        """Generate JSON output"""
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _generate_markdown_output(self, data: Dict[str, Any], output_file: Path) -> None:
        """Generate Markdown output"""
        with open(output_file, 'w') as f:
            self._write_markdown_header(f, data)
            self._write_system_info(f, data.get('system_info', {}))
            
            for site in data.get('sites', []):
                self._write_site_documentation(f, site)
    
    def _write_markdown_header(self, f, data: Dict[str, Any]) -> None:
        """Write markdown header"""
        controller = data.get('controller', {})
        f.write(f"# UniFi Network Documentation\n\n")
        f.write(f"**Controller:** {controller.get('name', 'Unknown')}\n")
        f.write(f"**Host:** {controller.get('host', 'Unknown')}:{controller.get('port', 443)}\n")
        f.write(f"**Generated:** {controller.get('generated_at', 'Unknown')}\n\n")
        f.write("---\n\n")
    
    def _write_system_info(self, f, system_info: Dict[str, Any]) -> None:
        """Write system information section"""
        if not system_info:
            return
        
        f.write("## Controller Information\n\n")
        
        # Basic system info
        if 'hostname' in system_info:
            f.write(f"**Hostname:** {system_info['hostname']}\n")
        if 'version' in system_info:
            f.write(f"**Version:** {system_info['version']}\n")
        if 'build' in system_info:
            f.write(f"**Build:** {system_info['build']}\n")
        if 'uptime' in system_info:
            f.write(f"**Uptime:** {system_info['uptime']} seconds\n")
        
        f.write("\n")
    
    def _write_site_documentation(self, f, site: Dict[str, Any]) -> None:
        """Write documentation for a single site"""
        site_info = site.get('info', {})
        site_name = site_info.get('desc', site_info.get('name', 'Unknown Site'))
        
        f.write(f"## Site: {site_name}\n\n")
        
        # Site description
        if site_info.get('desc') and site_info.get('desc') != site_info.get('name'):
            f.write(f"**Description:** {site_info['desc']}\n")
        if site_info.get('name'):
            f.write(f"**Site ID:** {site_info['name']}\n")
        f.write("\n")
        
        # Networks and VLANs
        self._write_networks_section(f, site.get('networks', []))
        
        # WiFi Networks
        self._write_wireless_networks_section(f, site.get('wireless_networks', []), site.get('wlan_groups', []))
        
        # Devices
        self._write_devices_section(f, site.get('devices', []))
        
        # Clients
        self._write_clients_section(f, site.get('clients', []), site.get('known_clients', []))
        
        # Firewall and Security
        self._write_firewall_section(f, site.get('firewall_rules', []), site.get('firewall_groups', []))
        
        # Port Forwarding
        self._write_port_forward_section(f, site.get('port_forwards', []))
        
        # Site Settings
        self._write_settings_section(f, site.get('settings', []))
        
        # Health and Statistics
        self._write_health_section(f, site.get('health', []))
    
    def _write_networks_section(self, f, networks: List[Dict[str, Any]]) -> None:
        """Write networks and VLANs section"""
        if not networks:
            return
        
        f.write("### Networks & VLANs\n\n")
        
        for network in networks:
            name = network.get('name', 'Unknown')
            purpose = network.get('purpose', 'Unknown')
            vlan = network.get('vlan', 'N/A')
            
            f.write(f"#### {name}\n\n")
            f.write(f"- **Purpose:** {purpose}\n")
            f.write(f"- **VLAN ID:** {vlan}\n")
            
            if network.get('ip_subnet'):
                f.write(f"- **Subnet:** {network['ip_subnet']}\n")
            if network.get('dhcp_enabled'):
                f.write(f"- **DHCP Enabled:** {network['dhcp_enabled']}\n")
                if network.get('dhcp_start') and network.get('dhcp_stop'):
                    f.write(f"- **DHCP Range:** {network['dhcp_start']} - {network['dhcp_stop']}\n")
            if network.get('domain_name'):
                f.write(f"- **Domain:** {network['domain_name']}\n")
            
            f.write("\n")
    
    def _write_wireless_networks_section(self, f, wireless_networks: List[Dict[str, Any]], wlan_groups: List[Dict[str, Any]]) -> None:
        """Write wireless networks section"""
        if not wireless_networks:
            return
        
        f.write("### WiFi Networks\n\n")
        
        # Create mapping of wlan_group_id to group info
        wlan_group_map = {group.get('_id'): group for group in wlan_groups}
        
        for wlan in wireless_networks:
            name = wlan.get('name', 'Unknown')
            enabled = wlan.get('enabled', False)
            
            f.write(f"#### {name}\n\n")
            f.write(f"- **Enabled:** {'Yes' if enabled else 'No'}\n")
            f.write(f"- **SSID:** {wlan.get('x_passphrase', 'Hidden') if wlan.get('hide_ssid') else name}\n")
            f.write(f"- **Security:** {wlan.get('security', 'Unknown')}\n")
            
            if wlan.get('networkconf_id'):
                f.write(f"- **Network ID:** {wlan['networkconf_id']}\n")
            if wlan.get('wlan_band'):
                f.write(f"- **Band:** {wlan['wlan_band']}\n")
            if wlan.get('is_guest'):
                f.write(f"- **Guest Network:** Yes\n")
            
            # WLAN Group info
            if wlan.get('wlangroup_id') and wlan['wlangroup_id'] in wlan_group_map:
                group = wlan_group_map[wlan['wlangroup_id']]
                f.write(f"- **WLAN Group:** {group.get('name', 'Unknown')}\n")
            
            f.write("\n")
    
    def _write_devices_section(self, f, devices: List[Dict[str, Any]]) -> None:
        """Write UniFi devices section"""
        if not devices:
            return
        
        f.write("### UniFi Devices\n\n")
        
        # Group devices by type
        device_types = {}
        for device in devices:
            device_type = device.get('type', 'Unknown')
            if device_type not in device_types:
                device_types[device_type] = []
            device_types[device_type].append(device)
        
        for device_type, type_devices in device_types.items():
            f.write(f"#### {device_type.title()} Devices\n\n")
            
            for device in type_devices:
                name = device.get('name', device.get('model', 'Unknown'))
                model = device.get('model', 'Unknown')
                ip = device.get('ip', 'Unknown')
                mac = device.get('mac', 'Unknown')
                state = device.get('state', 'Unknown')
                
                f.write(f"**{name}**\n")
                f.write(f"- **Model:** {model}\n")
                f.write(f"- **IP Address:** {ip}\n")
                f.write(f"- **MAC Address:** {mac}\n")
                f.write(f"- **State:** {state}\n")
                
                if device.get('version'):
                    f.write(f"- **Firmware:** {device['version']}\n")
                if device.get('uptime'):
                    f.write(f"- **Uptime:** {device['uptime']} seconds\n")
                
                f.write("\n")
    
    def _write_clients_section(self, f, active_clients: List[Dict[str, Any]], known_clients: List[Dict[str, Any]]) -> None:
        """Write clients section"""
        f.write("### Network Clients\n\n")
        
        if active_clients:
            f.write(f"#### Active Clients ({len(active_clients)})\n\n")
            for client in active_clients[:20]:  # Limit to first 20 for readability
                hostname = client.get('hostname', client.get('name', 'Unknown'))
                ip = client.get('ip', 'Unknown')
                mac = client.get('mac', 'Unknown')
                
                f.write(f"- **{hostname}** ({ip}) - {mac}\n")
                if client.get('network'):
                    f.write(f"  - Network: {client['network']}\n")
                if client.get('essid'):
                    f.write(f"  - WiFi: {client['essid']}\n")
            
            if len(active_clients) > 20:
                f.write(f"\n*... and {len(active_clients) - 20} more active clients*\n")
            f.write("\n")
        
        if known_clients:
            f.write(f"#### Known/Configured Clients ({len(known_clients)})\n\n")
            for client in known_clients[:10]:  # Limit to first 10
                name = client.get('name', client.get('hostname', 'Unknown'))
                mac = client.get('mac', 'Unknown')
                
                f.write(f"- **{name}** - {mac}\n")
                if client.get('fixed_ip'):
                    f.write(f"  - Fixed IP: {client['fixed_ip']}\n")
                if client.get('note'):
                    f.write(f"  - Note: {client['note']}\n")
            
            if len(known_clients) > 10:
                f.write(f"\n*... and {len(known_clients) - 10} more known clients*\n")
            f.write("\n")
    
    def _write_firewall_section(self, f, firewall_rules: List[Dict[str, Any]], firewall_groups: List[Dict[str, Any]]) -> None:
        """Write firewall rules section"""
        if not firewall_rules and not firewall_groups:
            return
        
        f.write("### Firewall & Security\n\n")
        
        if firewall_groups:
            f.write("#### Firewall Groups\n\n")
            for group in firewall_groups:
                name = group.get('name', 'Unknown')
                group_type = group.get('group_type', 'Unknown')
                f.write(f"- **{name}** ({group_type})\n")
                if group.get('group_members'):
                    members = ', '.join(group['group_members'])
                    f.write(f"  - Members: {members}\n")
            f.write("\n")
        
        if firewall_rules:
            f.write("#### Firewall Rules\n\n")
            for rule in firewall_rules:
                name = rule.get('name', f"Rule {rule.get('rule_index', 'Unknown')}")
                action = rule.get('action', 'Unknown')
                enabled = rule.get('enabled', False)
                
                f.write(f"**{name}**\n")
                f.write(f"- **Action:** {action}\n")
                f.write(f"- **Enabled:** {'Yes' if enabled else 'No'}\n")
                
                if rule.get('src_address'):
                    f.write(f"- **Source:** {rule['src_address']}\n")
                if rule.get('dst_address'):
                    f.write(f"- **Destination:** {rule['dst_address']}\n")
                if rule.get('dst_port'):
                    f.write(f"- **Port:** {rule['dst_port']}\n")
                if rule.get('protocol'):
                    f.write(f"- **Protocol:** {rule['protocol']}\n")
                
                f.write("\n")
    
    def _write_port_forward_section(self, f, port_forwards: List[Dict[str, Any]]) -> None:
        """Write port forwarding section"""
        if not port_forwards:
            return
        
        f.write("### Port Forwarding (NAT Rules)\n\n")
        
        for rule in port_forwards:
            name = rule.get('name', 'Unnamed Rule')
            enabled = rule.get('enabled', False)
            
            f.write(f"**{name}**\n")
            f.write(f"- **Enabled:** {'Yes' if enabled else 'No'}\n")
            
            if rule.get('src'):
                f.write(f"- **Source:** {rule['src']}\n")
            if rule.get('dst_port'):
                f.write(f"- **External Port:** {rule['dst_port']}\n")
            if rule.get('fwd'):
                f.write(f"- **Forward To:** {rule['fwd']}\n")
            if rule.get('fwd_port'):
                f.write(f"- **Internal Port:** {rule['fwd_port']}\n")
            if rule.get('proto'):
                f.write(f"- **Protocol:** {rule['proto']}\n")
            
            f.write("\n")
    
    def _write_settings_section(self, f, settings: List[Dict[str, Any]]) -> None:
        """Write configuration settings section"""
        if not settings:
            return
        
        f.write("### Configuration Settings\n\n")
        
        # Group settings by key for better organization
        setting_groups = {}
        for setting in settings:
            key = setting.get('key', 'unknown')
            category = key.split('.')[0] if '.' in key else 'general'
            if category not in setting_groups:
                setting_groups[category] = []
            setting_groups[category].append(setting)
        
        for category, category_settings in setting_groups.items():
            f.write(f"#### {category.title()} Settings\n\n")
            for setting in category_settings[:10]:  # Limit for readability
                key = setting.get('key', 'Unknown')
                value = setting.get('value', 'N/A')
                f.write(f"- **{key}:** {value}\n")
            
            if len(category_settings) > 10:
                f.write(f"*... and {len(category_settings) - 10} more {category} settings*\n")
            f.write("\n")
    
    def _write_health_section(self, f, health: List[Dict[str, Any]]) -> None:
        """Write health and statistics section"""
        if not health:
            return
        
        f.write("### System Health\n\n")
        
        for health_item in health:
            subsystem = health_item.get('subsystem', 'Unknown')
            status = health_item.get('status', 'Unknown')
            
            f.write(f"- **{subsystem}:** {status}\n")
            
            if health_item.get('num_user'):
                f.write(f"  - Connected Users: {health_item['num_user']}\n")
            if health_item.get('num_guest'):
                f.write(f"  - Connected Guests: {health_item['num_guest']}\n")
            if health_item.get('tx_bytes-r'):
                f.write(f"  - TX Rate: {health_item['tx_bytes-r']} bytes/s\n")
            if health_item.get('rx_bytes-r'):
                f.write(f"  - RX Rate: {health_item['rx_bytes-r']} bytes/s\n")
        
        f.write("\n")
    
    def backup_existing_files(self, controller_name: str) -> None:
        """Backup existing documentation files with timestamp"""
        patterns = [
            f"unifi-{controller_name}-latest.md",
            f"unifi-{controller_name}-latest.json"
        ]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for pattern in patterns:
            existing_file = self.output_dir / pattern
            if existing_file.exists():
                backup_file = self.output_dir / f"{existing_file.stem}-backup-{timestamp}{existing_file.suffix}"
                shutil.copy2(existing_file, backup_file)
                self.logger.info(f"Backed up {existing_file} to {backup_file}")