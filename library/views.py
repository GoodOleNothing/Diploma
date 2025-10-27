from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdministrator
from rest_framework.response import Response
from .pagination import StandardResultsSetPagination
from .filters import BookFilter, BorrowFilter
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Author, Book, Borrow, BookRequest
from .serializers import (
    AuthorSerializer, BookSerializer, BookCreateUpdateSerializer,
    BorrowSerializer, BorrowCreateSerializer, BorrowReturnSerializer,
    BookRequestCreateSerializer, BookRequestApproveSerializer, BookRequestSerializer, BookRequestRejectSerializer
)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]
    pagination_class = StandardResultsSetPagination


class AuthorListAPIView(generics.ListAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()

    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = BookFilter
    search_fields = ("title", "author__last_name", "genre")
    ordering_fields = ("title", "publication_year")
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return BookCreateUpdateSerializer
        return BookSerializer

    permission_classes = [IsAuthenticated, IsAdministrator]


class BookListAPIView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = BookFilter
    search_fields = ("title", "author__name", "genre")
    ordering_fields = ("title", "created_at")

    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]


class BorrowViewSet(viewsets.ModelViewSet):
    queryset = Borrow.objects.all()
    permission_classes = [IsAuthenticated, IsAdministrator]

    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = BorrowFilter
    search_fields = ("status",)
    ordering_fields = ("title", "created_at")
    pagination_class = StandardResultsSetPagination


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
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Borrow.objects.filter(user=self.request.user)


class BookRequestViewSet(viewsets.ModelViewSet):
    queryset = BookRequest.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return BookRequestCreateSerializer
        if self.action == "approve":
            return BookRequestApproveSerializer
        return BookRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="Administrator").exists():
            return BookRequest.objects.filter(status="pending")
        return BookRequest.objects.filter(user=user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdministrator])
    def approve(self, request, pk=None):
        request_obj = self.get_object()
        serializer = BookRequestApproveSerializer(request_obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Заявка одобрена, книга выдана!"})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdministrator])
    def reject(self, request, pk=None):
        request_obj = self.get_object()
        serializer = BookRequestRejectSerializer(request_obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Заявка отклонена!"})
