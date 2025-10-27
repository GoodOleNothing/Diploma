# library/tests/test_all.py

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework.serializers import ValidationError
from django.contrib.auth import get_user_model

from library.models import Author, Book, Borrow, BookRequest
from library.serializers import (
    BorrowCreateSerializer,
    BookRequestCreateSerializer,
)

User = get_user_model()


# MODELS TESTS

class LibraryModelsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="pass1234")
        self.author = Author.objects.create(first_name="Bob", last_name="Bobovich")
        self.book = Book.objects.create(
            title="Test Book",
            author=self.author,
            total_copies=2,
            available_copies=2
        )

    def test_borrow_overdue_status(self):
        borrow = Borrow.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.now().date() - timedelta(days=1)
        )
        borrow.save()
        self.assertEqual(borrow.status, "overdue")

    def test_borrow_returned_status(self):
        borrow = Borrow.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.now().date() + timedelta(days=1)
        )
        borrow.status = "returned"
        borrow.save()
        self.assertEqual(borrow.status, "returned")

    def test_book_request_creation(self):
        br = BookRequest.objects.create(
            user=self.user,
            book=self.book,
            desired_due_date=timezone.now().date() + timedelta(days=10)
        )
        self.assertEqual(br.status, "pending")


# SERIALIZERS TESTS

class LibrarySerializersTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email="user2@example.com", password="pass1234")
        self.author = Author.objects.create(first_name="Bob", last_name="Bobovich")
        self.book = Book.objects.create(
            title="Another Book",
            author=self.author,
            total_copies=1,
            available_copies=1
        )

    def test_borrow_serializer_due_date_in_past(self):
        data = {
            "user": self.user.id,
            "book": self.book.id,
            "due_date": timezone.now().date() - timedelta(days=1)
        }
        serializer = BorrowCreateSerializer(data=data, context={"request": None})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_book_request_serializer_prevents_duplicate_pending(self):
        # Создаем первую заявку
        BookRequest.objects.create(
            user=self.user,
            book=self.book,
            desired_due_date=timezone.now().date() + timedelta(days=10)
        )
        # Пытаемся создать вторую заявку
        data = {
            "book": self.book.id,
            "desired_due_date": timezone.now().date() + timedelta(days=10)
        }
        serializer = BookRequestCreateSerializer(data=data, context={"request": type('obj', (object,), {'user': self.user})()})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


# VIEWS / API TESTS

class LibraryAPITest(TestCase):

    def setUp(self):
        Book.objects.all().delete()
        Author.objects.all().delete()
        self.client = APIClient()
        self.user = User.objects.create_user(email="user3@example.com", password="pass1234")
        self.admin_user = User.objects.create_user(email="admin@example.com", password="admin123")
        self.client.force_authenticate(user=self.user)

        self.author = Author.objects.create(first_name="Bob", last_name="Bobovich")
        self.book1 = Book.objects.create(title="Book 1", author=self.author, total_copies=1, available_copies=1)
        self.book2 = Book.objects.create(title="Book 2", author=self.author, total_copies=1, available_copies=1)

    def test_book_list(self):
        response = self.client.get("/api/library/books/")
        self.assertEqual(response.status_code, 200)

        data = response.json()["results"]
        titles = [book["title"] for book in data]

        self.assertIn("Book 1", titles)
        self.assertIn("Book 2", titles)

    def test_create_book_request(self):
        response = self.client.post("/api/library/book-requests/", data={
            "book": self.book1.id
        })
        self.assertEqual(response.status_code, 201)

        # Получаем последний объект BookRequest текущего пользователя
        book_request = BookRequest.objects.filter(user=self.user, book=self.book1).last()
        self.assertIsNotNone(book_request)
        self.assertEqual(book_request.status, "pending")

    def test_borrow_create_decreases_available_copies(self):
        from library.serializers import BorrowCreateSerializer
        data = {
            "user": self.user.id,
            "book": self.book2.id,
            "due_date": timezone.now().date() + timedelta(days=7)
        }
        serializer = BorrowCreateSerializer(data=data, context={"request": type('obj', (object,), {'user': self.user})()})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.book2.refresh_from_db()
        self.assertEqual(self.book2.available_copies, 0)
