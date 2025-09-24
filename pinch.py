#!/usr/bin/env python3
"""
Pinch - A CLI tool to add torrents to qBittorrent via Web API
"""

import argparse
import sys
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Tuple
from qbittorrent import Client
import imdb


def validate_magnet_link(magnet_link: str) -> bool:
    """Validate if the provided string is a valid magnet link."""
    magnet_pattern = r'^magnet:\?xt=urn:btih:[a-fA-F0-9]+.*'
    return bool(re.match(magnet_pattern, magnet_link))


def search_movie_imdb(movie_name: str) -> Optional[Dict]:
    """
    Search for a movie using IMDb and return movie details.
    
    Args:
        movie_name: The name of the movie to search for
        
    Returns:
        Movie details dict or None if not found
    """
    try:
        ia = imdb.IMDb()
        search_results = ia.search_movie(movie_name)
        
        if not search_results:
            print(f"❌ No movies found for '{movie_name}'")
            return None
        
        # Get the first result (most relevant)
        movie = search_results[0]
        ia.update(movie)
        
        print(f"🎬 Found movie: {movie.get('title', 'Unknown')} ({movie.get('year', 'Unknown')})")
        
        return {
            'title': movie.get('title', ''),
            'year': movie.get('year', ''),
            'imdb_id': movie.getID()
        }
        
    except Exception as e:
        print(f"❌ Error searching IMDb: {e}")
        return None


def search_yts_torrents(movie_title: str, year: str = "") -> List[Dict]:
    """
    Search for torrents on YTS.mx for a given movie using direct URL construction.
    
    Args:
        movie_title: The title of the movie
        year: The year of the movie (optional)
        
    Returns:
        List of torrent dictionaries with quality and magnet links
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Construct YTS URL following their format: yts.mx/movies/movie-name-year
        # Convert to lowercase, replace spaces with dashes, remove special characters
        movie_slug = movie_title.lower()
        movie_slug = re.sub(r'[^\w\s-]', '', movie_slug)  # Remove special characters except spaces and dashes
        movie_slug = re.sub(r'\s+', '-', movie_slug)      # Replace spaces with dashes
        movie_slug = re.sub(r'-+', '-', movie_slug)       # Replace multiple dashes with single dash
        movie_slug = movie_slug.strip('-')                # Remove leading/trailing dashes
        
        # Construct the direct URL
        if year:
            yts_url = f"https://yts.mx/movies/{movie_slug}-{year}"
        else:
            yts_url = f"https://yts.mx/movies/{movie_slug}"
        
        print(f"🔍 Trying direct YTS URL: {yts_url}")
        
        try:
            response = requests.get(yts_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we got a valid movie page (not a 404 or search page)
            if "404" in soup.get_text() or "not found" in soup.get_text().lower():
                print(f"❌ Movie not found at direct URL")
                return []
            
            print(f"📽️  Found movie page: {yts_url}")
            
            # Find torrent links
            torrents = []
            torrent_links = soup.find_all('a', href=re.compile(r'magnet:'))
            
            for link in torrent_links:
                magnet_link = link['href']
                quality_text = link.get_text().strip()
                
                # Extract quality information
                quality = extract_quality(quality_text)
                
                torrents.append({
                    'quality': quality,
                    'quality_text': quality_text,
                    'magnet': magnet_link,
                    'size': extract_size(link)
                })
            
            if torrents:
                return torrents
            else:
                print(f"❌ No torrents found on movie page")
                return []
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"❌ Movie not found at direct URL (404)")
                return []
            else:
                raise e
        
    except Exception as e:
        print(f"❌ Error searching YTS.mx: {e}")
        return []


def extract_quality(quality_text: str) -> str:
    """Extract quality from torrent text."""
    quality_text = quality_text.lower()
    
    if '2160p' in quality_text or '4k' in quality_text:
        return '2160p'
    elif '1080p' in quality_text:
        return '1080p'
    elif '720p' in quality_text:
        return '720p'
    elif '480p' in quality_text:
        return '480p'
    else:
        return 'unknown'


def extract_size(link_element) -> str:
    """Extract file size from torrent link element."""
    try:
        # Look for size in the parent element or nearby text
        parent = link_element.parent
        if parent:
            text = parent.get_text()
            # Look for patterns like "1.33 GB" or "2.73 GB"
            size_match = re.search(r'(\d+\.?\d*)\s*(GB|MB)', text, re.IGNORECASE)
            if size_match:
                return f"{size_match.group(1)} {size_match.group(2).upper()}"
            
            # Also look in the grandparent element
            grandparent = parent.parent
            if grandparent:
                text = grandparent.get_text()
                size_match = re.search(r'(\d+\.?\d*)\s*(GB|MB)', text, re.IGNORECASE)
                if size_match:
                    return f"{size_match.group(1)} {size_match.group(2).upper()}"
    except:
        pass
    return "Unknown size"


def select_best_torrent(torrents: List[Dict]) -> Optional[Dict]:
    """
    Select the best quality torrent from the list.
    Priority: 2160p > 1080p > 720p > 480p
    
    Args:
        torrents: List of torrent dictionaries
        
    Returns:
        Best torrent dict or None if no torrents
    """
    if not torrents:
        return None
    
    # Quality priority order
    quality_priority = ['2160p', '1080p', '720p', '480p']
    
    # Group torrents by quality
    quality_groups = {}
    for torrent in torrents:
        quality = torrent['quality']
        if quality not in quality_groups:
            quality_groups[quality] = []
        quality_groups[quality].append(torrent)
    
    # Find the best quality available
    for quality in quality_priority:
        if quality in quality_groups:
            # If multiple torrents of same quality, prefer x265/HEVC
            quality_torrents = quality_groups[quality]
            
            # Look for x265/HEVC versions first
            for torrent in quality_torrents:
                if 'x265' in torrent['quality_text'].lower() or 'hevc' in torrent['quality_text'].lower():
                    return torrent
            
            # If no x265, return the first one
            return quality_torrents[0]
    
    # If no known quality found, return the first torrent
    return torrents[0]


def search_and_add_movie(movie_name: str, host: str = "192.168.2.45", port: int = 8080) -> bool:
    """
    Search for a movie and add the best torrent to qBittorrent.
    
    Args:
        movie_name: The name of the movie to search for
        host: qBittorrent host address
        port: qBittorrent Web UI port
        
    Returns:
        True if successful, False otherwise
    """
    print(f"🎬 Searching for movie: {movie_name}")
    
    # Step 1: Search IMDb
    movie_info = search_movie_imdb(movie_name)
    if not movie_info:
        return False
    
    # Step 2: Search YTS for torrents
    torrents = search_yts_torrents(movie_info['title'], str(movie_info['year']))
    if not torrents:
        return False
    
    print(f"📥 Found {len(torrents)} torrent(s)")
    
    # Step 3: Select best torrent
    best_torrent = select_best_torrent(torrents)
    if not best_torrent:
        print("❌ No suitable torrent found")
        return False
    
    print(f"✅ Selected: {best_torrent['quality_text']} ({best_torrent['size']})")
    
    # Step 4: Add to qBittorrent
    return add_torrent(best_torrent['magnet'], host, port)


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
  pinch -m "The Matrix"
  pinch --movie "Inception 2010" --host 192.168.1.100
        """
    )
    
    # Create mutually exclusive group for magnet link vs movie search
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        'magnet_link',
        nargs='?',
        help='The magnet link to add to qBittorrent'
    )
    
    group.add_argument(
        '-m', '--movie',
        help='Search for a movie by name and add the best quality torrent'
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
    
    # Determine which action to take
    if args.movie:
        # Movie search mode
        success = search_and_add_movie(args.movie, args.host, args.port)
    else:
        # Direct magnet link mode
        success = add_torrent(args.magnet_link, args.host, args.port)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()