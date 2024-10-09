from rest_framework import serializers
from .models import TheatreHall, Actor, Genre, Play, Performance, Reservation, Ticket


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
    play_title = serializers.CharField(source='play.title', read_only=True)
    theatre_hall_name = serializers.CharField(
        source='theatre_hall.name', read_only=True
    )

    class Meta:
        model = Performance
        fields = (
            "id",
            "play",
            "theatre_hall",
            "show_time",
            "play_title",
            "theatre_hall_name"
        )

class ReservationSerializer(serializers.ModelSerializer):
    tickets = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Ticket.objects.all()
    )

    class Meta:
        model = Reservation
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        tickets_data = validated_data.pop('tickets')
        reservation = Reservation.objects.create(**validated_data)
        reservation.tickets.set(tickets_data)
        return reservation


class TicketSerializer(serializers.ModelSerializer):
    performance_title = serializers.CharField(
        source='performance.play.title', read_only=True
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
