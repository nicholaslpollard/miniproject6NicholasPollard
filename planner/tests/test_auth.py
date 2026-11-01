# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()

# Throwaway password used only inside the temporary test database.
TEST_PASSWORD = 'Unit-Test-Passw0rd!'

# A fast hasher keeps these tests quick. It applies only to the test classes below;
# the real application keeps Django's default (PBKDF2) password hasher.
FAST_HASHER = override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])


@FAST_HASHER
class RegistrationTests(TestCase):
    url = reverse('planner:register')

    def post_registration(self, **overrides):
        data = {
            'username': 'newstudent',
            'email': 'newstudent@example.com',
            'password1': TEST_PASSWORD,
            'password2': TEST_PASSWORD,
        }
        data.update(overrides)
        return self.client.post(self.url, data)

    def test_register_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_successful_registration_creates_user_and_logs_in(self):
        response = self.post_registration()
        self.assertRedirects(response, reverse('planner:dashboard'))
        user = User.objects.get(username='newstudent')
        self.assertEqual(user.email, 'newstudent@example.com')
        self.assertTrue(user.check_password(TEST_PASSWORD))
        self.assertNotEqual(user.password, TEST_PASSWORD)  # stored hashed, not plain text
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_registration_cannot_create_staff_or_superuser(self):
        group = Group.objects.create(name='Editors')
        self.post_registration(
            is_staff='on', is_superuser='on', is_active='on',
            groups=[group.pk], user_permissions=['1'],
        )
        user = User.objects.get(username='newstudent')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.groups.exists())
        self.assertFalse(user.user_permissions.exists())

    def test_registered_user_cannot_access_admin(self):
        self.post_registration()
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith(reverse('admin:login')))

    def test_mismatched_passwords_rejected(self):
        response = self.post_registration(password2='Different-Passw0rd!')
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'password2', "The two password fields didn’t match.")
        self.assertFalse(User.objects.filter(username='newstudent').exists())

    def test_weak_password_rejected_by_validators(self):
        for weak in ('12345678', 'password', 'short'):
            with self.subTest(password=weak):
                response = self.post_registration(password1=weak, password2=weak)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                self.assertFalse(User.objects.filter(username='newstudent').exists())

    def test_password_similar_to_username_rejected(self):
        response = self.post_registration(username='studentname', password1='studentname1', password2='studentname1')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='studentname').exists())

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='newstudent')
        response = self.post_registration()
        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['form'].errors)
        self.assertEqual(User.objects.filter(username='newstudent').count(), 1)

    def test_missing_username_rejected(self):
        response = self.post_registration(username='')
        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['form'].errors)
        self.assertEqual(User.objects.count(), 0)

    def test_invalid_email_rejected(self):
        response = self.post_registration(email='not-an-email')
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.assertEqual(User.objects.count(), 0)

    def test_logged_in_user_redirected_away_from_register(self):
        self.client.force_login(User.objects.create_user(username='existing'))
        self.assertRedirects(self.client.get(self.url), reverse('planner:dashboard'))


@FAST_HASHER
class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student', password=TEST_PASSWORD)

    def test_login_page_loads(self):
        response = self.client.get(reverse('planner:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post(reverse('planner:login'), {'username': 'student', 'password': TEST_PASSWORD})
        self.assertRedirects(response, reverse('planner:dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_invalid_login_shows_error(self):
        response = self.client.post(reverse('planner:login'), {'username': 'student', 'password': 'wrong-password'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_follows_safe_next_url(self):
        next_url = reverse('planner:course_list')
        response = self.client.post(
            f"{reverse('planner:login')}?next={next_url}",
            {'username': 'student', 'password': TEST_PASSWORD, 'next': next_url},
        )
        self.assertRedirects(response, next_url)

    def test_login_ignores_external_next_url(self):
        for evil in ('https://evil.example/', '//evil.example/', 'http://evil.example/steal'):
            with self.subTest(next=evil):
                self.client.logout()
                response = self.client.post(
                    reverse('planner:login'),
                    {'username': 'student', 'password': TEST_PASSWORD, 'next': evil},
                )
                self.assertRedirects(response, reverse('planner:dashboard'))

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('planner:logout'))
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)  # still logged in

    def test_logout_with_post(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('planner:logout'))
        self.assertRedirects(response, reverse('planner:home'))
        self.assertNotIn('_auth_user_id', self.client.session)
        # Private pages require login again.
        self.assertEqual(self.client.get(reverse('planner:dashboard')).status_code, 302)

    def test_navbar_shows_logout_form_when_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('planner:home'))
        self.assertContains(response, f'action="{reverse("planner:logout")}"')
        self.assertContains(response, 'Signed in as')
        self.assertNotContains(response, f'href="{reverse("planner:register")}"', html=False)

    def test_navbar_shows_login_and_register_when_anonymous(self):
        response = self.client.get(reverse('planner:home'))
        self.assertContains(response, f'href="{reverse("planner:login")}"')
        self.assertContains(response, f'href="{reverse("planner:register")}"')
        self.assertNotContains(response, f'action="{reverse("planner:logout")}"')
