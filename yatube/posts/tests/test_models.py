from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test text text text text text text',
        )

    def test_models_have_correct_str(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        self.assertEqual(group.title, str(group))
        post = PostModelTest.post
        self.assertEqual(post.text[:15], str(post))
