#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import unittest

from datetime import datetime, timedelta

from pylookyloomonitoring import PyLookylooMonitoring, CaptureSettings


class TestBasic(unittest.TestCase):

    def setUp(self):
        self.client = PyLookylooMonitoring(root_url="http://127.0.0.1:5200")
        self.client.init_apikey('admin', 'admin')

    def test_up(self):
        self.assertTrue(self.client.is_up)
        self.assertTrue(self.client.redis_up())

    def test_instance_settings(self):
        settings = self.client.instance_settings()
        self.assertTrue('min_frequency' in settings, settings)
        self.assertTrue('max_captures' in settings, settings)
        self.assertTrue('force_expire' in settings, settings)

    def test_monitor_update(self) -> None:
        capture_settings: CaptureSettings = {'url': 'https://circl.lu'}
        monitor_uuid = self.client.monitor(capture_settings,
                                           frequency='hourly',
                                           expire_at=datetime.now() + timedelta(hours=2),
                                           collection="testing")
        monitor_uuid = self.client.update_monitor(monitor_uuid, frequency='daily')
        monitored = self.client.monitored('testing')
        for entry in monitored:
            if entry['uuid'] == monitor_uuid:
                settings = self.client.settings_monitor(monitor_uuid)
                self.assertEqual(settings['frequency'], 'daily', settings)
                break
        else:
            raise Exception(f'Unable to find {monitor_uuid}.')

    def test_monitor_expire(self) -> None:
        capture_settings: CaptureSettings = {'url': 'https://circl.lu'}
        monitor_uuid = self.client.monitor(capture_settings,
                                           frequency='hourly',
                                           expire_at=datetime.now() + timedelta(hours=2),
                                           collection="testing")
        collections = self.client.collections()
        self.assertTrue('testing' in collections)
        monitored = self.client.monitored('testing')
        self.assertTrue(monitor_uuid in [entry['uuid'] for entry in monitored], monitored)
        stop_monitored = self.client.stop_monitor(monitor_uuid)
        self.assertTrue(stop_monitored)
        # Need to wait for update_monitoring_queue to run
        time.sleep(10)
        expired = self.client.expired('testing')
        self.assertTrue(monitor_uuid in [entry['uuid'] for entry in expired], expired)
