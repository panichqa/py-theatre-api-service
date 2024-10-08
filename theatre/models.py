from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils import timezone


class TheatreHall(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Play(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.IntegerField()
    image = models.ImageField(null=True, upload_to="play/%Y/%m/%d")
    actors = models.ManyToManyField(Actor, related_name="plays")
    genres = models.ManyToManyField(Genre, related_name="plays")


    def __str__(self):
        return self.title


class Performance(models.Model):
    play = models.ForeignKey(Play, on_delete=models.CASCADE)
    theatre_hall = models.ForeignKey(TheatreHall, on_delete=models.CASCADE)
    show_time = models.DateTimeField()

    def clean(self):
        if self.show_time < timezone.now():
            raise ValidationError("The display time cannot be in the past.")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["play", "theatre_hall", "show_time"], name="unique_performance"
            )
        ]


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE)

    def clean(self):
        if self.performance.show_time - timezone.now() < timezone.timedelta(minutes=15):
            raise ValidationError("Reservations cannot be made less than 15 minutes before the performance.")


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        if self.row < 1 or self.seat < 1:
            raise ValidationError("The number of the row and place must be greater than 0.")
        if self.row > self.performance.theatre_hall.rows or self.seat > self.performance.theatre_hall.seats_in_row:
            raise ValidationError("Invalid row or seat number for this hall.")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["row", "seat", "performance"], name="unique_ticket"
            )
        ]
