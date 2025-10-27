from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.relations import StringRelatedField
from rest_framework.validators import UniqueTogetherValidator

from .models import Author, Book, Borrow, BookRequest
from django.utils import timezone

from .services import is_past_date


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = "__all__"


class BookSerializer(serializers.ModelSerializer):
    authors = StringRelatedField(read_only=True)

    class Meta:
        model = Book
        fields = "__all__"


class BookCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"


class BorrowSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    book = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Borrow
        fields = "__all__"


class BorrowCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all())

    class Meta:
        model = Borrow
        fields = ("user", "book", "due_date")

    def validate_due_date(self, value):
        if is_past_date(value):
            raise serializers.ValidationError("Дата возврата не может быть в прошлом.")
        return value

    def validate(self, attrs):
        book = attrs["book"]
        user = attrs["user"]

        # Проверка доступных копий
        if book.available_copies < 1:
            raise serializers.ValidationError("Нет доступных экземпляров книги.")

        # Проверка, что у пользователя нет активного borrow на эту книгу
        if Borrow.objects.filter(user=user, book=book, status__in=["borrowed", "overdue"]).exists():
            raise serializers.ValidationError("У пользователя уже есть активный borrow для этой книги.")

        return attrs

    def create(self, validated_data):
        book = validated_data["book"]

        # уменьшаем доступные копии книги
        book.available_copies -= 1
        book.save()

        # создаём borrow
        borrow = Borrow.objects.create(**validated_data)
        return borrow


class BorrowReturnSerializer(serializers.ModelSerializer):
    """
    Используется для возврата книги.
    """

    class Meta:
        model = Borrow
        fields = ("id",)

    def update(self, instance, validated_data):
        if instance.status != "borrowed" and instance.status != "overdue":
            raise serializers.ValidationError("Эта книга уже была возвращена.")

        instance.status = "returned"
        instance.returned_at = timezone.now()
        instance.save()

        book = instance.book
        book.available_copies += 1
        book.save()

        return instance


class BookRequestSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    book = serializers.SerializerMethodField()

    class Meta:
        model = BookRequest
        fields = "__all__"

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "email": obj.user.email
        }

    def get_book(self, obj):
        return {
            "id": obj.book.id,
            "title": obj.book.title
        }


class BookRequestCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = BookRequest
        fields = ("user", "book", "desired_due_date")

    def validate(self, attrs):
        user = attrs["user"]
        book = attrs["book"]

        if BookRequest.objects.filter(user=user, book=book, status="pending").exists():
            raise serializers.ValidationError("У вас уже есть активная заявка на эту книгу.")

        from .models import Borrow
        if Borrow.objects.filter(user=user, book=book, status__in=["borrowed", "overdue"]).exists():
            raise serializers.ValidationError(
                "Вы не можете оставить заявку на эту книгу, пока она не возвращена."
            )

        desired_due_date = attrs.get("desired_due_date")
        if desired_due_date and is_past_date(desired_due_date):
            raise serializers.ValidationError("Дата возврата должна быть позже сегодняшнего дня.")

        return attrs

    def create(self, validated_data):
        return BookRequest.objects.create(**validated_data)


class BookRequestApproveSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookRequest
        fields = ("id",)

    def update(self, instance, validated_data):
        book = instance.book
        user = instance.user

        from .models import Borrow
        if Borrow.objects.filter(user=user, book=book, status__in=["borrowed", "overdue"]).exists():
            raise serializers.ValidationError(
                "Невозможно одобрить заявку: у пользователя уже есть активный экземпляр этой книги."
            )

        instance.status = "approved"
        instance.save()

        Borrow.objects.create(
            user=user,
            book=book,
            due_date=instance.desired_due_date,
            status="borrowed"
        )

        if book.available_copies > 0:
            book.available_copies -= 1
            book.save()

        return instance


class BookRequestRejectSerializer(serializers.ModelSerializer):
    reject_reason = serializers.CharField(required=True, help_text="Причина отклонения заявки")

    class Meta:
        model = BookRequest
        fields = ("reject_reason",)

    def update(self, instance, validated_data):
        if instance.status != "pending":
            raise serializers.ValidationError("Эта заявка уже обработана.")

        instance.status = "rejected"
        instance.reject_reason = validated_data["reject_reason"]
        instance.save()
        return instance
