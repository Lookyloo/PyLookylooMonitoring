#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import unittest

from datetime import datetime, timedelta

from pylookyloomonitoring import PyLookylooMonitoring, CaptureSettings


class TestBasic(unittest.TestCase):

    def setUp(self):
        self.client = PyLookylooMonitoring(root_url="http://127.0.0.1:5200")

    def test_up(self):
        self.assertTrue(self.client.is_up)
        self.assertTrue(self.client.redis_up())

    def test_monitor_expire(self):
        capture_settings: CaptureSettings = {'url': 'https://circl.lu'}
        monitor_uuid = self.client.monitor(capture_settings,
                                           frequency='hourly',
                                           expire_at=datetime.now() + timedelta(hours=2),
                                           collection="testing")
        collections = self.client.collections()
        self.assertTrue('testing' in collections)
        monitored = self.client.monitored('testing')
        self.assertTrue(monitor_uuid in [entry[0] for entry in monitored])
        stop_monitored = self.client.stop_monitor(monitor_uuid)
        self.assertTrue(stop_monitored)
        # Need to wait for update_monitoring_queue to run
        time.sleep(15)
        expired = self.client.expired('testing')
        self.assertTrue(monitor_uuid in [entry[0] for entry in expired], expired)
