from django.db.models import F, Count
from django.utils import dateparse
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter

from theatre.models import (
    TheatreHall,
    Actor,
    Genre,
    Play,
    Performance,
    Reservation,
    Ticket
)
from theatre.permissions import IsAdminAllORAuthenticatedORReadOnly
from theatre.serializers import (
    TheatreHallSerializer,
    ActorSerializer,
    GenreSerializer,
    PlaySerializer,
    PerformanceSerializer,
    TicketSerializer,
    ReservationSerializer,
    ReservationListSerializer, PerformanceImageSerializer, PerformanceDetailSerializer, PerformanceListSerializer
)


class ReservationPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class TheatreHallViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer


class ActorViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class GenreViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class PlayViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Play.objects.all().order_by("title")
    serializer_class = PlaySerializer


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.all()
    serializer_class = PerformanceSerializer
    permission_classes = [IsAdminAllORAuthenticatedORReadOnly]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="play",
                type=str,
                description="Filter by play ID",
                required=False,
            ),
            OpenApiParameter(
                name="theatre_hall",
                type=str,
                description="Filter by theatre hall ID",
                required=False,
            ),
            OpenApiParameter(
                name="date",
                type=str,
                description="Filter by show date (YYYY-MM-DD)",
                required=False,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Retrieve a list of performances with optional filters."""
        queryset = self.queryset.select_related("play", "theatre_hall").annotate(
            tickets_available=F("theatre_hall__capacity") - Count("tickets")
        )

        play_id = request.query_params.get("play")
        theatre_hall_id = request.query_params.get("theatre_hall")
        date = request.query_params.get("date")

        if play_id:
            queryset = queryset.filter(play_id=play_id)
        if theatre_hall_id:
            queryset = queryset.filter(theatre_hall_id=theatre_hall_id)
        if date:
            try:
                parsed_date = dateparse.parse_date(date)
                if parsed_date is None:
                    raise ValueError
            except ValueError:
                return Response({"error": "Invalid date format."}, status=400)

        serializer = self.get_serializer(queryset.order_by("id"), many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve details of a specific performance along with occupied seats."""
        instance = self.get_object()
        taken_places = Ticket.objects.filter(performance=instance).values("row", "seat")
        serializer = self.get_serializer(instance)
        data = serializer.data
        data["taken_places"] = list(taken_places)
        return Response(data)

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAdminUser],
        url_path="upload-image",
    )
    def upload_image(self, request, pk=None):
        """Upload an image for a specific performance."""
        performance = self.get_object()
        serializer = PerformanceImageSerializer(performance, data=request.data)
        serializer.is_valid(
            raise_exception=True)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer
        if self.action == "retrieve":
            return PerformanceDetailSerializer
        if self.action == "upload_image":
            return PerformanceImageSerializer

        return PerformanceSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAdminAllORAuthenticatedORReadOnly]

    def get_queryset(self):
        """Filter tickets by authenticated user."""
        queryset = self.queryset.filter(reservation__user=self.request.user)
        return queryset


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = ReservationPagination

    def get_queryset(self):
        """Retrieve reservations for the authenticated user."""
        return self.queryset.filter(user=self.request.user).prefetch_related("tickets")

    def perform_create(self, serializer):
        """Create a new reservation for the authenticated user."""
        try:
            serializer.save(user=self.request.user)
        except Exception as e:
            raise ValidationError(f"Error creating reservation: {str(e)}")

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        """Retrieve a list of reservations for the authenticated user."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_destroy(self, instance: Reservation) -> None:
        """Cancel a reservation."""
        instance.delete()
