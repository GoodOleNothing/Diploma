from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, BookViewSet, BorrowViewSet


app_name = "library"

router = DefaultRouter()
router.register("authors", AuthorViewSet)
router.register("books", BookViewSet)
router.register("borrows", BorrowViewSet)

urlpatterns = router.urls
