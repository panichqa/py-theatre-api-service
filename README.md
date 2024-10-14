# Theatre API Service

This project implements an API for a theatre, allowing users to book seats for performances online without needing to visit the theatre in person.

### Features

* Users can view available performances and their details, including showtimes and dates.
* Seat reservation: Users can select available seats and reserve them for a specific show.
* Booking status: After booking, users can view their reservation status and the seats they’ve reserved.
* Admin panel: Administrators can add, modify, and delete performances and manage seat availability.

### Setup Instructions

##### Installation

1. Clone the repository:

`git clone https://github.com/your-username/repository-name.git`

2. Navigate to the project directory:

`cd repository-name`
3. Install dependencies:

`pip install -r requirements.txt`
4. Running with Docker
Run the project using Docker:

`docker-compose up`

`Access the API at http://localhost:8000/.`

#### Features

* The API supports various HTTP methods for viewing performances, booking seats, and checking booking status.
* User permissions are checked for accessing the admin panel.
* API documentation is available via an integrated Swagger UI.