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
from blog.forms import EntryForm
from blog.models import Post

class SimpleTest(TestCase):
    fixtures = ['tests_users.json', 'tests_posts.json']

    def setUp(self):
        self.user = User.objects.get(id=1)
        self.client = Client()
        self.client.login(username='waylybaye', password='python4life')

    def tearDown(self):
        pass


    def test_blog(self):
        entry = Post.objects.create(
            user = self.user,
            title = "First Post",
            content = "Hello World",
        )


    def test_post(self):
        resp = self.client.get(reverse("blog:post"))
        self.assertTemplateUsed(resp, "blog/post.html")

#        resp = self.client.post(reverse("blog:post"))
#        self.assertFormError(resp, EntryForm, 'title', "This field is required")

        resp = self.client.post(reverse("blog:post"), {
            'title': "Test Post",
            'content': "Good Content",
        })

        self.failUnless( Post.objects.filter(title__exact="Test Post").count() )
        post = Post.objects.order_by('-id')[0]
        self.assertRedirects(resp, post.get_absolute_url())


    def test_index(self):
        resp = self.client.get('/')
        self.assertTemplateUsed(resp, "index.html")
