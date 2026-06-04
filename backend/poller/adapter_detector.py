"""
Physical Network Adapter Detection
Filters out VPN and virtual adapters using multiple methods
"""

import re
import socket
import subprocess
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import Windows-specific modules
try:
    import wmi
    import psutil
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    logger.warning("WMI or psutil not available, using fallback methods")

class AdapterDetector:
    """Detects physical network adapters, filtering out VPN/virtual interfaces"""
    
    # Keywords that indicate VPN or virtual adapters
    VPN_KEYWORDS = [
        'tap', 'tun', 'virtual', 'vpn', 'openvpn', 'wireguard', 
        'pia', 'nordlynx', 'cisco', 'anyconnect', 'secure', 
        'fortinet', 'pulse', 'juniper', 'globalprotect',
        'vmware', 'virtualbox', 'hyper-v', 'docker', 'ndis'
    ]
    
    # Known virtual adapter names (case-insensitive partial match)
    VIRTUAL_NAMES = [
        'isatap', 'teredo', 'microsoft wi-fi direct',
        'microsoft hosted network', 'bluetooth', 'loopback'
    ]
    
    def __init__(self):
        self.wmi_conn = None
        if WMI_AVAILABLE:
            try:
                self.wmi_conn = wmi.WMI()
                logger.info("WMI initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize WMI: {e}")
    
    def _is_vpn_adapter(self, name: str, description: str = "") -> bool:
        """Check if adapter name/description indicates VPN"""
        combined = f"{name} {description}".lower()
        
        # Check VPN keywords
        for keyword in self.VPN_KEYWORDS:
            if keyword in combined:
                logger.debug(f"Filtered VPN adapter: {name} (matched: {keyword})")
                return True
        
        # Check virtual names
        for virtual in self.VIRTUAL_NAMES:
            if virtual in combined:
                logger.debug(f"Filtered virtual adapter: {name} (matched: {virtual})")
                return True
        
        return False
    
    def _has_physical_mac(self, mac_address: str) -> bool:
        """Check if MAC address appears to be physical (not virtual)"""
        if not mac_address:
            return False
            
        # Common virtual MAC patterns
        virtual_mac_patterns = [
            r'^00:05:69',  # VMware
            r'^00:0C:29',  # VMware
            r'^00:50:56',  # VMware
            r'^00:1C:42',  # Parallels
            r'^08:00:27',  # VirtualBox
            r'^00:15:5D',  # Hyper-V
            r'^00:FF:FF',  # Virtual
        ]
        
        for pattern in virtual_mac_patterns:
            if re.match(pattern, mac_address, re.IGNORECASE):
                logger.debug(f"Filtered virtual MAC: {mac_address}")
                return False
        
        return True
    
    def get_physical_adapters_wmi(self) -> List[Dict]:
        """Get physical adapters using WMI (Windows only)"""
        if not self.wmi_conn:
            return []
        
        adapters = []
        try:
            # Query network adapters
            for nic in self.wmi_conn.Win32_NetworkAdapter():
                # Basic checks
                if not nic.Name or not nic.NetEnabled:
                    continue
                
                # WMI's PhysicalAdapter property (Windows 8+)
                is_physical = getattr(nic, 'PhysicalAdapter', False)
                
                # Additional filtering
                is_vpn = self._is_vpn_adapter(nic.Name, nic.Description or "")
                
                # Check if it has a physical MAC
                has_physical_mac = self._has_physical_mac(nic.MACAddress or "")
                
                # Decision logic
                if is_physical and not is_vpn and has_physical_mac:
                    adapters.append({
                        'id': nic.Index,
                        'name': nic.Name,
                        'description': nic.Description or "",
                        'mac': nic.MACAddress,
                        'speed': nic.Speed,
                        'manufacturer': nic.Manufacturer or "",
                        'interface_index': getattr(nic, 'InterfaceIndex', None)
                    })
                    logger.info(f"Found physical adapter: {nic.Name}")
                else:
                    logger.debug(f"Filtered adapter: {nic.Name} (physical={is_physical}, vpn={is_vpn}, mac_ok={has_physical_mac})")
                    
        except Exception as e:
            logger.error(f"WMI query failed: {e}")
        
        return adapters
    
    def get_physical_adapters_psutil(self) -> List[Dict]:
        """Fallback method using psutil and routing table"""
        adapters = []
        
        try:
            # Get network interface stats
            stats = psutil.net_if_stats()
            addresses = psutil.net_if_addrs()
            
            for name, stat in stats.items():
                # Basic filters
                if not stat.isup:  # Interface must be up
                    continue
                
                # Filter VPN/virtual
                if self._is_vpn_adapter(name):
                    continue
                
                # Get MAC address
                mac = None
                for addr in addresses.get(name, []):
                    if addr.family == psutil.AF_LINK:
                        mac = addr.address
                        break
                
                # Check physical MAC
                if mac and not self._has_physical_mac(mac):
                    continue
                
                adapters.append({
                    'id': hash(name),
                    'name': name,
                    'description': name,
                    'mac': mac,
                    'speed': stat.speed,
                    'manufacturer': "",
                    'interface_index': None
                })
                logger.info(f"Found physical adapter (psutil): {name}")
                
        except Exception as e:
            logger.error(f"psutil detection failed: {e}")
        
        return adapters
    
    def get_physical_adapters_route(self) -> List[Dict]:
        """Third fallback using route table to find default gateway interface"""
        adapters = []
        
        try:
            # Run route print command
            result = subprocess.run(
                ['route', 'print', '-4'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse output to find default gateway interface
            # Look for "0.0.0.0" entry with gateway
            lines = result.stdout.split('\n')
            default_gateway = None
            
            for line in lines:
                if '0.0.0.0' in line and '0.0.0.0' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        gateway = parts[2]
                        interface = parts[3]
                        default_gateway = {'gateway': gateway, 'interface': interface}
                        break
            
            if default_gateway:
                # Get interface name from IP
                try:
                    ip_result = subprocess.run(
                        ['ipconfig'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    # Parse adapter info (simplified)
                    adapters.append({
                        'id': 0,
                        'name': default_gateway['interface'],
                        'description': 'Default Gateway Interface',
                        'mac': None,
                        'speed': None,
                        'manufacturer': "",
                        'interface_index': None
                    })
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Route detection failed: {e}")
        
        return adapters
    
    def get_active_physical_adapter(self) -> Optional[Dict]:
        """Get the single best physical adapter to use for monitoring"""
        
        # Try methods in order of reliability
        adapters = []
        
        # Method 1: WMI (most reliable on Windows)
        if WMI_AVAILABLE:
            adapters = self.get_physical_adapters_wmi()
            if adapters:
                logger.info(f"Found {len(adapters)} adapter(s) via WMI")
                # Return first active physical adapter
                return adapters[0]
        
        # Method 2: psutil fallback
        adapters = self.get_physical_adapters_psutil()
        if adapters:
            logger.info(f"Found {len(adapters)} adapter(s) via psutil")
            return adapters[0]
        
        # Method 3: Route table fallback
        adapters = self.get_physical_adapters_route()
        if adapters:
            logger.info(f"Found {len(adapters)} adapter(s) via route table")
            return adapters[0]
        
        logger.error("No physical adapters found!")
        return None
    
    def get_all_adapters_info(self) -> List[Dict]:
        """Get all network adapters (including VPN) for debugging"""
        all_adapters = []
        
        try:
            if self.wmi_conn:
                for nic in self.wmi_conn.Win32_NetworkAdapter():
                    if nic.Name:
                        all_adapters.append({
                            'name': nic.Name,
                            'description': nic.Description,
                            'physical': getattr(nic, 'PhysicalAdapter', False),
                            'enabled': nic.NetEnabled,
                            'mac': nic.MACAddress
                        })
        except:
            pass
            
        return all_adapters

# Simple test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    detector = AdapterDetector()
    
    print("All adapters:")
    for adapter in detector.get_all_adapters_info():
        print(f"  - {adapter['name']} (physical: {adapter['physical']})")
    
    print("\nSelected physical adapter:")
    active = detector.get_active_physical_adapter()
    if active:
        print(f"  {active['name']} - {active['description']}")
    else:
        print("  None found")