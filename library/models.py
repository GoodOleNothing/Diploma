from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Book(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    authors = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books", null=True,
                                verbose_name="Автор")
    description = models.TextField(blank=True, verbose_name="Описание")
    genre = models.CharField(max_length=100, blank=True, verbose_name="Жанр")
    total_copies = models.PositiveIntegerField(default=1, verbose_name="Всего копий")
    available_copies = models.PositiveIntegerField(default=1, verbose_name="Доступно копий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Добвалена")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Borrow(models.Model):
    STATUS_CHOICES = (
        ("borrowed", "Отдана"),
        ("returned", "Возвращена"),
        ("overdue", "Просрочена"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrows",
                             verbose_name="Пользователь")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrows", verbose_name="Книга")
    borrowed_at = models.DateField(auto_now_add=True, verbose_name="Отдана")
    due_date = models.DateField(verbose_name="До")
    returned_at = models.DateTimeField(null=True, blank=True, verbose_name="Возвращена")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="borrowed", verbose_name="Статус")

    class Meta:
        ordering = ["-borrowed_at"]


def default_due_date():
    return timezone.now().date() + timedelta(days=14)


class BookRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "В ожидании"),
        ("approved", "Одобрено"),
        ("rejected", "Отклонено"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="book_requests",
        verbose_name="Пользователь"
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="requests",
        verbose_name="Книга"
    )
    desired_due_date = models.DateField(verbose_name="Желаемая дата возврата", default=default_due_date)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "book")

    def __str__(self):
        return f"{self.user.email} → {self.book.title} ({self.status})"
