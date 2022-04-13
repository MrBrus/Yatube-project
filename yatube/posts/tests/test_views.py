import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.cache import cache

from ..forms import PostForm
from ..models import Post, Group, Comment, Follow
from ..views import POSTS_ON_PAGE

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PagesTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        batch_size = 13
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
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
            image=cls.image
        )
        objs = (Post(author=cls.author,
                     text='Test text',
                     group=cls.group,
                     image=cls.image
                     ) for i in range(1, 13))
        Post.objects.bulk_create(objs, batch_size)
        cls.author_2 = User.objects.create_user(username='PostAuthor2')
        cls.group_2 = Group.objects.create(
            title='Test title 2',
            description='Test description',
            slug='test-slug-2',
        )
        cls.form = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        cls.context_reverses = {
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': f'{PagesTest.group.slug}'}),
            reverse('posts:profile',
                    kwargs={'username': f'{PagesTest.author.username}'})
        }
        cls.comment = Comment.objects.create(
            post=cls.post, text="Big bad comment", author=cls.author
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем автора
        self.user = User.objects.get(username='PostAuthor')
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)
        # Создаем авторизованый клиент
        self.user2 = User.objects.create_user(username='test-user-second')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user2)

    def check_post(self, post):
        image = Post.objects.first().image
        self.assertEqual(post.text, 'Test text')
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group.title, 'Test title')
        self.assertEqual(post.image, image)

    def test_revers_pages(self):
        """Проверяем, что view-функции используют соответствующий шаблон"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'PostAuthor'}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse(
                'posts:edit_post',
                kwargs={'post_id': '1'}): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_profile_pages_show_correct_context(self):
        """Шаблоны index,group_list,profile  сформированы с правильным
        контекстом."""
        for reverse_context in self.context_reverses:
            with self.subTest(reverse_context=reverse_context):
                response = self.authorized_client_author.get(
                    reverse_context).context['page_obj'][0]
                self.check_post(response)

    def test_detail_post_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client_author.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        detail_post_context = response.context['post']
        expect_detail = PagesTest.post
        self.assertEqual(detail_post_context, expect_detail)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:create_post'))
        for field, expect_type in self.form.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expect_type)
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertFalse(response.context['is_edit'])

    def test_edit_post_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом"""
        response = self.authorized_client_author.get(
            reverse('posts:edit_post', kwargs={'post_id': self.post.pk}))
        for field, expect_type in self.form.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expect_type)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertTrue(response.context['is_edit'])

    def test_post_show_on_templates(self):
        """Пост появляется на главной, в группе, в профайле"""
        posts_count = Post.objects.count()
        for pages in self.context_reverses:
            pages_second = pages + '?page=2'
            with self.subTest(pages=pages_second):
                response = self.authorized_client_author.get(
                    pages_second).context['page_obj']
                self.assertEqual(len(response), (posts_count - POSTS_ON_PAGE))

    def test_post_not_shown_in_wrong_templates(self):
        """Пост не появится в неправильной группе/профиле"""
        response_bad_profile = self.authorized_client_author.get(
            reverse('posts:profile', kwargs={'username': 'PostAuthor2'}))
        response_bad_group = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug-2'}))
        self.assertEqual(len(response_bad_profile.context['page_obj']), 0)
        self.assertEqual(len(response_bad_group.context['page_obj']), 0)

    def test_post_detail_with_comment(self):
        """Новый комментарий появился на странице поста"""
        self.authorized_client_author.post(f'/posts/'
                                           f'{self.post.pk}/',
                                           {'text': self.comment.text},
                                           follow=True)
        expect_detail = self.comment.text
        response = self.client.get(f'/posts/{self.post.pk}/')
        self.assertContains(response, expect_detail)

    def test_cache_index(self):
        """Тест кэширования страницы index.html"""
        first_get = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(pk=self.post.id)
        post_1.text = 'Changed text'
        post_1.save()
        second_get = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_get.content, second_get.content)
        cache.clear()
        third_get = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_get.content, third_get.content)

    def test_follow(self):
        """Проверка подписки"""
        self.authorized_client.post(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}
        ))
        self.assertTrue(Follow.objects.filter(
            user=self.user2,
            author=self.user
        ).exists())

    def test_unfollow(self):
        """Проверка отписки"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}
        ))
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username}
        ))
        self.assertFalse(Follow.objects.filter(
            user=self.user2,
            author=self.user
        ).exists())

    def test_subscriber_follow_index_page(self):
        """Посты появляются в лентах подписчиков"""
        self.post = Post.objects.create(
            author=self.user,
            text='Test text for my lovely followers!'
        )
        Follow.objects.create(user=self.user2,
                              author=self.user)
        response = self.authorized_client.get('/follow/')
        post_text = response.context['page_obj'][0].text
        self.assertEqual(post_text, 'Test text for my lovely followers!')
        response = self.authorized_client_author.get('/follow/')
        self.assertNotContains(response, 'Test text for my lovely followers!')
