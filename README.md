
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

test/
├── run_tests.py            # Runs tests, outputs the performance comparison
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

## Is the project runnable right now?

Yes. Both the backend (Flask) and frontend (Vue 3 + Vite) are already included in this repo, along with the sample SQLite database (`server/database/concert.db`). You only need Python 3.10+ and Node.js 18+ available locally. No extra files are required.

## How to Run

1. Start the backend (Flask) in one terminal window:
   ```sh
   cd server
   # one-command bootstrap: creates .venv, installs deps, runs Flask on 0.0.0.0:5001
   bash start_backend.sh
   ```
   You can override host/port if needed (e.g., `HOST=127.0.0.1 PORT=5001 bash start_backend.sh`).

2. Run the client-side Vue app in a different terminal window:
   ```sh
   cd client
   npm install
   npm run dev
   ```
   Navigate to [http://localhost:5173](http://localhost:5173). If your backend is not on `http://localhost:5001`, create `client/.env` and set `VITE_API_BASE_URL` to the backend URL.

## Frontend Quick Guide (Vue 3 + Vite)

- Requirements: Node.js 18+, npm. Backend defaults to http://localhost:5001.
- Dev commands:
  - cd client
  - npm install
  - npm run dev (defaults to http://localhost:5173)
  - To point to another backend: create client/.env with VITE_API_BASE_URL=http://host:port
- Key routes:
  - /auth (login/register; saves session_id + is_admin to localStorage)
  - /tickets (event list, search by name/date, price/remaining overview)
  - /tickets/:id (seat selection, max 4 seats, shows total, handles concurrent failures)
  - /orders (filter by status; cancel order)
  - /admin/events, /admin/events/add, /admin/events/:id/edit (admin only)
- Navigation: Shows, My Orders, Admin Events (visible if is_admin=1), Login/Register or Logout.
- Session handling: axios interceptor auto-attaches Session-ID header from localStorage session_id. “Logout” clears session_id and is_admin locally (soft logout).
- Data seeds: sample SQLite DB under server/database/concert.db; ensure you add events (admin) before booking if none exist.
