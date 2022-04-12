import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group
from ..views import POSTS_ON_PAGE

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PagesTest(TestCase):
    page_reverses = {
        reverse('posts:index'),
        reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
        reverse('posts:profile', kwargs={'username': 'PostAuthor'}),
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        batch_size = 13
        cls.group = Group.objects.create(
            title='Test title',
            description='Test description',
            slug='test-slug'
        )

        cls.author = User.objects.create_user(username='PostAuthor')
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.author,
            group=cls.group,
        )

        objs = (Post(author=cls.author,
                     text=f'Test text {i}{i}{i}',
                     group=cls.group
                     ) for i in range(1, batch_size))
        Post.objects.bulk_create(objs, batch_size)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем автора
        self.user = User.objects.get(username='PostAuthor')
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Проверка Паджинатора на главной, в группе, в профайле (первые 10
        постов)"""
        for pages in self.page_reverses:
            with self.subTest(pages=pages):
                response = self.authorized_client_author.get(
                    pages).context['page_obj']
                self.assertEqual(len(response), POSTS_ON_PAGE)

    def test_second_page_contains_three_records(self):
        """Проверка Паджинатора на главной, в группе, в профайле (
        оставшиеся посты)"""
        posts_count = Post.objects.count()
        for pages in self.page_reverses:
            pages_second = pages + '?page=2'
            with self.subTest(pages=pages_second):
                response = self.authorized_client_author.get(
                    pages_second).context['page_obj']
                self.assertEqual(len(response), (posts_count - POSTS_ON_PAGE))
