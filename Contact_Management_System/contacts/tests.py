from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Contact


class ContactAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(user=self.user)

    def test_create_contact(self):
        resp = self.client.post('/api/contacts/', {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone_number': '+911234567890',
            'company': 'Acme',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contact.objects.count(), 1)

    def test_duplicate_email_rejected(self):
        Contact.objects.create(
            owner=self.user, name='John', email='john@example.com',
            phone_number='+911111111111',
        )
        resp = self.client.post('/api/contacts/', {
            'name': 'John 2',
            'email': 'john@example.com',
            'phone_number': '+922222222222',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_phone_rejected(self):
        resp = self.client.post('/api/contacts/', {
            'name': 'Bad Phone',
            'email': 'bad@example.com',
            'phone_number': 'not-a-phone',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_users_only_see_their_own_contacts(self):
        Contact.objects.create(
            owner=self.other, name='Bobs Contact', email='x@example.com',
            phone_number='+933333333333',
        )
        resp = self.client.get('/api/contacts/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 0)

    def test_search_by_name(self):
        Contact.objects.create(
            owner=self.user, name='Jane Smith', email='jane@example.com',
            phone_number='+944444444444',
        )
        resp = self.client.get('/api/contacts/?search=Jane')
        self.assertEqual(resp.data['count'], 1)

    def test_update_and_delete(self):
        c = Contact.objects.create(
            owner=self.user, name='Update Me', email='upd@example.com',
            phone_number='+955555555555',
        )
        resp = self.client.patch(f'/api/contacts/{c.id}/', {'company': 'NewCo'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['company'], 'NewCo')

        resp = self.client.delete(f'/api/contacts/{c.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Contact.objects.count(), 0)

    def test_unauthenticated_blocked(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/contacts/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
