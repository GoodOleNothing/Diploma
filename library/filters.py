import django_filters
from .models import Book, Borrow


class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    author = django_filters.CharFilter(field_name="author__last_name", lookup_expr="icontains")
    genre = django_filters.CharFilter(field_name="genre", lookup_expr="icontains")

    class Meta:
        model = Book
        fields = ["title", "author", "genre"]


class BorrowFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")

    class Meta:
        model = Borrow
        fields = ["status"]