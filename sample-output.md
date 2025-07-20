# UniFi Network Documentation

**Controller:** main
**Host:** 192.168.1.1:443
**Generated:** 2025-07-20T13:45:00

---

## Controller Information

**Hostname:** unifi.local
**Version:** 8.0.26
**Build:** 7c03e4aed6c5d2
**Uptime:** 3456789 seconds

## Site: Default Site

**Description:** Default Site
**Site ID:** default

### Networks & VLANs

#### Default
- **Purpose:** corporate
- **VLAN ID:** 1
- **Subnet:** 192.168.1.0/24
- **DHCP Enabled:** True
- **DHCP Range:** 192.168.1.100 - 192.168.1.200
- **Domain:** home.local

#### Guest Network
- **Purpose:** guest
- **VLAN ID:** 10
- **Subnet:** 192.168.10.0/24
- **DHCP Enabled:** True
- **DHCP Range:** 192.168.10.50 - 192.168.10.200

#### IoT Network
- **Purpose:** vlan-only
- **VLAN ID:** 20
- **Subnet:** 192.168.20.0/24
- **DHCP Enabled:** True
- **DHCP Range:** 192.168.20.100 - 192.168.20.200

### WiFi Networks

#### Home-WiFi
- **Enabled:** Yes
- **SSID:** Home-WiFi
- **Security:** wpapsk
- **Network ID:** 6074991c2a5e7b056cd54321
- **Band:** both
- **WLAN Group:** Default

#### Guest-WiFi
- **Enabled:** Yes
- **SSID:** Guest-WiFi
- **Security:** wpapsk
- **Network ID:** 6074991c2a5e7b056cd54322
- **Band:** both
- **Guest Network:** Yes
- **WLAN Group:** Default

#### IoT-WiFi
- **Enabled:** Yes
- **SSID:** IoT-WiFi
- **Security:** wpapsk
- **Network ID:** 6074991c2a5e7b056cd54323
- **Band:** both
- **WLAN Group:** Default

### UniFi Devices

#### Access Point Devices

**Living Room AP**
- **Model:** U6-Pro
- **IP Address:** 192.168.1.10
- **MAC Address:** 44:d9:e7:12:34:56
- **State:** Connected
- **Firmware:** 6.5.55.13928
- **Uptime:** 345678 seconds

**Office AP**
- **Model:** U6-Lite
- **IP Address:** 192.168.1.11
- **MAC Address:** 44:d9:e7:78:90:12
- **State:** Connected
- **Firmware:** 6.5.55.13928
- **Uptime:** 234567 seconds

#### Switch Devices

**Main Switch**
- **Model:** USW-24-POE
- **IP Address:** 192.168.1.5
- **MAC Address:** 78:45:c4:23:45:67
- **State:** Connected
- **Firmware:** 6.5.60.13875
- **Uptime:** 456789 seconds

#### Gateway Devices

**Dream Machine**
- **Model:** UDM-Pro
- **IP Address:** 192.168.1.1
- **MAC Address:** 78:45:c4:89:01:23
- **State:** Connected
- **Firmware:** 3.2.9.14019
- **Uptime:** 567890 seconds

### Network Clients

#### Active Clients (25)
- **John-MacBook** (192.168.1.150) - 88:e9:fe:12:34:56
  - Network: Default
  - WiFi: Home-WiFi
- **iPhone-13** (192.168.1.151) - 3c:06:30:78:90:12
  - Network: Default
  - WiFi: Home-WiFi
- **Samsung-TV** (192.168.20.45) - 40:b0:76:34:56:78
  - Network: IoT Network
  - WiFi: IoT-WiFi
- **Google-Home** (192.168.20.46) - 48:d6:d5:90:12:34
  - Network: IoT Network
  - WiFi: IoT-WiFi
- **Work-Laptop** (192.168.10.55) - ac:bc:32:56:78:90
  - Network: Guest Network
  - WiFi: Guest-WiFi

*... and 20 more active clients*

#### Known/Configured Clients (12)
- **Server** - 52:54:00:12:34:56
  - Fixed IP: 192.168.1.10
  - Note: Home server
- **NAS** - 00:11:32:78:90:12
  - Fixed IP: 192.168.1.20
  - Note: Network storage
- **Printer** - 00:23:ae:34:56:78
  - Fixed IP: 192.168.1.25
  - Note: Home printer

*... and 9 more known clients*

### Firewall & Security

#### Firewall Groups
- **BlockedCountries** (address-group)
  - Members: 192.0.2.0/24, 198.51.100.0/24
- **TrustedDevices** (address-group)
  - Members: 192.168.1.10, 192.168.1.20

#### Firewall Rules

**Block IoT to LAN**
- **Action:** drop
- **Enabled:** Yes
- **Source:** 192.168.20.0/24
- **Destination:** 192.168.1.0/24
- **Protocol:** all

**Allow Guest Internet**
- **Action:** accept
- **Enabled:** Yes
- **Source:** 192.168.10.0/24
- **Destination:** any
- **Protocol:** all

**Block P2P**
- **Action:** drop
- **Enabled:** Yes
- **Port:** 6881-6999
- **Protocol:** tcp

### Port Forwarding (NAT Rules)

**Web Server**
- **Enabled:** Yes
- **External Port:** 80
- **Forward To:** 192.168.1.10
- **Internal Port:** 80
- **Protocol:** tcp

**SSH Server**
- **Enabled:** Yes
- **External Port:** 22
- **Forward To:** 192.168.1.10
- **Internal Port:** 22
- **Protocol:** tcp

**Plex Server**
- **Enabled:** Yes
- **External Port:** 32400
- **Forward To:** 192.168.1.20
- **Internal Port:** 32400
- **Protocol:** tcp

### Configuration Settings

#### Mgmt Settings
- **mgmt.autobackup.enabled:** true
- **mgmt.autobackup.days:** 7
- **mgmt.x_ssh_enabled:** true
- **mgmt.x_ssh_bind_wildcard:** false

*... and 5 more mgmt settings*

#### Auto Settings
- **auto_upgrade.enabled:** false
- **auto_speedtest.enabled:** true
- **auto_speedtest.interval:** 24

*... and 3 more auto settings*

#### Connectivity Settings
- **connectivity.uplink.type:** dhcp
- **connectivity.monitor.enabled:** true

*... and 4 more connectivity settings*

### System Health

- **wan:** ok
  - TX Rate: 125434 bytes/s
  - RX Rate: 876543 bytes/s
- **lan:** ok
  - Connected Users: 25
  - TX Rate: 345678 bytes/s
  - RX Rate: 234567 bytes/s
- **wlan:** ok
  - Connected Users: 18
  - Connected Guests: 3
  - TX Rate: 123456 bytes/s
  - RX Rate: 456789 bytes/s