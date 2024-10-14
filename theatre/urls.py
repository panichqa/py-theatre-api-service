from django.urls import path, include
from rest_framework import routers

from theatre.views import (
    PlayViewSet,
    ActorViewSet,
    TheatreHallViewSet,
    PerformanceViewSet,
    ReservationViewSet,
    TicketViewSet,
    GenreViewSet
)

router = routers.DefaultRouter()
router.register("plays", PlayViewSet)
router.register("actors", ActorViewSet)
router.register("theatre_halls", TheatreHallViewSet)
router.register("performances", PerformanceViewSet)
router.register("reservations", ReservationViewSet)
router.register("tickets", TicketViewSet)
router.register("genre", GenreViewSet)


urlpatterns = [
    path("", include(router.urls)),
]

app_name = "theatre"
