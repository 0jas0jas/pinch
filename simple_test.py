#!/usr/bin/env python3
"""
Simple test to debug the authentication issue
"""

from qbittorrent import Client

def test_simple():
    qb = Client('http://192.168.2.45:8080/')
    
    print("Testing basic connection...")
    
    try:
        # Try to get torrents without login
        torrents = qb.torrents()
        print(f"✅ Got torrents without login: {len(torrents)} found")
        return True
    except Exception as e:
        print(f"❌ Failed without login: {e}")
        
        # Try with login
        try:
            qb.login("368sherbrookee", "368sherbrookee")
            torrents = qb.torrents()
            print(f"✅ Got torrents with login: {len(torrents)} found")
            return True
        except Exception as e2:
            print(f"❌ Failed with login: {e2}")
            return False

if __name__ == "__main__":
    test_simple()
