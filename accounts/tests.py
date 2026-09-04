from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .forms import CustomUserCreationForm


class CustomUserCreationFormTest(TestCase):
    def test_unique_email_registration(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_duplicate_email_registration(self):
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password',
        )
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(
            form.errors['email'][0],
            "A user with that email already exists.",
        )

    def test_duplicate_email_case_insensitive(self):
        User.objects.create_user(
            username='existinguser',
            email='Existing@Example.Com',
            password='password',
        )
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(
            form.errors['email'][0],
            "A user with that email already exists.",
        )

    def test_successful_registration_creates_business(self):
        from businesses.models import Business

        url = reverse('register')
        form_data = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        response = self.client.post(url, data=form_data, follow=True)

        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username='testuser2')
        self.assertEqual(
            Business.objects.filter(owner=user).count(),
            1,
        )

        business = Business.objects.filter(owner=user).first()
        self.assertEqual(business.name, "My Business")

    def test_duplicate_email_no_business_created(self):
        from businesses.models import Business

        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password',
        )

        initial_user_count = User.objects.count()
        initial_business_count = Business.objects.count()

        url = reverse('register')
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }

        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), initial_user_count)
        self.assertEqual(
            Business.objects.count(),
            initial_business_count,
        )