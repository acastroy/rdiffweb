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
Created on Apr 25, 2015

Module used to test the i18n tools. Check if translation are properly loaded.

@author: ikus060
"""

from __future__ import unicode_literals

from cherrypy import _cpconfig
import cherrypy
import gettext
import pkg_resources
import unittest

from rdiffweb import i18n
from rdiffweb.test import WebCase


class Test(unittest.TestCase):

    def setUp(self):
        self.mo_dir = pkg_resources.resource_filename('rdiffweb', 'locales')  # @UndefinedVariable
        cherrypy.request.config = _cpconfig.Config()

    def tearDown(self):
        pass

    def test_load_translation(self):
        # Load default translation
        i18n.get_lang(self.mo_dir, 'en_US', 'messages')
        t = cherrypy.response.i18n.trans
        l = cherrypy.response.i18n.locale
        self.assertIsInstance(t, gettext.GNUTranslations)
        self.assertEqual("en", l.language)

    def test_load_translation_with_accept_language_fr(self):
        # Mock a header
        cherrypy.request.headers["Accept-Language"] = "fr_CA,fr,en_en_US"
        # Load default translation
        i18n.get_lang(self.mo_dir, 'en_US', 'messages')
        t = cherrypy.response.i18n.trans
        l = cherrypy.response.i18n.locale
        self.assertIsInstance(t, gettext.GNUTranslations)
        self.assertEqual("fr", l.language)

    def test_load_translation_with_accept_language_unknown(self):
        # Mock a header
        cherrypy.request.headers["Accept-Language"] = "br_CA"
        # Load default translation
        i18n.get_lang(self.mo_dir, 'en_US', 'messages')
        t = cherrypy.response.i18n.trans
        l = cherrypy.response.i18n.locale
        self.assertIsInstance(t, gettext.GNUTranslations)
        self.assertEqual("en", l.language)

    def test_translation_with_fr(self):
        # Get trans
        i18n.get_lang(self.mo_dir, 'fr', 'messages')
        t = cherrypy.response.i18n.trans
        l = cherrypy.response.i18n.locale
        self.assertIsInstance(t, gettext.GNUTranslations)
        self.assertEqual("fr", l.language)
        # Test translation object
        self.assertEqual("Modifier", t.gettext("Edit"))
        # Check if the translation fallback
        self.assertEqual("Invalid String", t.gettext("Invalid String"))
        pass

    def test_translation_with_en(self):
        # Get trans
        i18n.get_lang(self.mo_dir, 'en', 'messages')
        t = cherrypy.response.i18n.trans
        l = cherrypy.response.i18n.locale
        self.assertIsInstance(t, gettext.GNUTranslations)
        self.assertEqual("en", l.language)
        pass

    def test_translation_with_en_us(self):
        # Get trans
        i18n.get_lang(self.mo_dir, 'en_US', 'messages')
        t = cherrypy.response.i18n.trans
        l = cherrypy.response.i18n.locale
        self.assertIsInstance(t, gettext.GNUTranslations)
        self.assertEqual("en", l.language)
        pass

    def test_translation_with_fr_ca(self):
        # Get trans
        i18n.get_lang(self.mo_dir, 'fr_CA', 'messages')
        t = cherrypy.response.i18n.trans
        l = cherrypy.response.i18n.locale
        self.assertIsInstance(t, gettext.GNUTranslations)
        self.assertEqual("fr", l.language)
        pass

    def test_translation_with_en_fr(self):
        # Get trans
        i18n.get_lang(self.mo_dir, 'en', 'messages')
        t = cherrypy.response.i18n.trans
        l = cherrypy.response.i18n.locale
        self.assertIsInstance(t, gettext.GNUTranslations)
        self.assertEqual("en", l.language)
        # Test translation object
        self.assertEqual("Edit", t.gettext("Edit"))
        # Check if the translation fallback
        self.assertEqual("Invalid String", t.gettext("Invalid String"))
        pass

    def test_translation_with_fr_en(self):
        # Get trans
        i18n.get_lang(self.mo_dir, 'fr', 'messages')
        t = cherrypy.response.i18n.trans
        l = cherrypy.response.i18n.locale
        self.assertIsInstance(t, gettext.GNUTranslations)
        self.assertEqual("fr", l.language)
        # Test translation object
        self.assertEqual("Modifier", t.gettext("Edit"))
        pass


class TestI18nWebCase(WebCase):

    reset_app = True

    def testLanguage_WithUnknown(self):
        #  Query the page without login-in
        self.getPage("/", headers=[("Accept-Language", "it")])
        self.assertStatus('200 OK')
        self.assertHeaderItemValue("Content-Language", "en_US")
        self.assertInBody("Sign in")

    def testLanguage_En(self):
        self.getPage("/", headers=[("Accept-Language", "en-US,en;q=0.8")])
        self.assertStatus('200 OK')
        self.assertHeaderItemValue("Content-Language", "en_US")
        self.assertInBody("Sign in")

    def testLanguage_EnFr(self):
        self.getPage("/", headers=[("Accept-Language", "en-US,en;q=0.8,fr-CA;q=0.8")])
        self.assertStatus('200 OK')
        self.assertHeaderItemValue("Content-Language", "en_US")
        self.assertInBody("Sign in")

    def testLanguage_Fr(self):
        self.getPage("/", headers=[("Accept-Language", "fr-CA;q=0.8,fr;q=0.6")])
        self.assertStatus('200 OK')
        self.assertHeaderItemValue("Content-Language", "fr_CA")
        self.assertInBody("Se connecter")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
