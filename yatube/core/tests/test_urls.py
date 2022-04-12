from django.test import TestCase, Client

from http import HTTPStatus


class CoresURLTests(TestCase):
    free_urls = [
        '/about/author/',
        '/about/tech/',
    ]

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    def test_free_pages(self):
        """Базовые страницы доступны любому пользователю"""
        for address in self.free_urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL использует нужный шаблон."""
        templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_404_page(self):
        """404 использует кастомный шаблон. Проверка соответствия статуса"""
        response = self.guest_client.get('/nononono/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

#    def test_403_page(self):
#        """403 использует кастомный шаблон. Проверка соответствия статуса"""
#        response = self.guest_client.get

#    def test_500_page(self):
#        """500 использует кастомный шаблон. Проверка соответствия статуса"""
#        response = self.guest_client.get
