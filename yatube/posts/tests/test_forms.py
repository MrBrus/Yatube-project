import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    context_reverses = reverse('posts:profile',
                               kwargs={'username': 'PostAuthor'})

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем автора
        self.user = User.objects.get(username='PostAuthor')
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_non_auth_create_post(self):
        """Неавторизованный юзер не создает пост"""
        posts_count = Post.objects.count()
        redirect_url = '/auth/login/?next=/create/'
        form_data = {
            'text': 'Test text trr trr',
            'group': self.group.id,
        }
        response = self.client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_add_comment_form(self):
        """Валидная форма коммента создает коммент к посту"""
        form_data = {
            'post': self.post,
            'author': self.authorized_client_author,
            'text': 'Big bad comment',
        }
        response = self.authorized_client_author.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertContains(response, form_data['text'])

    def test_add_comment_for_non_auth(self):
        """Неавторизованный не создаст коммент"""
        redirect_url = (f'/auth/login/?next=/posts/'
                        f'{PostCreateFormTests.post.pk}/comment/')
        form_data = {
            'post': self.post,
            'author': self.client,
            'text': 'Another big bad comment',
        }
        response = self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            redirect_url)

    def test_create_post_with_img(self):
        """Валидная форма создает запись."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Test text and tururu',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client_author.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.context_reverses)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(Post.objects.latest('id').text,
                         form_data['text'])
        self.assertEqual(Post.objects.latest('id').group.id,
                         form_data['group'])
        self.assertEqual(Post.objects.latest('id').image.name,
                         f"posts/{form_data['image'].name}")
        self.assertEqual(self.group.posts.count(),
                         posts_count + 1)

    def test_edit_post(self):
        """Проверка формы редактирования поста"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test text and another test text',
            'group': self.group.id
        }
        response = self.authorized_client_author.post(
            reverse(
                'posts:edit_post',
                kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            Post.objects.get(id=self.post.id).text, form_data[
                'text'])
        self.assertEqual(
            Post.objects.get(id=self.post.id).group.id,
            form_data['group'])
        self.assertEqual(Post.objects.count(), posts_count)
