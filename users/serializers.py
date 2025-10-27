from rest_framework import serializers

from library.serializers import BorrowSerializer
from users.models import User
from library.models import Borrow


class UserSerializer(serializers.ModelSerializer):
    borrows = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "password", "phone", "avatar", "city", "borrows")

    def get_borrows(self, obj):
        borrows_qs = Borrow.objects.filter(user=obj.id)
        if borrows_qs:
            return BorrowSerializer(borrows_qs, many=True).data
        return "Отсутствуют"


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("id", "email", "password", "phone", "avatar", "city")
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user



