from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from theatre.models import Actor, Play, Performance, Genre, TheatreHall, Reservation, Ticket
from datetime import timedelta


User = get_user_model()

PLAY_URL = reverse("theatre:play-list")
PERFORMANCE_URL = reverse("theatre:performance-list")
RESERVATION_URL = reverse("theatre:reservation-list")
TICKET_URL = reverse("theatre:ticket-list")


def sample_actor(**params):
    defaults = {"first_name": "George", "last_name": "Clooney"}
    defaults.update(params)

    return Actor.objects.create(**defaults)

def sample_play(**params):
    defaults = {
        "title": "Sample Play",
        "description": "Sample description",
        "duration": 120,
    }
    defaults.update(params)

    return Play.objects.create(**defaults)

def sample_genre(name="Drama"):
    return Genre.objects.create(name=name)

def sample_performance(show_time):
    return Performance.objects.create(
        title="Test Performance",
        show_time=show_time,
        theatre_hall="Main Hall"
    )

def sample_ticket(performance, seat="A1"):
    return Ticket.objects.create(
        performance=performance,
        seat=seat
    )


class PlayAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@theater.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.play_one = Play.objects.create(title="Play One", description="Description One", duration=120)
        self.play_two = Play.objects.create(title="Play Two", description="Description Two", duration=90)


    def test_create_play(self):
        """Test creating a new play"""
        payload = {
            "title": "New Play",
            "description": "A thrilling new play.",
            "duration": 150,
        }
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(title=payload["title"])
        self.assertEqual(play.description, payload["description"])

    def test_create_play_without_title(self):
        """Test creating a play without a title"""
        payload = {
            "description": "A play without a title.",
            "duration": 90,
        }
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', res.data)

    def test_create_play_without_duration(self):
        """Test creating a play without a duration"""
        payload = {
            "title": "Play Without Duration",
            "description": "This play lacks duration.",
        }
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duration', res.data)


class ActorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@theater.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.actor_url = reverse("theatre:actor-list")

    def test_create_actor(self):
        payload = {
            "first_name": "Brad",
            "last_name": "Pitt",
        }
        res = self.client.post(self.actor_url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        actor = Actor.objects.get(first_name=payload["first_name"])
        self.assertEqual(actor.last_name, payload["last_name"])

    def test_create_actor_without_last_name(self):
        payload = {
            "first_name": "Leonardo",
        }
        res = self.client.post(self.actor_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("last_name", res.data)

    def test_create_actor_invalid_data(self):
        payload = {
            "first_name": "",
            "last_name": "DiCaprio",
        }
        res = self.client.post(self.actor_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("first_name", res.data)

class PerformanceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@theater.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.performance_url = PERFORMANCE_URL
        self.play = sample_play()

    def test_create_performance(self):
        hall = TheatreHall.objects.create(name="Main Hall", rows=2, seats_in_row=2)
        future_time = timezone.now() + timedelta(days=1)

        payload = {
            "show_time": future_time.strftime("%Y-%m-%d %H:%M"),
            "play": self.play.id,
            "theatre_hall": hall.id,
        }

        res = self.client.post(PERFORMANCE_URL, payload)

        print(f"Response data: {res.data}")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        performance = Performance.objects.get(play=self.play)
        self.assertEqual(performance.theatre_hall, hall)

    def test_create_performance_without_play(self):
        payload = {
            "show_time": "2024-06-02 14:00:00",
            "hall": "Main Hall",
        }
        res = self.client.post(self.performance_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("play", res.data)

    def test_create_performance_invalid_time(self):
        payload = {
            "show_time": "incorrect_time",
            "play": self.play.id,
            "hall": "Main Hall",
        }
        res = self.client.post(self.performance_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("show_time", res.data)

    def test_create_performance_with_invalid_theatre_hall(self):
        """Test creating a performance with an invalid theatre hall"""
        payload = {
            "show_time": "2024-06-02 14:00:00",
            "play": self.play.id,
            "theatre_hall": 9999,
        }
        res = self.client.post(self.performance_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("theatre_hall", res.data)

class TheatreHallAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@theater.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.hall_url = reverse("theatre:theatrehall-list")

    def test_create_theatre_hall(self):
        """Test creating a new theatre hall"""
        payload = {
            "name": "Main Hall",
            "rows": 5,
            "seats_in_row": 10,
        }
        res = self.client.post(self.hall_url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        hall = TheatreHall.objects.get(name=payload["name"])
        self.assertEqual(hall.rows, payload["rows"])
        self.assertEqual(hall.seats_in_row, payload["seats_in_row"])

    def test_create_theatre_hall_without_name(self):
        """Test creating a theatre hall without a name"""
        payload = {
            "rows": 5,
            "seats_in_row": 10,
        }
        res = self.client.post(self.hall_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", res.data)

    def test_create_theatre_hall_with_duplicate_name(self):
        """Test creating a theatre hall with a duplicate name"""
        TheatreHall.objects.create(name="Main Hall", rows=5, seats_in_row=10)
        payload = {
            "name": "Main Hall",
            "rows": 3,
            "seats_in_row": 5,
        }
        res = self.client.post(self.hall_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', res.data)

    def test_theatre_hall_capacity(self):
        """Test the capacity property of the theatre hall"""
        hall = TheatreHall.objects.create(name="Test Hall", rows=5, seats_in_row=10)
        self.assertEqual(hall.capacity, 50)


class ReservationAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            "admin@theater.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.theatre_hall = TheatreHall.objects.create(
            name="Main Hall",
            rows=5,
            seats_in_row=10
        )
        self.play = Play.objects.create(
            title="Test Play",
            description="A play for testing purposes",
            duration=120
        )
        self.performance = Performance.objects.create(
            play=self.play,
            theatre_hall=self.theatre_hall,
            show_time=timezone.now() + timezone.timedelta(hours=1),
            image=None
        )
        self.ticket1 = Ticket.objects.create(row=1, seat=1, performance=self.performance)
        self.ticket2 = Ticket.objects.create(row=1, seat=2, performance=self.performance)

        self.url = RESERVATION_URL

    def test_create_reservation(self):
        """Test creating a reservation successfully."""
        data = {
            "tickets": [self.ticket1.id, self.ticket2.id]
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(Reservation.objects.first().user, self.user)

    def test_list_reservations(self):
        """Test listing reservations for the authenticated user."""
        reservation = Reservation.objects.create(user=self.user)
        reservation.tickets.set([self.ticket1, self.ticket2])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], reservation.id)

    def test_cancel_reservation(self):
        """Test deleting a reservation successfully."""
        reservation = Reservation.objects.create(user=self.user)
        reservation.tickets.set([self.ticket1, self.ticket2])

        delete_url = f'{self.url}{reservation.id}/'
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_create_reservation_unauthenticated(self):
        """Test that unauthenticated user cannot create a reservation."""
        self.client.force_authenticate(user=None)
        data = {
            "tickets": [self.ticket1.id, self.ticket2.id]
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_reservations_unauthenticated(self):
        """Test that unauthenticated user cannot list reservations."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TicketAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            "admin@theater.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.theatre_hall = TheatreHall.objects.create(name="Test Hall", seats_in_row=10, rows=5)
        self.play_instance = Play.objects.create(
            title="Test Play",duration=120
        )

        self.performance = Performance.objects.create(
            show_time=timezone.now() + timezone.timedelta(hours=1),
            theatre_hall=self.theatre_hall,
            play=self.play_instance
        )
        self.url = TICKET_URL


    def test_ticket_creation_success(self):
        """Test creating a ticket with valid data."""

        data = {
            "row": 1,
            "seat": 1,
            "performance": self.performance.id
        }
        response = self.client.post(self.url, data, format="json")


        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_ticket_creation_reserved_seat(self):
        """Test creating a ticket for a seat that is already reserved."""
        Ticket.objects.create(row=1, seat=1, performance=self.performance)
        data = {
            "row": 1,
            "seat": 1,
            "performance": self.performance.id
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_ticket_creation_details(self):
        """Test creating a ticket and checking its details."""
        data = {
            "row": 1,
            "seat": 1,
            "performance": self.performance.id
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ticket.objects.count(), 1)

        ticket = Ticket.objects.first()

        self.assertEqual(ticket.row, data['row'])
        self.assertEqual(ticket.seat, data['seat'])
        self.assertEqual(ticket.performance.id, data['performance'])
