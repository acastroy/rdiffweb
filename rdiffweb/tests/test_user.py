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
Created on Oct 14, 2015

Module to test `user` module.

@author: ikus060
"""

from __future__ import unicode_literals

from builtins import str
import logging
from mock import MagicMock
from mockldap import MockLdap
import unittest

from rdiffweb.core import InvalidUserError, RdiffError
from rdiffweb.rdw_plugin import IUserChangeListener
from rdiffweb.test import AppTestCase


def _ldap_user(name, password='password'):
    """Create ldap entry to be mock."""
    assert isinstance(name, str)
    assert isinstance(password, str)
    return ('uid=%s,ou=People,dc=nodomain' % (name), {
        'uid': [name],
        'cn': [name],
        'userPassword': [password],
        'objectClass': ['person', 'organizationalPerson', 'inetOrgPerson', 'posixAccount']})


class UserManagerSQLiteTest(AppTestCase):

    def setUp(self):
        AppTestCase.setUp(self)
        self.mlistener = IUserChangeListener()
        self.mlistener.user_added = MagicMock()
        self.mlistener.user_attr_changed = MagicMock()
        self.mlistener.user_deleted = MagicMock()
        self.mlistener.user_logined = MagicMock()
        self.mlistener.user_password_changed = MagicMock()
        self.app.plugins._register_plugin('MockUserChangeListener', [self.mlistener.CATEGORY], self.mlistener)

    def test_add_user(self):
        """Add user to database."""
        user = self.app.userdb.add_user('joe')
        self.assertIsNotNone(user)
        self.assertTrue(self.app.userdb.exists('joe'))
        # Check if listener called
        self.mlistener.user_added.assert_called_once_with('joe', None)

    def test_add_user_with_duplicate(self):
        """Add user to database."""
        self.app.userdb.add_user('denise')
        with self.assertRaises(RdiffError):
            self.app.userdb.add_user('denise')
        # Check if listener called
        self.mlistener.user_added.assert_called_once_with('denise', None)

    def test_add_user_with_password(self):
        """Add user to database with password."""
        self.app.userdb.add_user('jo', 'password')
        self.assertTrue(self.app.userdb.exists('jo'))
        self.assertTrue(self.app.userdb.login('jo', 'password'))
        # Check if listener called
        self.mlistener.user_added.assert_called_once_with('jo', 'password')

    def test_delete_user(self):
        # Create user
        self.app.userdb.add_user('vicky', 'password')
        self.assertTrue(self.app.userdb.exists('vicky'))
        # Delete user
        self.assertTrue(self.app.userdb.delete_user('vicky'))
        self.assertFalse(self.app.userdb.exists('vicky'))
        # Check if listener called
        self.mlistener.user_deleted.assert_called_once_with('vicky')

    def test_delete_user_with_invalid_user(self):
        self.assertFalse(self.app.userdb.delete_user('eve'))
        # Check if listener called
        self.mlistener.user_deleted.assert_not_called()

    def test_exists(self):
        self.app.userdb.add_user('bob', 'password')
        self.assertTrue(self.app.userdb.exists('bob'))

    def test_exists_with_invalid_user(self):
        self.assertFalse(self.app.userdb.exists('invalid'))

    def test_get_user(self):
        """
        Test user record.
        """
        # Create new user
        user = self.app.userdb.add_user('bernie', 'my-password')
        user.user_root = '/backups/bernie/'
        user.is_admin = True
        user.email = 'bernie@gmail.com'
        user.repos = ['/backups/bernie/computer/', '/backups/bernie/laptop/']
        user.repo_list[0].maxage = -1
        user.repo_list[0].set_attr('newattribute', 'test1')
        user.get_repo('/backups/bernie/laptop/').maxage = 3
        user.get_repo('/backups/bernie/laptop/').set_attr('newattribute', 'test2')

        # Get user record.
        obj = self.app.userdb.get_user('bernie')
        self.assertIsNotNone(obj)
        self.assertEqual('bernie', obj.username)
        self.assertEqual('bernie@gmail.com', obj.email)
        self.assertEqual(['/backups/bernie/computer/', '/backups/bernie/laptop/'], obj.repos)
        self.assertEqual('/backups/bernie/', obj.user_root)
        self.assertEqual(True, obj.is_admin)

        # Get repo object
        self.assertEqual('/backups/bernie/computer/', obj.repo_list[0].name)
        self.assertEqual(-1, obj.repo_list[0].maxage)
        self.assertEqual('test1', obj.repo_list[0].get_attr('newattribute'))
        self.assertEqual('/backups/bernie/laptop/', obj.get_repo('/backups/bernie/laptop/').name)
        self.assertEqual(3, obj.get_repo('/backups/bernie/laptop/').maxage)
        self.assertEqual('test2', obj.get_repo('/backups/bernie/laptop/').get_attr('newattribute'))

    def test_get_attr_with_default(self):
        """
        Get repository attribute with default value.
        """
        user = self.app.userdb.add_user('mo', 'my-password')
        user.repos = ['/backups/bernie/computer/']
        value = user.get_repo('/backups/bernie/computer/').get_attr('newcolumn', default='coucou')
        self.assertEqual('coucou', value)

    def test_get_set(self):
        user = self.app.userdb.add_user('larry', 'password')

        self.assertEqual('', user.email)
        self.assertEqual([], user.repos)
        self.assertEqual('', user.user_root)
        self.assertEqual(False, user.is_admin)

        user.user_root = '/backups/'
        self.mlistener.user_attr_changed.assert_called_with('larry', {'user_root': '/backups/'})
        user.is_admin = True
        self.mlistener.user_attr_changed.assert_called_with('larry', {'is_admin': True})
        user.email = 'larry@gmail.com'
        self.mlistener.user_attr_changed.assert_called_with('larry', {'email': 'larry@gmail.com'})
        user.repos = ['/backups/computer/', '/backups/laptop/']
        self.mlistener.user_attr_changed.assert_called_with('larry', {'repos': ['/backups/computer/', '/backups/laptop/']})

        self.assertEqual('larry@gmail.com', user.email)
        self.assertEqual(['/backups/computer/', '/backups/laptop/'], user.repos)
        self.assertEqual('/backups/', user.user_root)
        self.assertEqual(True, user.is_admin)

    def test_list(self):
        self.assertEqual([], list(self.app.userdb.list()))
        self.app.userdb.add_user('annik')
        users = list(self.app.userdb.list())
        self.assertEqual(1, len(users))
        self.assertEqual('annik', users[0].username)

    def test_login(self):
        """Check if login work"""
        self.app.userdb.add_user('tom', 'password')
        self.assertIsNotNone(self.app.userdb.login('tom', 'password'))
        self.assertFalse(self.app.userdb.login('tom', 'invalid'))
        # Check if listener called
        self.mlistener.user_logined.assert_called_once_with('tom', 'password')

    def login_with_invalid_password(self):
        self.app.userdb.add_user('jeff', 'password')
        self.assertFalse(self.app.userdb.login('jeff', 'invalid'))
        # password is case sensitive
        self.assertFalse(self.app.userdb.login('jeff', 'Password'))
        # Match entire password
        self.assertFalse(self.app.userdb.login('jeff', 'pass'))
        self.assertFalse(self.app.userdb.login('jeff', ''))
        # Check if listener called
        self.mlistener.user_logined.assert_not_called()

    def test_login_with_invalid_user(self):
        """Check if login work"""
        self.assertIsNone(self.app.userdb.login('josh', 'password'))
        # Check if listener called
        self.mlistener.user_logined.assert_not_called()

    def test_search(self):
        """
        Check if search is working.
        """
        self.app.userdb.add_user('Charlie', 'password')
        self.app.userdb.add_user('Bernard', 'password')
        self.app.userdb.add_user('Kim', 'password')
        users = list(self.app.userdb.list())
        self.assertEqual(3, len(users))

    def test_set_password_update(self):
        self.app.userdb.add_user('annik', 'password')
        self.assertFalse(self.app.userdb.set_password('annik', 'new_password'))
        # Check new credentials
        self.assertIsNotNone(self.app.userdb.login('annik', 'new_password'))
        # Check if listener called
        self.mlistener.user_password_changed.assert_called_once_with('annik', 'new_password')

    def test_set_password_with_old_password(self):
        self.app.userdb.add_user('john', 'password')
        self.app.userdb.set_password('john', 'new_password', old_password='password')
        # Check new credentials
        self.assertIsNotNone(self.app.userdb.login('john', 'new_password'))
        # Check if listener called
        self.mlistener.user_password_changed.assert_called_once_with('john', 'new_password')

    def test_set_password_with_invalid_old_password(self):
        self.app.userdb.add_user('foo', 'password')
        with self.assertRaises(RdiffError):
            self.app.userdb.set_password('foo', 'new_password', old_password='invalid')
        # Check if listener called
        self.mlistener.user_password_changed.assert_not_called()

    def test_set_password_update_not_exists(self):
        """Expect error when trying to update password of invalid user."""
        with self.assertRaises(InvalidUserError):
            self.assertFalse(self.app.userdb.set_password('bar', 'new_password'))
        # Check if listener called
        self.mlistener.user_password_changed.assert_not_called()


class UserManagerSQLiteLdapTest(AppTestCase):

    basedn = ('dc=nodomain', {
        'dc': ['nodomain'],
        'o': ['nodomain']})
    people = ('ou=People,dc=nodomain', {
        'ou': ['People'],
        'objectClass': ['organizationalUnit']})

    # This is the content of our mock LDAP directory. It takes the form
    # {dn: {attr: [value, ...], ...}, ...}.
    directory = dict([
        basedn,
        people,
        _ldap_user('annik'),
        _ldap_user('bob'),
        _ldap_user('foo'),
        _ldap_user('jeff'),
        _ldap_user('john'),
        _ldap_user('karl'),
        _ldap_user('kim'),
        _ldap_user('larry'),
        _ldap_user('mike'),
        _ldap_user('tony'),
        _ldap_user('vicky'),
    ])

    enabled_plugins = ['Ldap', 'SQLite']

    default_config = {'LdapAllowPasswordChange': 'true'}

    @classmethod
    def setUpClass(cls):
        # We only need to create the MockLdap instance once. The content we
        # pass in will be used for all LDAP connections.
        cls.mockldap = MockLdap(cls.directory)

    @classmethod
    def tearDownClass(cls):
        del cls.mockldap

    def setUp(self):
        # Mock LDAP
        self.mockldap.start()
        self.ldapobj = self.mockldap['ldap://localhost/']
        # Original setup
        AppTestCase.setUp(self)
        # Get reference to LdapStore
        self.ldapstore = self.app.userdb._password_stores[0]

    def tearDown(self):
        # Stop patching ldap.initialize and reset state.
        self.mockldap.stop()
        del self.ldapobj
        AppTestCase.tearDown(self)

    def test_add_user_to_sqlite(self):
        """Add user to local database."""
        self.app.userdb.add_user('joe', 'password')
        user = self.app.userdb.login('joe', 'password')
        self.assertIsNotNone(user)
        self.assertEqual('joe', user.username)

    def test_add_user_to_ldap(self):
        """Add user to LDAP."""
        self.app.userdb.add_user('karl', 'password')
        user = self.app.userdb.login('karl', 'password')
        self.assertIsNotNone(user)
        self.assertEqual('karl', user.username)

    def test_delete_user(self):
        """Create then delete a user."""
        # Create user
        self.app.userdb.add_user('vicky')
        self.assertTrue(self.app.userdb.exists('vicky'))
        self.assertIsNotNone(self.app.userdb.login('vicky', 'password'))
        # Delete user.
        self.assertTrue(self.app.userdb.delete_user('vicky'))
        self.assertFalse(self.app.userdb.exists('vicky'))

    def test_delete_user_with_invalid_user(self):
        self.assertFalse(self.app.userdb.delete_user('eve'))

    def test_exists(self):
        """Check if user doesn't exists when only in LDAP."""
        self.assertFalse(self.app.userdb.exists('bob'))

    def test_exists_with_invalid_user(self):
        self.assertFalse(self.app.userdb.exists('invalid'))

    def test_get_set(self):
        username = 'larry'
        user = self.app.userdb.add_user(username, 'password')

        self.assertEqual('', user.email)
        self.assertEqual([], user.repos)
        self.assertEqual('', user.user_root)
        self.assertEqual(False, user.is_admin)

        user.user_root = '/backups/'
        user.is_admin = True
        user.email = 'larry@gmail.com'
        user.repos = ['/backups/computer/', '/backups/laptop/']

        user = self.app.userdb.get_user(username)
        self.assertEqual('larry@gmail.com', user.email)
        self.assertEqual(['/backups/computer/', '/backups/laptop/'], user.repos)
        self.assertEqual('/backups/', user.user_root)

    def test_list(self):
        self.assertEqual([], list(self.app.userdb.list()))
        self.app.userdb.add_user('annik')
        users = list(self.app.userdb.list())
        self.assertEqual('annik', users[0].username)

    def test_login(self):
        """Check if login work"""
        self.app.userdb.add_user('tom', 'password')
        self.assertIsNotNone(self.app.userdb.login('tom', 'password'))
        self.assertIsNone(self.app.userdb.login('tom', 'invalid'))

    def test_login_with_invalid_password(self):
        self.app.userdb.add_user('jeff', 'password')
        self.assertIsNone(self.app.userdb.login('jeff', 'invalid'))
        # password is case sensitive
        self.assertIsNone(self.app.userdb.login('jeff', 'Password'))
        # Match entire password
        self.assertIsNone(self.app.userdb.login('jeff', 'pass'))
        self.assertIsNone(self.app.userdb.login('jeff', ''))

    def test_login_with_invalid_user(self):
        """Check if login work"""
        self.assertIsNone(self.app.userdb.login('josh', 'password'))

    def test_login_with_invalid_user_in_ldap(self):
        """Check if login work"""
        self.assertIsNone(self.app.userdb.login('kim', 'password'))

    def test_login_with_create_user(self):
        """Check if login create the user in database if user exists in LDAP"""
        self.assertFalse(self.app.userdb.exists('tony'))
        self.app.cfg.set_config('AddMissingUser', 'true')
        try:
            user = self.app.userdb.login('tony', 'password')
            self.assertTrue(self.app.userdb.exists('tony'))
            self.assertFalse(user.is_admin)
        finally:
            self.app.cfg.set_config('AddMissingUser', 'false')

    def test_get_user_invalid(self):
        with self.assertRaises(InvalidUserError):
            self.app.userdb.get_user('invalid')

    def test_set_password_update(self):
        self.app.userdb.add_user('annik')
        self.assertFalse(self.app.userdb.set_password('annik', 'new_password'))
        # Check new credentials
        self.assertIsNotNone(self.app.userdb.login('annik', 'new_password'))

    def test_set_password_with_old_password(self):
        self.app.userdb.add_user('john')
        self.app.userdb.set_password('john', 'new_password', old_password='password')
        # Check new credentials
        self.assertIsNotNone(self.app.userdb.login('john', 'new_password'))

    def test_set_password_with_invalid_old_password(self):
        self.app.userdb.add_user('foo')
        with self.assertRaises(RdiffError):
            self.app.userdb.set_password('foo', 'new_password', old_password='invalid')

    def test_set_password_update_not_exists(self):
        """Expect error when trying to update password of invalid user."""
        with self.assertRaises(InvalidUserError):
            self.assertFalse(self.app.userdb.set_password('bar', 'new_password'))

    def test_supports(self):
        """Check basic supports"""
        self.assertTrue(self.app.userdb.supports('set_password'))
        self.assertTrue(self.app.userdb.supports('set_email'))
        self.assertTrue(self.app.userdb.supports('set_password', 'annik'))
        self.assertFalse(self.app.userdb.supports('set_email', 'annik'))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
