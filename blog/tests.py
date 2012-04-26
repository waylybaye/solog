"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from django.test import TestCase
from django.test.client import Client
from django.test.testcases import LiveServerTestCase
from selenium import webdriver
from blog.models import Entry

class SimpleTest(TestCase):
    fixtures = ['tests_users.json']

    def setUp(self):
        self.user = User.objects.get(id=1)
        self.client = Client()
        self.client.login(username='waylybaye', password='python4life')

    def tearDown(self):
        pass


    def test_blog(self):
        entry = Entry.objects.create(
            user = self.user,
            title = "First Entry",
            content = "Hello World",
        )

        self.assertEqual(self.user.entries.count(), 1)


    def test_post(self):
        resp = self.client.post(reverse("blog:post"), {
            'title': "Test Post",
            'content': "Good Content",
        })
        post = Entry.objects.order_by('-id')[0]
        self.assertRedirects(resp, post.get_absolute_url())
