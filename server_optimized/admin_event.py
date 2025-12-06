import os
from flask import Blueprint, request, jsonify, session
from database.db import execute_query, fetch_query
import sqlite3
from werkzeug.utils import secure_filename
admin_event_bp = Blueprint('admin_event', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "posters")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 确保目录存在

    #handle and store poster image
def handle_poster_upload(req):
    """Process the uploaded poster image and return its public URL."""
    if "poster" not in req.files:
        return None, {"status": "error", "message": "No file uploaded"}, 400

    file = req.files["poster"]
    if file.filename == "":
        return None, {"status": "error", "message": "Empty filename"}, 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    # Public path for serving the image
    poster_url = f"/posters/{filename}"
    return poster_url, None, None

#FR-EM-001
@admin_event_bp.route('/add_event', methods=['POST'])
def add_event():
    #check is_admin
    session_id = request.headers.get('Session-ID')
    print('session_id', session_id)
    session_info = fetch_query("SELECT username, is_admin FROM Sessions WHERE session_id = ?", (session_id,))
    if not session_info:
        return jsonify({'status': 'fail', 'message': 'Invalid or expired session'}), 401
    #username = session_info[0]['username']
    is_admin = session_info[0]['is_admin']
    if is_admin==0:
        return jsonify({'status': 'fail', 'message': 'Permission denied: not an admin'}), 403

    #generate poster_url
    poster_url, err_json, err_code = handle_poster_upload(request)
    if err_json:
        return jsonify(err_json), err_code

    # Parse other fields from FormData
    data = request.form.to_dict()
    name = data.get('name')
    event_date = data.get('event_date') # Expected format: YYYY-MM-DD
    start_time = data.get('start_time') # Expected format: HH:MM
    #1-vip 2-standard 3-economy
    #set initial stock stationary: 1-40 2-50 3-60
    price_1 = data.get('price_1')
    price_2 = data.get('price_2')
    price_3 = data.get('price_3')
    stock_1 = 40
    stock_2 = 50
    stock_3 = 60

    #Insert Events
    try:
        event_id = execute_query(
            "INSERT INTO Events (name, poster_url, event_date, start_time) VALUES (?, ?, ?, ?)",
            (name, poster_url, event_date, start_time)
        )
        print('event_id', event_id)
    except sqlite3.IntegrityError:
        return jsonify({'status': 'fail', 'message': 'Event name already exists'}), 409
    except Exception as e:
        print(f"Unexpected error during event insertion: {e}")
        return jsonify({'status': 'error', 'message': 'Server error during event creation'}), 500

    try:
        seat_data = [
            (event_id, 1, price_1, stock_1),  # VIP
            (event_id, 2, price_2, stock_2),  # Standard
            (event_id, 3, price_3, stock_3),  # Economy
        ]

        row_offset = 0  # keep track of current row number across all seat types

        #Insert SeatTypes
        for seat_type in seat_data:
            execute_query(
                "INSERT INTO SeatTypes (event_id, type, price, stock) VALUES (?, ?, ?, ?)",
                seat_type
            )
            _, seat_type_id, price, stock = seat_type

            # Insert info of all seats
            for i in range(stock):
                row = (i // 10) + 1 + row_offset  # continue rows across types
                col = (i % 10) + 1
                execute_query(
                    "INSERT INTO Seats (event_id, row, col, type, is_reserved) VALUES (?, ?, ?, ?, 0)",
                    (event_id, row, col, seat_type_id)
                )

            # update row_offset after finishing this seat type
            row_offset += (stock // 10) + (1 if stock % 10 != 0 else 0)

    except Exception as e:
        print(f"Unexpected error during seat insertion: {e}")
        return jsonify({'status': 'error', 'message': 'Server error during seat setup'}), 500
    return jsonify({'status': 'success', 'message': 'Add event success'})

#FR-EM-002
@admin_event_bp.route('/edit_event', methods=['POST'])
def edit_event():
    # check is_admin
    session_id = request.headers.get('Session-ID')
    session_info = fetch_query("SELECT username, is_admin FROM Sessions WHERE session_id = ?", (session_id,))
    if not session_info:
        return jsonify({'status': 'fail', 'message': 'Invalid or expired session'}), 401
    is_admin = session_info[0]['is_admin']
    if is_admin == 0:
        return jsonify({'status': 'fail', 'message': 'Permission denied: not an admin'}), 403

    data = request.get_json()
    #print('data', data)
    event_id = data.get('event_id')
    price_1 = data.get('price_1')
    price_2 = data.get('price_2')
    price_3 = data.get('price_3')
    event_date = data.get('event_date')
    start_time = data.get('start_time')

    try:
        # Update event info
        execute_query(
            "UPDATE Events SET event_date = ?, start_time = ? WHERE id = ?",
            (event_date, start_time, event_id)
        )

        # Update seat types and seats
        seat_updates = [
            (price_1, event_id, 1),
            (price_2, event_id, 2),
            (price_3, event_id, 3)
        ]
        for price, eid, seat_type in seat_updates:
            # Update SeatTypes price
            execute_query(
                "UPDATE SeatTypes SET price = ? WHERE event_id = ? AND type = ?",
                (price, eid, seat_type)
            )

        return jsonify({'status': 'success', 'message': 'Event updated successfully'})
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({'status': 'error', 'message': 'Database error'}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'status': 'error', 'message': 'Server is wrong'}), 500

# FR-EM-002
@admin_event_bp.route('/delete_event', methods=['POST'])
def delete_event():
    # check is_admin
    session_id = request.headers.get('Session-ID')
    session_info = fetch_query("SELECT username, is_admin FROM Sessions WHERE session_id = ?", (session_id,))
    if not session_info:
        return jsonify({'status': 'fail', 'message': 'Invalid or expired session'}), 401
    is_admin = session_info[0]['is_admin']
    if is_admin == 0:
        return jsonify({'status': 'fail', 'message': 'Permission denied: not an admin'}), 403
    data = request.get_json()
    event_id = data.get('event_id')

    try:
        execute_query("DELETE FROM Events WHERE id=?", (event_id,))

        return jsonify({"status": "success", "message": f"Event {event_id} deleted"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500