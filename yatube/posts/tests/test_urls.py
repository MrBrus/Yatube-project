from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='PostAuthor'),
            text='Test text',
            group=Group.objects.create(
                title='Test title',
                description='Test description',
                slug='test-slug'
            )
        )

        cls.free_urls = {
            '/': HTTPStatus.OK,
            f'/group/{PostsURLTests.post.group.slug}/': HTTPStatus.OK,
            f'/posts/{PostsURLTests.post.pk}/': HTTPStatus.OK,
            f'/profile/{PostsURLTests.post.author}/': HTTPStatus.OK,
            '/unexisting/': HTTPStatus.NOT_FOUND,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{PostsURLTests.post.pk}/edit/': HTTPStatus.FOUND,
        }

    def setUp(self):
        # Создаем автора
        self.user = User.objects.get(username='PostAuthor')
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)
        # Создаем авторизованый клиент
        self.user2 = User.objects.create_user(username='test-user-second')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user2)

    def test_pages(self):
        """Страницы возвращают ожидаемый статус для неавторизованного
        пользователя"""
        for address, status_code in self.free_urls.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_create_post_non_auth_user(self):
        """Гости при попытке создания поста перенаправятся на вход"""
        response_guest = self.client.get('/create/')
        self.assertRedirects(response_guest, '/auth/login/?next=/create/')

    def test_edit_post_non_auth_user(self):
        """Гости не могут редактировать пост и перенаправятся"""
        response_guest = self.client.get(
            f'/posts/{PostsURLTests.post.pk}/edit/'
        )
        self.assertRedirects(response_guest,
                             f'/posts/{PostsURLTests.post.pk}/'
                             )

    def test_edit_post_non_author_user(self):
        """Авторизованный пользователь не может редактировать не свой пост"""
        response_authorized = self.authorized_client.get(
            f'/posts/{PostsURLTests.post.pk}/edit/')
        self.assertEqual(response_authorized.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response_authorized,
                             f'/posts/{PostsURLTests.post.pk}/'
                             )

    def test_create_authorized_user(self):
        """Авторизованные пользователи могут создать пост"""
        response_authorized = self.authorized_client.get('/create/')
        self.assertEqual(response_authorized.status_code, HTTPStatus.OK)

    def test_edit_by_author(self):
        """Редактирование доступно ТОЛЬКО автору"""
        response_author = self.authorized_client_author.get(
            f'/posts/{PostsURLTests.post.pk}/edit/'
        )
        self.assertEqual(response_author.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL использует нужный шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostsURLTests.post.group.slug}/':
                'posts/group_list.html',
            f'/profile/{PostsURLTests.post.author.username}/':
                'posts/profile.html',
            f'/posts/{PostsURLTests.post.pk}/': 'posts/post_detail.html',
            f'/posts/{PostsURLTests.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertTemplateUsed(response, template)
