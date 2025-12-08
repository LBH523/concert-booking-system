
# High-Concurrency Concert Ticket Booking System with Flask & Vue

This project is a **full-stack web application** for managing concert events, user accounts, and ticket booking.  
It consists of a **Flask backend** providing REST APIs, a **Vue.js frontend** delivering a modern user interface, and is designed with **high concurrency support** to handle many simultaneous users.

## Project Structure

```text
server/
├── app.py                  # Main Flask application entry point
├── user.py                 # User registration and login routes
├── admin_event.py          # Admin routes for adding, editing, deleting events
├── admin_order.py          # Admin and user routes for viewing/canceling orders
├── ticket_booking.py       # Routes for searching events, viewing seats, booking tickets
├── database/
│   ├── db.py               # Database helper functions (public queries, transactions)
│   └── concert.db          # SQLite database file
├── requirements.txt
└── README.md
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

## How to Run

1. Run the server-side Flask app in one terminal window:
   ```sh
   $ cd server
   $ python3 -m venv env
   $ source env/bin/activate
   (env)$ pip install -r requirements.txt
   (env)$ PYTHONPATH=. flask --app app run --port=5001 --debug
   ```
   Navigate to [http://localhost:5001](http://localhost:5001)

2. Run the client-side Vue app in a different terminal window:
   ```sh
   $ cd client
   $ npm install
   $ npm run dev
   ```
   Navigate to [http://localhost:5173](http://localhost:5173)
```
