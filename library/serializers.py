from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import Author, Book, Borrow, BookRequest
from django.utils import timezone


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = "__all__"


class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(read_only=True)

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
    """
    Используется для выдачи книги пользователю.
    """
    class Meta:
        model = Borrow
        fields = ("book", "due_date")

    def validate(self, attrs):
        book = attrs["book"]
        if book.available_copies < 1:
            raise serializers.ValidationError("Нет доступных экземпляров книги.")
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        # убираем book из validated_data, чтобы не передавать дважды
        book = validated_data.pop("book")

        # уменьшаем доступные копии книги
        book.available_copies -= 1
        book.save()

        # создаём Borrow
        borrow = Borrow.objects.create(
            user=user,
            book=book,
            status="borrowed",
            **validated_data  # book уже удалён из validated_data
        )
        return borrow


class BorrowReturnSerializer(serializers.ModelSerializer):
    """
    Используется для возврата книги.
    """

    class Meta:
        model = Borrow
        fields = ("id",)

    def update(self, instance, validated_data):
        if instance.status != "borrowed":
            raise serializers.ValidationError("Эта книга уже была возвращена.")

        instance.status = "returned"
        instance.returned_at = timezone.now()
        instance.save()

        # Возвращаем книгу на полку
        book = instance.book
        book.available_copies += 1
        book.save()

        return instance


class BookRequestCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = BookRequest
        fields = ("user", "book", "desired_due_date")
        validators = [
            UniqueTogetherValidator(
                queryset=BookRequest.objects.all(),
                fields=["user", "book"],
                message="Вы уже отправили заявку на эту книгу."
            )
        ]

    def validate(self, attrs):
        if attrs["desired_due_date"] <= timezone.now().date():
            raise serializers.ValidationError("Дата возврата должна быть позже сегодняшнего дня.")
        return attrs

    def create(self, validated_data):
        return BookRequest.objects.create(
            user=self.context["request"].user,
            **validated_data
        )


class BookRequestApproveSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookRequest
        fields = ("id",)

    def update(self, instance, validated_data):
        instance.status = "approved"
        instance.save()

        book = instance.book

        # Создаём Borrow с датой, указанной в заявке
        Borrow.objects.create(
            user=instance.user,
            book=book,
            due_date=instance.desired_due_date,
            status="borrowed"
        )

        # уменьшаем копии
        if book.available_copies > 0:
            book.available_copies -= 1
            book.save()

        return instance
