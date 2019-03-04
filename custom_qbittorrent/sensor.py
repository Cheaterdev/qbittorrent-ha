import logging
import json

DOMAIN = 'custom_qbittorrent'
_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    for entity in hass.data[DOMAIN]:
        add_entities(hass.data[DOMAIN][entity].sensors)

