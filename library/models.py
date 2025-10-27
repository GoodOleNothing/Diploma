from django.db import models
from django.conf import settings
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from library.services import is_past_date


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
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books", null=True,
                                verbose_name="Автор")
    description = models.TextField(blank=True, verbose_name="Описание")
    genre = models.CharField(max_length=100, blank=True, verbose_name="Жанр")
    total_copies = models.PositiveIntegerField(default=1, verbose_name="Всего копий")
    available_copies = models.PositiveIntegerField(default=1, verbose_name="Доступно копий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Добвалена")

    class Meta:
        ordering = ["title"]

    def save(self, *args, **kwargs):
        # Если книга создаётся впервые — делаем доступные копии равными общим
        if self._state.adding:
            self.available_copies = self.total_copies
        else:
            # Если книга уже существует — не даём доступных копий быть больше total_copies
            if self.available_copies > self.total_copies:
                self.available_copies = self.total_copies

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


def default_due_date():
    return timezone.now().date() + timedelta(days=14)


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
    due_date = models.DateField(verbose_name="До", default=default_due_date)
    returned_at = models.DateTimeField(null=True, blank=True, verbose_name="Возвращена")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="borrowed", verbose_name="Статус")

    class Meta:
        ordering = ["-borrowed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "book"],
                condition=Q(status__in=["borrowed", "overdue"]),
                name="Только одна выданя книга на пользователя"
            )
        ]

    def save(self, *args, **kwargs):
        if self.status != "returned":
            if is_past_date(self.due_date):
                self.status = "overdue"
            else:
                self.status = "borrowed"
        super().save(*args, **kwargs)

    @property
    def current_status(self):
        """
        Возвращает актуальный статус:
        """
        if self.status == "returned":
            return "returned"
        if is_past_date(self.due_date):
            return "overdue"
        return self.status


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
    reject_reason = models.TextField(null=True, blank=True, verbose_name="Причина отказа")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} → {self.book.title} ({self.status})"
