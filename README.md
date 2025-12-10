
# High-Concurrency Concert Ticket Booking System with Flask & Vue

This project is a **full-stack web application** for managing concert events, user accounts, and ticket booking.  
It consists of a **Flask backend** providing REST APIs, a **Vue.js frontend** delivering a modern user interface, and is designed with **high concurrency support** to handle many simultaneous users.

## Project Structure

```text
client/
├── index.html               # Vite entry HTML
├── package.json             # Frontend dependencies and scripts
├── vite.config.js           # Vite configuration
├── src/
│   ├── App.vue              # Root Vue component with global navbar/layout
│   ├── main.js              # Vue app bootstrap
│   ├── api/
│   │   ├── auth.js          # Auth endpoints: login/register
│   │   ├── client.js        # Axios instance with Session-ID interceptor
│   │   ├── tickets.js       # Event search, seat detail, purchase
│   │   ├── orders.js        # Order list and cancel APIs
│   │   └── adminEvents.js   # Admin event add/edit/delete APIs
│   ├── components/
│   │   ├── Books.vue        # Sample CRUD component (demo)
│   │   ├── Ping.vue         # Sample component (demo)
│   │   ├── HelloWorld.vue   # Vite starter component (demo)
│   │   └── tickets/SeatGrid.vue  # Seat grid UI with selection logic
│   ├── views/
│   │   ├── Auth.vue         # Login/Register page
│   │   ├── Orders.vue       # Order list, filter, cancel
│   │   ├── Tickets/
│   │   │   ├── EventBrowse.vue   # Event list/search, price/remaining preview
│   │   │   └── SeatSelection.vue # Seat selection and booking
│   │   └── admin/
│   │       ├── AdminEventList.vue # Admin event list with edit/delete
│   │       ├── AddEvent.vue       # Admin add event (FormData upload)
│   │       └── EditEvent.vue      # Admin edit event (date/time/prices)
│   ├── router/
│   │   └── index.js         # Vue Router setup and guards
│   └── assets/
│       └── logo.svg         # Default asset
├── public/
│   └── favicon.ico (if present)  # Static assets
└── package-lock.json        # Pinned dependency tree
server/
├── app.py                  # Main Flask application entry point
├── user.py                 # User registration and login routes
├── admin_event.py          # Admin routes for adding, editing, deleting events
├── admin_order.py          # Admin and user routes for viewing/canceling orders
├── ticket_booking.py       # Routes for searching events, viewing seats, booking tickets
├── test.py                 # Concert booking performance test under varied loads
├── database/
│   ├── db.py               # Database helper functions (public queries, transactions)
│   └── concert.db          # SQLite database file
├── requirements.txt
└── README.md
server_optimized/
├── app.py                  # Main Flask application entry point
├── user.py                 # User registration and login routes
├── admin_event.py          # Admin routes for adding, editing, deleting events
├── admin_order.py          # Admin and user routes for viewing/canceling orders
├── ticket_booking.py       # Routes for searching events, viewing seats, booking tickets
├── seat_cache.py           # Cache management for seat status info based on Redis
├── test.py                 # Optimized concert booking performance test under varied loads
├── database/
│   ├── db.py               # Database helper functions (public queries, transactions)
│   └── concert.db          # SQLite database file
├── requirements.txt
└── README.md
test/
├── run_tests.py            # Runs tests, outputs the performance comparison
server/tests/
├── conftest.py             # pytest configuration and fixtures
├── test_user.py            # User management module tests
├── test_admin_event.py     # Event management module tests
├── test_ticket_booking.py  # Ticket booking module tests
├── test_admin_order.py     # Order management module tests
├── test_database.py        # Database module tests
└── README.md              # Test documentation
```

## Dependencies

The project uses the following Python packages:

- **Flask==3.1.2**  
  Web framework for building the REST API.
- **Flask-Cors==6.0.1**  
  Enables Cross-Origin Resource Sharing (CORS) so the frontend can communicate with the backend.
- **sqlite3** (built-in with Python)  
  Lightweight relational database used for storing users, events, seats, and orders.

Other modules used:  
`uuid` (standard library) for generating session IDs.  
`os`, `re`, `werkzeug.utils` (standard libraries) for file handling and regex validation.

## Testing Framework

The project includes comprehensive test suites using:

- **pytest==7.4.0**: Testing framework
- **coverage==7.2.7**: Code coverage analysis
- **pytest-flask**: Flask application testing utilities

## How to Run

### 1. Server-side Flask App
```sh
$ cd server
$ python3 -m venv env
$ source env/bin/activate
(env)$ pip install -r requirements.txt
(env)$ PYTHONPATH=. flask --app app run --port=5001 --debug
```
Navigate to [http://localhost:5001](http://localhost:5001)

### 2. Client-side Vue App
```sh
$ cd client
$ npm install
$ npm run dev
```
Navigate to [http://localhost:5173](http://localhost:5173)

### 3. Running Tests
```sh
# Navigate to server directory and activate virtual environment
$ cd server
$ source env/bin/activate

# Run all tests
(env)$ pytest tests/ -v

# Run specific test module
(env)$ pytest tests/test_user.py -v

# Run tests with coverage report
(env)$ coverage run -m pytest tests/
(env)$ coverage report
(env)$ coverage html  # Generate HTML report
```

### 4. Performance Testing
```sh
$ cd test
$ python run_tests.py
```


