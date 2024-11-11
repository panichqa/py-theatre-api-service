from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from theatre.models import TheatreHall, Actor, Genre, Play, Performance, Reservation, Ticket


class TheatreHallSerializer(serializers.ModelSerializer):

    class Meta:
        model = TheatreHall
        fields = '__all__'


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ("id", "name")


class PlaySerializer(serializers.ModelSerializer):

    actors = ActorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Play
        fields = (
            "id",
            "title",
            "actors",
            "genres",
            "description",
            "duration"
        )


class PerformanceSerializer(serializers.ModelSerializer):
    play_title = serializers.CharField(source="play.title", read_only=True)
    theatre_hall_name = serializers.CharField(
        source="theatre_hall.name", read_only=True
    )
    show_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Performance
        fields = (
            "id",
            "play",
            "theatre_hall",
            "show_time",
            "play_title",
            "theatre_hall_name",
            "image"
        )


class PerformanceListSerializer(serializers.ModelSerializer):
    play_title = serializers.CharField(source="play.title", read_only=True)
    theatre_hall_name = serializers.CharField(source="theatre_hall.name", read_only=True)
    show_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Performance
        fields = (
            "id",
            "show_time",
            "play_title",
            "theatre_hall_name",
            "image",
        )


class PerformanceDetailSerializer(serializers.ModelSerializer):
    taken_places = serializers.ListField(child=serializers.DictField())
    play_title = serializers.CharField(source="play.title", read_only=True)
    theatre_hall_name = serializers.CharField(source="theatre_hall.name", read_only=True)
    show_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Performance
        fields = ("id", "show_time", "play", "theatre_hall", "taken_places", "play_title", "theatre_hall_name")


class PerformanceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ["image"]


class TicketSerializer(serializers.ModelSerializer):
    performance_title = serializers.CharField(
        source="performance.play.title", read_only=True
    )

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "performance",
            "performance_title"
        )

        def validate(self, attrs):
            performance = attrs.get("performance")
            if performance:
                ticket = Ticket(**attrs)
                try:
                    ticket.full_clean()
                except ValidationError as e:
                    raise serializers.ValidationError(str(e))
            return attrs


class ReservationListSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%fZ")

    class Meta:
        model = Reservation
        fields = ("id", "tickets", "created_at")


class ReservationSerializer(serializers.ModelSerializer):
    tickets = serializers.PrimaryKeyRelatedField(many=True, queryset=Ticket.objects.all())
    performance = serializers.PrimaryKeyRelatedField(queryset=Performance.objects.all())

    class Meta:
        model = Reservation
        fields = ["id", "user", "performance", "tickets"]


    def create(self, validated_data):
        user = self.context["request"].user
        tickets_data = validated_data.pop("tickets")
        performance = validated_data.pop("performance")

        tickets = Ticket.objects.filter(id__in=[ticket.id for ticket in tickets_data])
        for ticket in tickets:
            if ticket.performance != performance:
                raise serializers.ValidationError("All tickets must be for the same performance.")

        with transaction.atomic():
            reservation = Reservation.objects.create(user=user)
            for ticket in tickets:
                ticket.reservation = reservation
                ticket.performance = performance
                ticket.full_clean()
                ticket.save()

        return reservation

