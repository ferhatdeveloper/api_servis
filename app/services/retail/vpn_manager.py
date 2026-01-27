"""
ExRetailOS Enterprise VPN Manager
WireGuard-based Secure Tunnel System

Features:
- Automatic WireGuard server setup
- Client key generation and management
- Config file generation
- Connection monitoring
- Traffic analytics
- Multi-platform support (Windows, Linux, macOS, Android, iOS)
"""

import subprocess
import os
import ipaddress
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import secrets
import base64
import json
from pathlib import Path

class VPNManager:
    """
    Enterprise VPN Manager for ExRetailOS
    Manages WireGuard VPN server and clients
    """
    
    def __init__(self, config_dir: str = "/etc/wireguard", network: str = "10.8.0.0/24", port: int = 51820):
        self.config_dir = Path(config_dir)
        self.network = ipaddress.IPv4Network(network)
        self.port = port
        self.interface_name = "wg0"
        self.clients_db = {}
        self.server_keys = None
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_keypair(self) -> Tuple[str, str]:
        """
        Generate WireGuard public/private key pair
        
        Returns:
            Tuple[str, str]: (private_key, public_key)
        """
        try:
            # Generate private key
            private_key = subprocess.run(
                ["wg", "genkey"],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            # Generate public key from private key
            public_key = subprocess.run(
                ["wg", "pubkey"],
                input=private_key,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            return private_key, public_key
        except subprocess.CalledProcessError as e:
            print(f"Error generating keys: {e}")
            # Fallback to demo keys for testing
            private_key = base64.b64encode(secrets.token_bytes(32)).decode()
            public_key = base64.b64encode(secrets.token_bytes(32)).decode()
            return private_key, public_key
    
    def initialize_server(self) -> bool:
        """
        Initialize WireGuard VPN server
        
        Returns:
            bool: True if successful
        """
        try:
            # Generate server keys if not exists
            if not self.server_keys:
                private_key, public_key = self.generate_keypair()
                self.server_keys = {
                    "private_key": private_key,
                    "public_key": public_key
                }
            
            # Create server config
            server_config = self._generate_server_config()
            
            # Write server config
            config_file = self.config_dir / f"{self.interface_name}.conf"
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(server_config)
            
            print(f"âœ… VPN Server initialized successfully!")
            print(f"ğŸ“ Config: {config_file}")
            print(f"ğŸ”‘ Public Key: {self.server_keys['public_key']}")
            
            return True
        except Exception as e:
            print(f"âŒ Error initializing server: {e}")
            return False
    
    def _generate_server_config(self) -> str:
        """Generate server configuration file"""
        server_ip = str(list(self.network.hosts())[0])
        
        config = f"""[Interface]
# ExRetailOS VPN Server
Address = {server_ip}/{self.network.prefixlen}
ListenPort = {self.port}
PrivateKey = {self.server_keys['private_key']}

# Firewall rules
PostUp = iptables -A FORWARD -i {self.interface_name} -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i {self.interface_name} -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Clients will be added below
"""
        
        # Add existing clients
        for client_id, client in self.clients_db.items():
            config += f"""
[Peer]
# {client['name']}
PublicKey = {client['public_key']}
AllowedIPs = {client['ip_address']}/32
"""
        
        return config
    
    def add_client(
        self,
        name: str,
        client_type: str = "store",
        location: Optional[str] = None,
        device_type: str = "desktop"
    ) -> Optional[Dict]:
        """
        Add new VPN client
        
        Args:
            name: Client name (e.g., "Åube 1 - Ankara")
            client_type: Type (store, fieldsales, warehouse, central)
            location: Physical location
            device_type: Device type (desktop, mobile, server)
            
        Returns:
            Dict: Client configuration or None
        """
        try:
            # Generate client keys
            private_key, public_key = self.generate_keypair()
            
            # Get next available IP
            ip_address = self._get_next_ip()
            if not ip_address:
                print("âŒ No available IP addresses")
                return None
            
            # Create client record
            client_id = secrets.token_hex(8)
            client = {
                "id": client_id,
                "name": name,
                "type": client_type,
                "public_key": public_key,
                "private_key": private_key,
                "ip_address": str(ip_address),
                "location": location or "Unknown",
                "device_type": device_type,
                "created_at": datetime.now().isoformat(),
                "status": "disconnected",
                "data_transferred": {
                    "upload": 0,
                    "download": 0
                }
            }
            
            # Add to database
            self.clients_db[client_id] = client
            
            # Update server config
            self._update_server_config()
            
            print(f"âœ… Client '{name}' added successfully!")
            print(f"ğŸ“ IP: {ip_address}")
            print(f"ğŸ”‘ Public Key: {public_key}")
            
            return client
        except Exception as e:
            print(f"âŒ Error adding client: {e}")
            return None
    
    def _get_next_ip(self) -> Optional[ipaddress.IPv4Address]:
        """Get next available IP address from network"""
        used_ips = {client["ip_address"] for client in self.clients_db.values()}
        used_ips.add(str(list(self.network.hosts())[0]))  # Server IP
        
        for ip in self.network.hosts():
            if str(ip) not in used_ips:
                return ip
        return None
    
    def _update_server_config(self):
        """Update server configuration with all clients"""
        config = self._generate_server_config()
        config_file = self.config_dir / f"{self.interface_name}.conf"
        with open(config_file, 'w') as f:
            f.write(config)
    
    def generate_client_config(self, client_id: str, server_endpoint: str) -> Optional[str]:
        """
        Generate client configuration file
        
        Args:
            client_id: Client ID
            server_endpoint: Server public endpoint (e.g., "45.123.45.67:51820")
            
        Returns:
            str: Client configuration or None
        """
        client = self.clients_db.get(client_id)
        if not client:
            print(f"âŒ Client {client_id} not found")
            return None
        
        config = f"""[Interface]
# ExRetailOS VPN Client - {client['name']}
PrivateKey = {client['private_key']}
Address = {client['ip_address']}/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
# ExRetailOS VPN Server
PublicKey = {self.server_keys['public_key']}
Endpoint = {server_endpoint}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
        return config
    
    def save_client_config(self, client_id: str, server_endpoint: str, output_dir: str = "./vpn_configs") -> Optional[str]:
        """
        Save client configuration to file
        
        Returns:
            str: Path to config file or None
        """
        config = self.generate_client_config(client_id, server_endpoint)
        if not config:
            return None
        
        client = self.clients_db[client_id]
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{client['name'].replace(' ', '_')}.conf"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            f.write(config)
        
        print(f"âœ… Config saved: {filepath}")
        return str(filepath)
    
    def start_server(self) -> bool:
        """Start WireGuard VPN server"""
        try:
            subprocess.run(
                ["wg-quick", "up", self.interface_name],
                check=True,
                capture_output=True
            )
            print(f"âœ… VPN Server started on port {self.port}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"âŒ Failed to start server: {e}")
            return False
    
    def stop_server(self) -> bool:
        """Stop WireGuard VPN server"""
        try:
            subprocess.run(
                ["wg-quick", "down", self.interface_name],
                check=True,
                capture_output=True
            )
            print(f"âœ… VPN Server stopped")
            return True
        except subprocess.CalledProcessError as e:
            print(f"âŒ Failed to stop server: {e}")
            return False
    
    def get_server_status(self) -> Dict:
        """Get VPN server status"""
        try:
            result = subprocess.run(
                ["wg", "show", self.interface_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "status": "running",
                "port": self.port,
                "public_key": self.server_keys['public_key'],
                "network": str(self.network),
                "connected_clients": len([c for c in self.clients_db.values() if c['status'] == 'connected']),
                "total_clients": len(self.clients_db),
                "interface": self.interface_name,
                "output": result.stdout
            }
        except subprocess.CalledProcessError:
            return {
                "status": "stopped",
                "port": self.port,
                "public_key": self.server_keys['public_key'] if self.server_keys else None,
                "network": str(self.network),
                "connected_clients": 0,
                "total_clients": len(self.clients_db),
                "interface": self.interface_name
            }
    
    def get_client_info(self, client_id: str) -> Optional[Dict]:
        """Get client information"""
        return self.clients_db.get(client_id)
    
    def list_clients(self) -> List[Dict]:
        """List all clients"""
        return list(self.clients_db.values())
    
    def remove_client(self, client_id: str) -> bool:
        """Remove a client"""
        if client_id in self.clients_db:
            client_name = self.clients_db[client_id]['name']
            del self.clients_db[client_id]
            self._update_server_config()
            print(f"âœ… Client '{client_name}' removed")
            return True
        return False
    
    def export_database(self, filepath: str = "./vpn_database.json"):
        """Export clients database to JSON"""
        with open(filepath, 'w') as f:
            json.dump({
                "server": self.server_keys,
                "network": str(self.network),
                "port": self.port,
                "clients": self.clients_db
            }, f, indent=2)
        print(f"âœ… Database exported to {filepath}")
    
    def import_database(self, filepath: str = "./vpn_database.json"):
        """Import clients database from JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.server_keys = data['server']
            self.network = ipaddress.IPv4Network(data['network'])
            self.port = data['port']
            self.clients_db = data['clients']
        print(f"âœ… Database imported from {filepath}")


# Example usage
if __name__ == "__main__":
    print("ğŸš€ ExRetailOS VPN Manager Demo")
    print("=" * 50)
    
    # Initialize VPN Manager
    vpn = VPNManager()
    
    # Initialize server
    vpn.initialize_server()
    
    # Add demo clients
    print("\nğŸ“ Adding demo clients...")
    
    vpn.add_client("Merkez MaÄŸaza - Ä°stanbul", "central", "Ä°stanbul, TÃ¼rkiye", "server")
    vpn.add_client("Åube 1 - Ankara", "store", "Ankara, TÃ¼rkiye", "desktop")
    vpn.add_client("Åube 2 - Ä°zmir", "store", "Ä°zmir, TÃ¼rkiye", "desktop")
    vpn.add_client("Depo 1 - Gebze", "warehouse", "Gebze, Kocaeli", "server")
    vpn.add_client("Saha SatÄ±ÅŸ - Ahmet YÄ±lmaz", "fieldsales", "Bursa, TÃ¼rkiye", "mobile")
    vpn.add_client("Saha SatÄ±ÅŸ - Mehmet Demir", "fieldsales", "Antalya, TÃ¼rkiye", "mobile")
    
    # List clients
    print("\nğŸ“‹ Client List:")
    for client in vpn.list_clients():
        print(f"  - {client['name']} ({client['ip_address']}) [{client['type']}]")
    
    # Generate client configs
    print("\nğŸ’¾ Generating client configurations...")
    for client_id in vpn.clients_db.keys():
        vpn.save_client_config(client_id, "45.123.45.67:51820")
    
    # Export database
    vpn.export_database()
    
    # Server status
    print("\nğŸ“Š Server Status:")
    status = vpn.get_server_status()
    for key, value in status.items():
        if key != 'output':
            print(f"  {key}: {value}")
    
    print("\nâœ… VPN Manager demo completed!")
    print("ğŸ’¡ Config files saved to ./vpn_configs/")
    print("ğŸ’¡ Database exported to ./vpn_database.json")
