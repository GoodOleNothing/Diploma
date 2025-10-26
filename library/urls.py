from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, BookViewSet, BorrowViewSet, AuthorListAPIView, BookListAPIView, BorrowListAPIView, \
    BookRequestViewSet

app_name = "library"

router = DefaultRouter()
router.register("admin_authors", AuthorViewSet)
router.register("admin_books", BookViewSet)
router.register("admin_borrows", BorrowViewSet)
router.register("book-requests", BookRequestViewSet)
#urlpatterns = router.urls


urlpatterns = [
    path('', include(router.urls)),
    path('authors/', AuthorListAPIView.as_view(), name='authors-list'),
    path('books/', BookListAPIView.as_view(), name='books-list'),
    path('borrows/', BorrowListAPIView.as_view(), name='borrows-list'),
]
