import pathlib
import uuid
from typing import Type

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.db.models import UniqueConstraint
from django.utils import timezone
from django.utils.text import slugify
from django.utils.timezone import make_aware
from datetime import datetime

class TheatreHall(models.Model):
    name = models.CharField(max_length=255, unique=True)
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
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    duration = models.IntegerField()
    actors = models.ManyToManyField(Actor, related_name="plays", blank=True)
    genres = models.ManyToManyField(Genre, related_name="plays", blank=True)


    def __str__(self):
        return self.title

def movie_image_path(instance, filename) -> pathlib.Path:
    filename = f"{slugify(instance.title)}-{uuid.uuid4()}{pathlib.Path(filename).suffix}"
    return pathlib.Path("uploads/performances/") / filename


class Performance(models.Model):
    play = models.ForeignKey(Play, on_delete=models.CASCADE)
    theatre_hall = models.ForeignKey(TheatreHall, on_delete=models.CASCADE)
    show_time = models.DateTimeField()
    image = models.ImageField(null=True, upload_to=movie_image_path)

    def save(self, *args, **kwargs):
        if self.show_time and self.show_time < timezone.now():
            raise ValidationError("The display time cannot be in the past.")
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["play", "theatre_hall", "show_time"], name="unique_performance"
            )
        ]


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE, related_name="tickets")
    reservation = models.ForeignKey(Reservation, null=True, blank=True, on_delete=models.CASCADE, related_name="tickets")

    def clean(self):
        if self.performance.show_time - timezone.now() < timezone.timedelta(minutes=15):
            raise ValidationError("Reservations cannot be made less than 15 minutes before the performance.")
        Ticket.validate_seat(self.seat, self.row, self.performance, ValidationError)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @staticmethod
    def validate_seat(seat: int, row: int, performance: Performance, error_to_raise: Type[BaseException]) -> None:
        for ticket_attr_value, ticket_attr_name, theatre_hall_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(performance.theatre_hall, theatre_hall_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} number must be in available range: (1, {count_attrs})"
                    }
                )

    def __str__(self):
        return f"{str(self.performance)} (row: {self.row}, seat: {self.seat})"

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["performance", "row", "seat"],
                name="unique_ticket"
            )
        ]
