# qbittorrent-ha
qBittorrent integration into Home Assistant

Based on official home-assistant integration

## Features
- Sensors from oficial integration: status, download, upload
New:
- Pause all service
- Pesume all service

## Setup

Place "custom_qbittorrent" folder in **/custom_components** folder
	
```yaml
# configuration.yaml
    
custom_qbittorrent:
  entities:
   - url: **url**
     username:  **username**
     password: **password**
     name: **name**
  
```
Configuration variables:
- **url** (*Required*): qBittorrent url with port
- **username** (*Required*): Login to Web UI
- **password** (*Required*): Password to Web UI
- **name** (*Optional*): Name of entity. 

## Services

#custom_qbittorrent.pause_downloads
```json
{
	"name": "qBittorrent"
}
```

#custom_qbittorrent.resume_downloads
```json
{
	"name": "qBittorrent"
}
```

## Disclaimer
This software is supplied "AS IS" without any warranties and support.

