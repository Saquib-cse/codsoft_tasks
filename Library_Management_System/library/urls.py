from rest_framework.routers import DefaultRouter

from .views import AuthorViewSet, BookViewSet, IssuedBookViewSet, MemberViewSet, ReportsView

router = DefaultRouter()
router.register(r"authors", AuthorViewSet, basename="author")
router.register(r"books", BookViewSet, basename="book")
router.register(r"members", MemberViewSet, basename="member")
router.register(r"issues", IssuedBookViewSet, basename="issue")
router.register(r"reports", ReportsView, basename="report")

urlpatterns = router.urls
