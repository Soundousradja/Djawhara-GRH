import os
import sqlite3
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class BackupRestoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='secret123',
            first_name='Test',
            last_name='User',
        )
        self.client.force_login(self.user)

    def test_backup_database_download(self):
        response = self.client.get(reverse('backup_database'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment; filename=', response.get('Content-Disposition', ''))

    def test_restore_database_upload(self):
        fd, temp_path = tempfile.mkstemp(suffix='.sqlite3')
        os.close(fd)
        conn = sqlite3.connect(temp_path)
        conn.execute('CREATE TABLE test_restore (id INTEGER PRIMARY KEY, name TEXT)')
        conn.execute('INSERT INTO test_restore (name) VALUES (?)', ('ok',))
        conn.commit()
        conn.close()

        with open(temp_path, 'rb') as f:
            uploaded = SimpleUploadedFile(
                'backup.sqlite3',
                f.read(),
                content_type='application/octet-stream',
            )

        response = self.client.post(
            reverse('restore_database'),
            {'backup_file': uploaded},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'sauvegarde restaurée')

        os.remove(temp_path)


class AuthLandingTests(TestCase):
    def test_auth_choice_page_displays_login_and_register_buttons(self):
        response = self.client.get(reverse('auth_choice'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Se connecter')
        self.assertContains(response, 'Créer un compte (responsable)')

    def test_responsible_can_self_register(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'responsable',
                'email': 'resp@example.com',
                'password1': 'Motdepasse123!',
                'password2': 'Motdepasse123!',
                'first_name': 'Chef',
                'last_name': 'Responsable',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username='responsable')
        self.assertEqual(user.profile.role, 'RH')

    def test_manager_can_create_other_user(self):
        manager = User.objects.create_user(
            username='responsable2',
            email='responsable2@example.com',
            password='secret123',
        )
        manager.profile.role = 'RH'
        manager.profile.save()
        self.client.force_login(manager)

        response = self.client.post(
            reverse('register'),
            {
                'username': 'nouvel_utilisateur',
                'email': 'new@example.com',
                'password1': 'Motdepasse123!',
                'password2': 'Motdepasse123!',
                'first_name': 'Nouveau',
                'last_name': 'Utilisateur',
                'role': 'CHEF',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username='nouvel_utilisateur')
        self.assertEqual(user.profile.role, 'CHEF')

    def test_manager_dashboard_shows_create_user_button(self):
        manager = User.objects.create_user(
            username='responsable_dashboard',
            email='respdash@example.com',
            password='secret123',
        )
        manager.profile.role = 'RH'
        manager.profile.save()
        self.client.force_login(manager)

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Créer un utilisateur')

    def test_non_limited_users_have_manager_permissions(self):
        user = User.objects.create_user(
            username='chef_access',
            email='chef@example.com',
            password='secret123',
        )
        user.profile.role = 'CHEF'
        user.profile.save()
        self.client.force_login(user)

        response = self.client.get(reverse('employee_create'))
        self.assertEqual(response.status_code, 200)
