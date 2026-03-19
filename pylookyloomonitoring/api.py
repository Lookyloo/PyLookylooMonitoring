#!/usr/bin/env python3

from __future__ import annotations

import logging

from importlib.metadata import version
from datetime import datetime
from pathlib import Path
from typing import TypedDict, Any
from urllib.parse import urljoin, urlparse

import requests

from lookyloo_models import LookylooCaptureSettings, CompareSettings, NotificationSettings, MonitorCaptureSettings


class MonitoringInstanceSettings(TypedDict):
    '''The settings of the monitoring instance.'''
    min_frequency: int
    max_captures: int
    force_expire: bool


class PyLookylooMonitoringException(Exception):
    ...


class TimeError(PyLookylooMonitoringException):
    ...


class AuthError(PyLookylooMonitoringException):
    ...


class PyLookylooMonitoring():

    def __init__(self, root_url: str, useragent: str | None=None,
                 *, proxies: dict[str, str] | None=None):
        '''Query a specific instance.

        :param root_url: URL of the instance to query.
        :param useragent: The User Agent used by requests to run the HTTP requests against the monitoring, it is *not* passed to the captures.
        :param proxies: The proxies to use to connect to lookyloo (not the ones given to the capture itself) - More details: https://requests.readthedocs.io/en/latest/user/advanced/#proxies
        '''
        self.root_url = root_url

        if not urlparse(self.root_url).scheme:
            self.root_url = 'http://' + self.root_url
        if not self.root_url.endswith('/'):
            self.root_url += '/'
        self.session = requests.session()
        self.session.headers['user-agent'] = useragent if useragent else f'PyLookylooMonitoring / {version("pylookyloomonitoring")}'
        if proxies:
            self.session.proxies.update(proxies)
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.apikey: str | None = None

    def get_apikey(self, username: str, password: str) -> dict[str, str]:
        '''Get the API key for the given user.'''
        to_post = {'username': username, 'password': password}
        r = self.session.post(urljoin(self.root_url, str(Path('json', 'get_token'))), json=to_post)
        return r.json()

    def init_apikey(self, username: str | None=None, password: str | None=None, apikey: str | None=None) -> None:
        '''Init the API key for the current session. All the requests against the monitoring instance after this call will be authenticated.'''
        if apikey:
            self.apikey = apikey
        elif username and password:
            t = self.get_apikey(username, password)
            if 'authkey' in t:
                self.apikey = t['authkey']
        else:
            raise AuthError('Username and password required')
        if self.apikey:
            self.session.headers['Authorization'] = self.apikey
        else:
            raise AuthError('Unable to initialize API key')

    @property
    def is_up(self) -> bool:
        '''Test if the given instance is accessible'''
        try:
            r = self.session.head(self.root_url, timeout=2)
        except requests.exceptions.ConnectionError:
            return False
        return r.status_code == 200

    def redis_up(self) -> dict[str, Any]:
        '''Check if redis is up and running'''
        r = self.session.get(urljoin(self.root_url, 'redis_up'))
        return r.json()

    def collections(self) -> list[str]:
        """Get all the collections"""
        r = self.session.get(urljoin(self.root_url, str(Path('json', 'collections'))))
        return r.json()

    def monitored(self, collection: str | None=None) -> list[dict[str, Any]]:
        """Get the list of what is currently monitored.

        :param collection: Filter by collection
        """
        if collection:
            _path = str(Path('json', 'monitored', collection))
        else:
            _path = str(Path('json', 'monitored'))
        r = self.session.get(urljoin(self.root_url, _path))
        return r.json()

    def expired(self, collection: str | None=None) -> list[dict[str, Any]]:
        """Get the list of the capture we're not monitoring anymore.

        :param collection: Filter by collection
        """
        if collection:
            _path = str(Path('json', 'expired', collection))
        else:
            _path = str(Path('json', 'expired'))
        r = self.session.get(urljoin(self.root_url, _path))
        return r.json()

    def settings_monitor(self, uuid: str) -> MonitorCaptureSettings:
        """Get the settings of a specific monitoring.

        :param uuid: The UUID we want the settings of.
        """
        r = self.session.get(urljoin(self.root_url, str(Path('settings_monitor', uuid))))
        return MonitorCaptureSettings(**r.json())

    def stop_monitor(self, uuid: str) -> bool | dict[str, str]:
        """Stop monitoring a specific capture

        :param uuid: the UUID we want to expire
        """
        if not self.apikey:
            raise AuthError('You need to initialize the apikey to use this method (see init_apikey)')
        r = self.session.post(urljoin(self.root_url, str(Path('stop_monitor', uuid))))
        return r.json()

    def start_monitor(self, uuid: str) -> bool | dict[str, str]:
        """(re)Start monitoring a specific capture

        :param uuid: the UUID we want to (re)start to monitor
        """
        if not self.apikey:
            raise AuthError('You need to initialize the apikey to use this method (see init_apikey)')
        r = self.session.post(urljoin(self.root_url, str(Path('start_monitor', uuid))))
        return r.json()

    def changes(self, uuid: str) -> dict[str, Any]:
        """Get the changes for a specific monitored capture.

        :param uuid: the UUID we want to get the changes
        """
        r = self.session.get(urljoin(self.root_url, str(Path('json', 'changes', uuid))))
        return r.json()

    def update_monitor(self, monitor_uuid: str, *,
                       capture_settings: LookylooCaptureSettings | dict[str, Any] | None=None,
                       frequency: str | None=None,
                       expire_at: datetime | str | int | float | None=None,
                       never_expire: bool = False,
                       collection: str | None=None,
                       compare_settings: CompareSettings | dict[str, Any] | None=None,
                       notification: NotificationSettings | dict[str, Any] | None=None) -> str:

        _cs: LookylooCaptureSettings | None
        _comp_s: CompareSettings | None
        _ns: NotificationSettings | None
        if isinstance(capture_settings, dict):
            _cs = LookylooCaptureSettings(**capture_settings)
        else:
            _cs = capture_settings

        if isinstance(compare_settings, dict):
            _comp_s = CompareSettings(**compare_settings)
        else:
            _comp_s = compare_settings

        if isinstance(notification, dict):
            _ns = NotificationSettings(**notification)
        else:
            _ns = notification

        to_post = MonitorCaptureSettings(
            capture_settings=_cs,
            frequency=frequency,
            expire_at=expire_at,
            never_expire=never_expire,
            collection=collection,
            compare_settings=_comp_s,
            notification=_ns
        )
        r = self.session.post(urljoin(self.root_url, str(Path('update_monitor', monitor_uuid))),
                              data=to_post.model_dump_json())
        return r.json()

    def monitor(self, capture_settings: LookylooCaptureSettings | dict[str, Any], /, frequency: str, *,
                expire_at: datetime | str | int | float | None=None,
                never_expire: bool=False,
                collection: str | None=None,
                compare_settings: CompareSettings | dict[str, Any] | None=None,
                notification: NotificationSettings | dict[str, Any] | None=None) -> str:
        """Add a new capture to monitor.

        :param capture_settings: The settings of the capture
        :param frequency: The frequency of the monitoring
        :param expire_at: When the monitoring should expire.
        :param never_expire: If True, the capture will never expire.
        :param collection: The collection the monitored capture is part of.
        :param compare_settings: The comparison settings.
        :param notification: The notification settings.
        """
        _cs: LookylooCaptureSettings | None
        _comp_s: CompareSettings | None
        _ns: NotificationSettings | None
        if isinstance(capture_settings, dict):
            _cs = LookylooCaptureSettings(**capture_settings)
        else:
            _cs = capture_settings

        if isinstance(compare_settings, dict):
            _comp_s = CompareSettings(**compare_settings)
        else:
            _comp_s = compare_settings

        if isinstance(notification, dict):
            _ns = NotificationSettings(**notification)
        else:
            _ns = notification

        to_post = MonitorCaptureSettings(
            capture_settings=_cs,
            frequency=frequency,
            never_expire=never_expire,
            expire_at=expire_at,
            collection=collection,
            compare_settings=_comp_s,
            notification=_ns
        )
        r = self.session.post(urljoin(self.root_url, 'monitor'), data=to_post.model_dump_json())
        return r.json()

    def instance_settings(self) -> MonitoringInstanceSettings:
        """Get the settings of the monitoring instance."""
        r = self.session.get(urljoin(self.root_url, str(Path('json', 'settings'))))
        return r.json()
