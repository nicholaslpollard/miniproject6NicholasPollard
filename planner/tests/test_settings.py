# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

import os
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase

from config.settings import env_bool


class DeploymentSettingsTests(SimpleTestCase):
    def test_whitenoise_directly_after_security_middleware(self):
        middleware = settings.MIDDLEWARE
        security = middleware.index('django.middleware.security.SecurityMiddleware')
        self.assertEqual(middleware[security + 1], 'whitenoise.middleware.WhiteNoiseMiddleware')

    def test_csrf_middleware_still_enabled(self):
        self.assertIn('django.middleware.csrf.CsrfViewMiddleware', settings.MIDDLEWARE)

    def test_static_settings_preserved(self):
        self.assertEqual(settings.STATIC_URL, '/static/')  # Django prefixes 'static/' with '/'
        self.assertEqual(settings.STATIC_ROOT, settings.BASE_DIR / 'staticfiles')
        self.assertIn(settings.BASE_DIR / 'static', settings.STATICFILES_DIRS)
        self.assertEqual(
            settings.STORAGES['staticfiles']['BACKEND'], 'whitenoise.storage.CompressedStaticFilesStorage',
        )

    def test_session_and_csrf_cookies_share_secure_setting(self):
        self.assertEqual(settings.SESSION_COOKIE_SECURE, settings.SECURE_COOKIES)
        self.assertEqual(settings.CSRF_COOKIE_SECURE, settings.SECURE_COOKIES)

    def test_secret_key_is_not_django_insecure_default(self):
        self.assertFalse(settings.SECRET_KEY.startswith('django-insecure'))
        self.assertGreaterEqual(len(settings.SECRET_KEY), 50)

    def test_ssl_redirect_and_proxy_header_not_enabled(self):
        # Not enabled until the course reverse proxy's forwarded headers are verified.
        self.assertFalse(settings.SECURE_SSL_REDIRECT)
        self.assertIsNone(settings.SECURE_PROXY_SSL_HEADER)
        self.assertEqual(settings.SECURE_HSTS_SECONDS, 0)

    def test_runserver_nostatic_listed_before_staticfiles(self):
        # Required so runserver hands static files to WhiteNoise instead of Django.
        apps = settings.INSTALLED_APPS
        self.assertLess(
            apps.index('whitenoise.runserver_nostatic'), apps.index('django.contrib.staticfiles'),
        )

    def test_secure_cookies_default_follows_debug(self):
        # With no explicit override, cookies are secure exactly when DEBUG is off.
        if os.getenv('DJANGO_SECURE_COOKIES', '').strip():
            self.skipTest('DJANGO_SECURE_COOKIES is explicitly set in this environment.')
        # The test runner forces settings.DEBUG to False, so compare with the configured value.
        self.assertEqual(settings.SECURE_COOKIES, not env_bool('DJANGO_DEBUG', False))


class EnvBoolTests(SimpleTestCase):
    def test_true_values(self):
        for value in ('True', 'true', ' TRUE ', '1', 'yes'):
            with self.subTest(value=value), mock.patch.dict(os.environ, {'TEST_FLAG': value}):
                self.assertTrue(env_bool('TEST_FLAG', False))

    def test_false_values(self):
        for value in ('False', 'false', '0', 'no', 'off'):
            with self.subTest(value=value), mock.patch.dict(os.environ, {'TEST_FLAG': value}):
                self.assertFalse(env_bool('TEST_FLAG', True))

    def test_missing_or_blank_uses_default(self):
        with mock.patch.dict(os.environ, {'TEST_FLAG': '   '}):
            self.assertTrue(env_bool('TEST_FLAG', True))
            self.assertFalse(env_bool('TEST_FLAG', False))
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('TEST_FLAG', None)
            self.assertTrue(env_bool('TEST_FLAG', True))
