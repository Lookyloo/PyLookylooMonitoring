#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from pylookyloomonitoring import PyLookylooMonitoring


class TestBasic(unittest.TestCase):

    def setUp(self):
        self.client = PyLookylooMonitoring(root_url="http://127.0.0.1:5200")

    def test_up(self):
        self.assertTrue(self.client.is_up)
        self.assertTrue(self.client.redis_up())
