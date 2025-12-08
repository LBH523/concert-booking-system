from flask import Blueprint, request, jsonify
from database.db import fetch_query, reserve_seats, get_user_id
import re
import threading  # 新增：用于请求合并的锁机制
# 新增：导入缓存模块
import seat_cache  # <-- 新增

ticket_booking_bp = Blueprint("ticket_booking", __name__)

# 新增：请求合并控制 - 记录正在加载的event_id及其锁
loading_locks = {}  # 格式: {event_id: threading.Lock()}


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

        # 新增：缓存预热 - 搜索到活动后提前加载座位缓存
        for event in dict_results:  # 新增
            event_id = event["id"]  # 新增
            # 检查缓存是否已存在，不存在则加载
            if not seat_cache.get_seats_from_cache(event_id):  # 新增
                # 从数据库查询座位数据
                seats = fetch_query("SELECT * FROM Seats WHERE event_id = ?", (event_id,))  # 新增
                if seats:  # 新增
                    dict_seats = [dict(row) for row in seats]  # 新增
                    seat_cache.set_seats_to_cache(event_id, dict_seats)  # 新增
        # 新增：缓存预热结束

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

    # 新增：请求合并逻辑
    # 获取或创建当前event_id的加载锁
    lock = loading_locks.get(event_id)  # 新增
    if not lock:  # 新增
        lock = threading.Lock()  # 新增
        loading_locks[event_id] = lock  # 新增

    with lock:  # 新增：确保同一event_id的并发请求仅查询一次数据库
        # 双重检查缓存，防止锁等待期间缓存已被其他请求填充
        cached_seats = seat_cache.get_seats_from_cache(event_id)  # 新增
        if cached_seats:  # 新增
            return jsonify({'status': 'success', 'data': cached_seats})  # 新增

        # 原逻辑：查询数据库
        results = fetch_query("SELECT * FROM Seats WHERE event_id = ?", (event_id,))
        if results:
            dict_results = [dict(row) for row in results]

            # 新增：将查询结果写入缓存
            seat_cache.set_seats_to_cache(event_id, dict_results)  # <-- 新增

            return jsonify({'status': 'success', 'data': dict_results})
        else:
            return jsonify({'status': 'fail', 'message': 'Event not found or has been deleted'}), 404
    # 新增：请求合并逻辑结束


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
