from flask import Blueprint, request, jsonify
from database.db import fetch_query, reserve_seats, get_user_id
import re
# 新增：导入缓存模块
import seat_cache  # <-- 新增

ticket_booking_bp = Blueprint("ticket_booking", __name__)

#FR-TK-001
@ticket_booking_bp.route("/search_events", methods=["GET"])
def search_events():
    keyword = request.args.get("keyword")
    keyword = keyword.strip()
    #print('keyword', keyword)
    pattern_date = r"^\d{4}-\d{2}-\d{2}$"
    # Search events by date
    if re.match(pattern_date, keyword):
        print(keyword)
        results = fetch_query("SELECT * FROM Events WHERE event_date = ?", (keyword,))
    # Search events by name, ignoring case sensitivity
    else:
        results = fetch_query(
            "SELECT * FROM Events WHERE LOWER(name) LIKE LOWER(?)",
            (f"%{keyword}%",)
        )
    if results:
        dict_results = [dict(row) for row in results]
        #print('dict_results', dict_results)
        return jsonify({'status': 'success', 'data': dict_results})
    else:
        return jsonify({'status': 'fail', 'message': 'No results'}), 404

#FR-TK-002
@ticket_booking_bp.route("/get_seats", methods=["GET"])
def get_seats():
    event_id = request.args.get("event_id")

    # 新增：先查询缓存
    cached_seats = seat_cache.get_seats_from_cache(event_id)  # <-- 新增
    if cached_seats:  # <-- 新增
        return jsonify({'status': 'success', 'data': cached_seats})  # <-- 新增

    results = fetch_query("SELECT * FROM Seats WHERE event_id = ?", (event_id,))
    if results:
        dict_results = [dict(row) for row in results]

        # 新增：将查询结果写入缓存
        seat_cache.set_seats_to_cache(event_id, dict_results)  # <-- 新增

        return jsonify({'status': 'success', 'data': dict_results})
    else:
        return jsonify({'status': 'fail', 'message': 'Event not found or has been deleted'}), 404






@ticket_booking_bp.route('/book_ticket', methods=['POST'])
def book_ticket():
    # Step 1: validate session
    session_id = request.headers.get('Session-ID')
    session_info = fetch_query("SELECT username, is_admin FROM Sessions WHERE session_id = ?", (session_id,))
    if not session_info:
        return jsonify({'status': 'fail', 'message': 'Invalid or expired session'}), 401
    username = session_info[0]['username']

    # Step 2: parse request body
    data = request.get_json()
    event_id = data.get("event_id")
    seat_ids = data.get("seat_ids", [])
    user_id = get_user_id(username)

    if not event_id or not seat_ids:
        return jsonify({"status": "fail", "message": "event_id and seat_ids required"}), 400
    if len(seat_ids) > 4:
        return jsonify({"status": "fail", "message": "Cannot purchase more than 4 seats"}), 400

    # Step 3: call db.py function
    result = reserve_seats(event_id, seat_ids, username, user_id)

    # Step 4: return response
    if result["status"] == "success":
        return jsonify(result), 200
    elif result["status"] == "fail":
        return jsonify(result), 400
    else:  # "error"
        return jsonify(result), 500