from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdministrator
from rest_framework.response import Response
from .models import Author, Book, Borrow, BookRequest
from .serializers import (
    AuthorSerializer, BookSerializer, BookCreateUpdateSerializer,
    BorrowSerializer, BorrowCreateSerializer, BorrowReturnSerializer,
    BookRequestCreateSerializer, BookRequestApproveSerializer, BookRequestSerializer
)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]


class AuthorListAPIView(generics.ListAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]
    #pagination_class = StandardResultsSetPagination


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return BookCreateUpdateSerializer
        return BookSerializer

    permission_classes = [IsAuthenticated, IsAdministrator]


class BookListAPIView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    #pagination_class = StandardResultsSetPagination


class BorrowViewSet(viewsets.ModelViewSet):
    queryset = Borrow.objects.all()
    permission_classes = [IsAuthenticated, IsAdministrator]

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowCreateSerializer
        return BorrowSerializer

    @action(detail=True, methods=["post"])
    def return_borrow(self, request, pk=None):
        borrow = self.get_object()
        serializer = BorrowReturnSerializer(borrow, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Книга успешно возвращена!"})


class BorrowListAPIView(generics.ListAPIView):
    serializer_class = BorrowSerializer
    permission_classes = [IsAuthenticated]
    #pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Borrow.objects.filter(user=self.request.user)


class BookRequestViewSet(viewsets.ModelViewSet):
    queryset = BookRequest.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return BookRequestCreateSerializer
        if self.action == "approve":
            return BookRequestApproveSerializer
        return BookRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="Administrator").exists():
            return BookRequest.objects.all()
        return BookRequest.objects.filter(user=user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdministrator])
    def approve(self, request, pk=None):
        request_obj = self.get_object()
        serializer = BookRequestApproveSerializer(request_obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Заявка одобрена, книга выдана!"})
