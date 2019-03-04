import asyncio
import logging
import json
import voluptuous as vol
import sseclient
import requests
import time
from collections import defaultdict
from requests_toolbelt.utils import dump
from homeassistant.core import callback
import voluptuous as vol
from datetime import timedelta
from homeassistant.exceptions import TemplateError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change

from threading import Thread
from homeassistant.helpers import discovery
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.helpers.restore_state import RestoreEntity
_LOGGER = logging.getLogger(__name__)
from homeassistant.const import (STATE_ON, STATE_OFF)

from homeassistant.const import (
    CONF_NAME, CONF_PORT, CONF_PASSWORD)
import socketserver 
from datetime import datetime
import time
import logging
import threading
import sys
import re

from Crypto.Cipher import AES
from binascii import unhexlify,hexlify
from Crypto import Random
import random, string, base64
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util.dt import utcnow


import logging

import voluptuous as vol

from requests.exceptions import RequestException

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, CONF_PASSWORD, CONF_URL, CONF_USERNAME, STATE_IDLE,CONF_ENTITIES)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.exceptions import PlatformNotReady
REQUIREMENTS = ['python-qbittorrent==0.3.1']
from qbittorrent.client import Client, LoginRequired


DOMAIN = 'custom_qbittorrent'
DEFAULT_NAME = 'qBittorrent'

ENTITY_CONFIG = vol.Schema({
    vol.Required(CONF_URL): cv.url,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_ENTITIES, default={}):
            vol.All(cv.ensure_list, [ENTITY_CONFIG]),
     
    }),
}, extra=vol.ALLOW_EXTRA)

SENSOR_TYPE_CURRENT_STATUS = 'current_status'
SENSOR_TYPE_DOWNLOAD_SPEED = 'download_speed'
SENSOR_TYPE_UPLOAD_SPEED = 'upload_speed'

SENSOR_TYPES = {
    SENSOR_TYPE_CURRENT_STATUS: ['Status', None],
    SENSOR_TYPE_DOWNLOAD_SPEED: ['Down Speed', 'kB/s'],
    SENSOR_TYPE_UPLOAD_SPEED: ['Up Speed', 'kB/s'],
}

SERVICE_RESUME_DOWLOADS = 'resume_downloads'
SERVICE_PAUSE_DOWLOADS = 'pause_downloads'




def setup(hass, _config):          
    """Set up the qBittorrent sensors."""
    config = _config[DOMAIN]

    hass.data[DOMAIN] = {}

    for entity_config in config[CONF_ENTITIES]:
        qb = QBittorrent(hass, entity_config)
        hass.data[DOMAIN][qb.name] = qb


    for component in ['sensor']:
       discovery.load_platform(hass, component, DOMAIN, {}, config)

    def resume_downloads(call):
        hass.data[DOMAIN][call.data.get("name")].resume_downloads()

    def pause_downloads(call):
        hass.data[DOMAIN][call.data.get("name")].pause_downloads()
      
    hass.services.register(DOMAIN, SERVICE_RESUME_DOWLOADS, resume_downloads)
    hass.services.register(DOMAIN, SERVICE_PAUSE_DOWLOADS, pause_downloads)
    return True



def format_speed(speed):
    """Return a bytes/s measurement as a human readable string."""
    kb_spd = float(speed) / 1024
    return round(kb_spd, 2 if kb_spd < 0.1 else 1)


class QBittorrentSensor(Entity):
    """Representation of an qBittorrent sensor."""

    def __init__(self, sensor_type, qbittorrent_client,
                 client_name, exception):
        """Initialize the qBittorrent sensor."""
        self._name = SENSOR_TYPES[sensor_type][0]
        self.client = qbittorrent_client
        self.type = sensor_type
        self.client_name = client_name
        self._state = None
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._available = False
        self._exception = exception

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self.client_name, self._name)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def available(self):
        """Return true if device is available."""
        return self._available

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    async def async_update(self):
        """Get the latest data from qBittorrent and updates the state."""
        try:
            data = self.client.sync()
            self._available = True
        except RequestException:
            _LOGGER.error("Connection lost")
            self._available = False
            return
        except self._exception:
            _LOGGER.error("Invalid authentication")
            return

        if data is None:
            return

        download = data['server_state']['dl_info_speed']
        upload = data['server_state']['up_info_speed']

        if self.type == SENSOR_TYPE_CURRENT_STATUS:
            if upload > 0 and download > 0:
                self._state = 'up_down'
            elif upload > 0 and download == 0:
                self._state = 'seeding'
            elif upload == 0 and download > 0:
                self._state = 'downloading'
            else:
                self._state = STATE_IDLE

        elif self.type == SENSOR_TYPE_DOWNLOAD_SPEED:
            self._state = format_speed(download)
        elif self.type == SENSOR_TYPE_UPLOAD_SPEED:
            self._state = format_speed(upload)



class QBittorrent:
    def __init__(self, hass, config):
                
        try:
            self.client = Client(config[CONF_URL])
            self.client.login(config[CONF_USERNAME], config[CONF_PASSWORD])
        except LoginRequired:
            _LOGGER.error("Invalid authentication")
            return
        except RequestException:
            _LOGGER.error("Connection failed")
            raise PlatformNotReady

        self.sensors = []
        self.name = config.get(CONF_NAME)
        for sensor_type in SENSOR_TYPES:
            sensor = QBittorrentSensor(sensor_type, self.client, self.name, LoginRequired)
            self.sensors.append(sensor)


    def resume_downloads(self):
        self.client.resume_all()
    
    def pause_downloads(self):
        self.client.pause_all()

  