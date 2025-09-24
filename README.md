# Pinch

A simple CLI tool to add torrents to qBittorrent via Web API.

## Features

- Add magnet links to qBittorrent via Web API
- No SSH required - direct network connection
- Input validation for magnet links
- Configurable host, port, and credentials
- Clear success/error feedback

## Requirements

- Python 3.7+
- python-qbittorrent library (installed via requirements.txt)
- qBittorrent running with Web UI enabled
- Network access to the qBittorrent Web UI

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make the script executable:
   ```bash
   chmod +x pinch.py
   ```

## Usage

### Basic Usage

```bash
./pinch.py "magnet:?xt=urn:btih:abc123..."
```

### With Custom Host/Port

```bash
./pinch.py --host 192.168.1.100 --port 8080 "magnet:?xt=urn:btih:def456..."
```

### With Custom Credentials

```bash
./pinch.py --username myuser --password mypass "magnet:?xt=urn:btih:def456..."
```

### Command Line Options

- `magnet_link`: The magnet link to add (required)
- `--host`: qBittorrent host address (default: 192.168.2.45)
- `--port`: qBittorrent Web UI port (default: 8080)
- `--username`: Web UI username (default: admin)
- `--password`: Web UI password (default: adminadmin)

## Examples

```bash
# Add a torrent using default settings
./pinch.py "magnet:?xt=urn:btih:1234567890abcdef1234567890abcdef12345678"

# Add a torrent to a different host
./pinch.py --host 192.168.1.50 --port 8080 --username torrentuser --password mypass "magnet:?xt=urn:btih:abcdef1234567890abcdef1234567890abcdef12"
```

## How It Works

1. Validates the provided magnet link format
2. Connects to qBittorrent Web API using python-qbittorrent library
3. Authenticates with username/password
4. Adds the magnet link directly via Web API
5. Returns success/failure status with appropriate feedback

## Error Handling

The tool handles various error conditions:
- Invalid magnet link format
- Web API connection failures
- Authentication errors
- Network timeout scenarios

## Security Notes

- The tool uses HTTPS for secure communication (if qBittorrent is configured with SSL)
- Web UI credentials are passed as command-line arguments
- Consider using environment variables for sensitive credentials
- Ensure your qBittorrent Web UI is properly secured

## Troubleshooting

### Connection Issues
- Verify qBittorrent Web UI is accessible: `http://192.168.2.45:8080`
- Check if qBittorrent is running with Web UI enabled
- Ensure the host and port are correct

### Authentication Issues
- Verify your username and password are correct
- Check if Web UI authentication is enabled in qBittorrent settings
- Try accessing the Web UI in your browser first

### qBittorrent Setup
- Make sure qBittorrent is running with Web UI enabled
- Check qBittorrent settings: Tools → Options → Web UI
- Ensure the Web UI port (default: 8080) is not blocked by firewall
