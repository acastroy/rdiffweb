#!/usr/bin/python
# -*- coding: utf-8 -*-
# rdiffweb, A web interface to rdiff-backup repositories
# Copyright (C) 2018 rdiffweb contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Created on Nov 16, 2017

@author: Patrik Dufresne
"""

from __future__ import unicode_literals

import logging
import unittest

from rdiffweb.test import WebCase


class APITest(WebCase):

    login = True

    reset_app = True

    reset_testcases = True

    @classmethod
    def setup_server(cls):
        WebCase.setup_server(enabled_plugins=['SQLite'])

    def test_get_currentuser(self):
        data = self.getJson('/api/currentuser/')
        self.assertEqual(data.get('username'), 'admin')
        self.assertEqual(data.get('is_admin'), True)
        self.assertEqual(data.get('email'), '')
        # This value change on every execution.
        # self.assertEqual(data.get('user_root'), 'admin')
        self.assertIn('/tmp/rdiffweb_tests', data.get('user_root'))
        self.assertEqual(data.get('repos'), ['testcases/'])

    def test_get_currentuser_repos(self):
        data = self.getJson('/api/currentuser/repos')
        self.assertEqual(data, ['testcases/'])


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
