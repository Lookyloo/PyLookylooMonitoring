#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from importlib.metadata import version
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Any, Union, TypedDict
from urllib.parse import urljoin, urlparse

import requests


class CaptureSettings(TypedDict, total=False):
    '''The capture settings that can be passed to Lookyloo.'''

    url: Optional[str]
    document_name: Optional[str]
    document: Optional[str]
    browser: Optional[str]
    device_name: Optional[str]
    user_agent: Optional[str]
    proxy: Optional[Union[str, Dict[str, str]]]
    general_timeout_in_sec: Optional[int]
    cookies: Optional[List[Dict[str, Any]]]
    headers: Optional[Union[str, Dict[str, str]]]
    http_credentials: Optional[Dict[str, int]]
    viewport: Optional[Dict[str, int]]
    referer: Optional[str]
    force: Optional[bool]
    recapture_interval: Optional[int]
    priority: Optional[int]

    listing: Optional[bool]


class CompareSettings(TypedDict, total=False):
    '''The settings that can be passed to the compare method on lookyloo side to filter out some differences'''

    ressources_ignore_domains: Optional[List[str]]
    ressources_ignore_regexes: Optional[List[str]]


class NotificationSettings(TypedDict, total=False):
    '''The notification settings for a monitoring'''

    email: str


class MonitorSettings(TypedDict, total=False):
    '''The settings for the capture we want to monitor'''

    capture_settings: CaptureSettings
    frequency: str
    expire_at: Optional[float]
    collection: Optional[str]
    compare_settings: Optional[CompareSettings]
    notification: Optional[NotificationSettings]


class MonitoringInstanceSettings(TypedDict):
    '''The settings of the monitoring instance.'''
    min_frequency: int
    max_captures: int
    force_expire: bool


class PyLookylooMonitoringException(Exception):
    ...


class TimeError(PyLookylooMonitoringException):
    ...


class PyLookylooMonitoring():

    def __init__(self, root_url: str, useragent: Optional[str]=None):
        '''Query a specific instance.

        :param root_url: URL of the instance to query.
        '''
        self.root_url = root_url

        if not urlparse(self.root_url).scheme:
            self.root_url = 'http://' + self.root_url
        if not self.root_url.endswith('/'):
            self.root_url += '/'
        self.session = requests.session()
        self.session.headers['user-agent'] = useragent if useragent else f'PyLookylooMonitoring / {version("pylookyloomonitoring")}'
        self.logger = logging.getLogger(f'{self.__class__.__name__}')

    @property
    def is_up(self) -> bool:
        '''Test if the given instance is accessible'''
        try:
            r = self.session.head(self.root_url)
        except requests.exceptions.ConnectionError:
            return False
        return r.status_code == 200

    def redis_up(self) -> Dict:
        '''Check if redis is up and running'''
        r = self.session.get(urljoin(self.root_url, 'redis_up'))
        return r.json()

    def collections(self) -> List[str]:
        """Get all the collections"""
        r = self.session.get(urljoin(self.root_url, str(Path('json', 'collections'))))
        return r.json()

    def monitored(self, collection: Optional[str]=None) -> List[Dict[str, Any]]:
        """Get the list of what is currently monitored.

        :param collection: Filter by collection
        """
        if collection:
            _path = str(Path('json', 'monitored', collection))
        else:
            _path = str(Path('json', 'monitored'))
        r = self.session.get(urljoin(self.root_url, _path))
        return r.json()

    def expired(self, collection: Optional[str]=None) -> List[Dict[str, Any]]:
        """Get the list of the capture we're not monitoring anymore.

        :param collection: Filter by collection
        """
        if collection:
            _path = str(Path('json', 'expired', collection))
        else:
            _path = str(Path('json', 'expired'))
        r = self.session.get(urljoin(self.root_url, _path))
        return r.json()

    def stop_monitor(self, uuid: str) -> bool:
        """Stop monitoring a specific capture

        :param uuid: the UUID we want to expire
        """
        r = self.session.post(urljoin(self.root_url, str(Path('stop_monitor', uuid))))
        return r.json()

    def changes(self, uuid: str) -> Dict[str, Any]:
        """Get the changes for a specific monitored capture.

        :param uuid: the UUID we want to get the changes
        """
        r = self.session.get(urljoin(self.root_url, str(Path('json', 'changes', uuid))))
        return r.json()

    def monitor(self, capture_settings: CaptureSettings, /, frequency: str, *,
                expire_at: Optional[Union[datetime, str, int, float]]=None,
                collection: Optional[str]=None,
                compare_settings: Optional[CompareSettings]=None,
                notification: Optional[NotificationSettings]=None) -> str:
        """Add a new capture to monitor.

        :param capture_settings: The settings of the capture
        :param frequency: The frequency of the monitoring
        :param expire_at: When the monitoring should expire.
        :param collection: The collection the monitored capture is part of.
        :param compare_settings: The comparison settings.
        :param notification: The notification settings.
        """
        to_post: MonitorSettings = {
            'capture_settings': capture_settings,
            'frequency': frequency
        }
        if expire_at:
            if isinstance(expire_at, (str, int, float)):
                _expire = float(expire_at)
            if isinstance(expire_at, datetime):
                _expire = expire_at.timestamp()
            if _expire < datetime.now().timestamp():
                # The expiration time is in the past.
                self.logger.warning(f'Expiration time in the past ({expire_at}), forcing it to tomorrow.')
                _expire = (datetime.now() + timedelta(hours=24)).timestamp()
            to_post['expire_at'] = _expire
        if collection:
            to_post['collection'] = collection
        if compare_settings:
            to_post['compare_settings'] = compare_settings
        if notification:
            to_post['notification'] = notification

        r = self.session.post(urljoin(self.root_url, 'monitor'), json=to_post)
        return r.json()

    def instance_settings(self) -> MonitoringInstanceSettings:
        """Get the settings of the monitoring instance."""
        r = self.session.get(urljoin(self.root_url, str(Path('json', 'settings'))))
        return r.json()
