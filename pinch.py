#!/usr/bin/env python3
"""
Pinch - A CLI tool to add torrents to qBittorrent via Web API
"""

import argparse
import sys
import re
from typing import Optional
from qbittorrent import Client


def validate_magnet_link(magnet_link: str) -> bool:
    """Validate if the provided string is a valid magnet link."""
    magnet_pattern = r'^magnet:\?xt=urn:btih:[a-fA-F0-9]+.*'
    return bool(re.match(magnet_pattern, magnet_link))


def add_torrent(magnet_link: str, host: str = "192.168.2.45", port: int = 8080) -> bool:
    """
    Add a torrent to qBittorrent via Web API.
    
    Args:
        magnet_link: The magnet link to add
        host: The qBittorrent host address
        port: The qBittorrent Web UI port
        
    Returns:
        True if successful, False otherwise
    """
    # Validate magnet link
    if not validate_magnet_link(magnet_link):
        print(f"Error: Invalid magnet link format: {magnet_link}")
        return False
    
    print(f"✅ Magnet link validation passed")
    
    # Construct the qBittorrent Web API URL
    qb_url = f"http://{host}:{port}/"
    
    try:
        # Create qBittorrent client
        qb = Client(qb_url)
        
        print(f"Connecting to qBittorrent at {qb_url}...")
        
        # Try to add torrent without authentication first
        print("✅ Connected to qBittorrent (trying without authentication)")
        
        try:
            # Add the torrent
            print(f"Adding torrent: {magnet_link}")
            qb.download_from_link(magnet_link)
            print("✅ Torrent added successfully!")
            return True
        except Exception as add_error:
            if "Please login first" in str(add_error):
                print("⚠️  Authentication required, trying with default credentials...")
                try:
                    qb.login("368sherbrookee", "368sherbrookee")
                    qb.download_from_link(magnet_link)
                    print("✅ Torrent added successfully with your credentials!")
                    return True
                except Exception as login_error:
                    print(f"❌ Failed with your credentials: {login_error}")
                    raise add_error
            else:
                raise add_error
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
        # Provide helpful error messages
        if "Connection refused" in str(e) or "No connection" in str(e):
            print(f"💡 Make sure qBittorrent is running with Web UI enabled on {host}:{port}")
            print("💡 Check if the Web UI is accessible in your browser")
        elif "timeout" in str(e).lower():
            print("💡 Connection timed out - check if the host is reachable")
        elif "Please login first" in str(e):
            print("💡 Make sure 'Bypass authentication for clients on localhost' is enabled in qBittorrent")
        
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Add torrents to qBittorrent via Web API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pinch "magnet:?xt=urn:btih:abc123..."
  pinch --host 192.168.1.100 --port 8080 "magnet:?xt=urn:btih:def456..."
        """
    )
    
    parser.add_argument(
        'magnet_link',
        help='The magnet link to add to qBittorrent'
    )
    
    parser.add_argument(
        '--host',
        default='192.168.2.45',
        help='qBittorrent host address (default: 192.168.2.45)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='qBittorrent Web UI port (default: 8080)'
    )
    
    args = parser.parse_args()
    
    # Add the torrent
    success = add_torrent(args.magnet_link, args.host, args.port)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()