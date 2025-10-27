from django.contrib import admin
from users.models import User
from library.models import Author, Book, Borrow, BookRequest


@admin.register(User)
class User(admin.ModelAdmin):
    list_display = ('id', 'email', 'phone', 'avatar', 'city', 'is_active')


@admin.register(Author)
class Author(admin.ModelAdmin):
    list_display = ('id','first_name', 'last_name', 'bio')


@admin.register(Book)
class Book(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'description', 'genre', 'total_copies', 'available_copies', 'created_at')


@admin.register(Borrow)
class Borrow(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'borrowed_at', 'due_date', 'returned_at', 'status')


@admin.register(BookRequest)
class BookRequest(admin.ModelAdmin):
    list_display = ('id','user', 'book', 'desired_due_date', 'created_at', 'status')
