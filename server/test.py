import threading
import requests
import time
import random
import sys
from datetime import datetime
from collections import defaultdict
import sqlite3
import os
from io import BytesIO
from werkzeug.datastructures import FileStorage
import json


# 新增：添加随机种子配置，确保多次运行条件一致
RANDOM_SEED = 42  # 固定种子值，可根据需要修改
random.seed(RANDOM_SEED)

# 配置信息 - 测试梯度核心参数
BASE_URL = "http://localhost:5001"
ADMIN_USER = {"username": "test_admin", "password": "admin123"}
TEST_EVENT_INFO = {
    "name": f"TestEvent_{int(time.time())}",
    "event_date": "2024-12-31",
    "start_time": "20:00",
    "price_1": 300,
    "price_2": 200,
    "price_3": 100
}

# 测试梯度配置 (名称, 并发用户数)
TEST_GRADIENTS = [
    ("轻度负载(1.5倍座位需求)", 75),  # 75*2=150 ≈ 100*1.5=150
    ("中度负载(5倍座位需求)", 250),  # 250*2=500 ≈ 100*5=500
    ("重度负载(20倍座位需求)", 1000)  # 1000*2=2000 = 100*20
]

# 全局锁，确保统计数据线程安全
stats_lock = threading.Lock()

# 性能指标记录 (按梯度存储)
gradient_performance = {}
test_resources = {
    "users": [],
    "event_id": None,
    "admin_session": None,
    "original_seat_count": 100  # 总座位数(固定100)
}

# 数据库配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "concert.db")


def progress_bar(current, total, prefix='', suffix='', length=50, fill='█'):
    """
    重构进度条函数：使用sys.stdout精准控制输出，确保动态刷新
    :param current: 当前进度
    :param total: 总进度
    :param prefix: 前缀文本
    :param suffix: 后缀文本
    :param length: 进度条长度
    :param fill: 填充字符
    """
    # 计算进度百分比和填充长度
    percent = 100.0 * current / total
    filled_length = int(length * current // total)
    # 构造进度条字符串
    bar = fill * filled_length + '-' * (length - filled_length)
    # 拼接完整输出字符串（\r 表示回到当前行开头，覆盖原有内容）
    output = f'\r{prefix} |{bar}| {percent:.1f}% {suffix}'
    # 写入输出流并强制刷新（核心修复）
    sys.stdout.write(output)
    sys.stdout.flush()
    # 进度完成后换行
    if current == total:
        sys.stdout.write('\n')
        sys.stdout.flush()


def connect_db():
    return sqlite3.connect(DB_PATH)


def set_admin_permission(username, is_admin=1):
    """设置用户管理员权限（修改提示文案）"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Users SET is_admin = ? WHERE username = ?",
            (is_admin, username)
        )
        conn.commit()
        print(f"已获得管理员权限")
        return True
    except Exception as e:
        print(f"设置管理员权限失败: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()


def reset_test_environment(event_id):
    """重置座位和订单状态，确保每个测试梯度独立"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        # 重置座位状态
        cursor.execute("UPDATE Seats SET is_reserved = 0 WHERE event_id = ?", (event_id,))
        # 重置座位类型库存（确保总座位数为100）
        cursor.execute("UPDATE SeatTypes SET stock = 30 WHERE event_id = ? AND type = 1", (event_id,))
        cursor.execute("UPDATE SeatTypes SET stock = 40 WHERE event_id = ? AND type = 2", (event_id,))
        cursor.execute("UPDATE SeatTypes SET stock = 30 WHERE event_id = ? AND type = 3", (event_id,))
        # 清除订单记录
        cursor.execute("DELETE FROM OrderDetails WHERE order_id IN (SELECT id FROM Orders WHERE event_id = ?)",
                       (event_id,))
        cursor.execute("DELETE FROM Orders WHERE event_id = ?", (event_id,))
        conn.commit()
        print("测试环境已重置，准备下一梯度测试")
    except Exception as e:
        print(f"重置环境失败: {str(e)}")
    finally:
        if conn:
            conn.close()


class TicketBookingTester(threading.Thread):
    def __init__(self, user_credentials, event_id, gradient_name, user_index):
        super().__init__()
        self.user = user_credentials
        self.event_id = event_id
        self.gradient_name = gradient_name
        self.session_id = None
        self.seat_ids = []
        self.user_index = user_index  # 新增：用户索引，用于生成独立但可复现的随机数
        # 为每个用户创建独立的随机数生成器，确保随机性的同时保持可复现性
        self.local_random = random.Random(RANDOM_SEED + user_index)
        # 标记当前用户各环节状态
        self.status = {
            "login_success": False,
            "get_seats_success": False,
            "ticket_request_sent": False,
            "ticket_response_success": False
        }
        # 记录当前用户实际请求的座位数
        self.actual_seats_requested = 0
        # 记录当前请求的响应时间（供成功请求统计）
        self.current_response_time = 0

    def register_with_retry(self, max_retry=3, silent=True):
        """
        注册用户（带重试，确保100%成功）
        :param max_retry: 最大重试次数
        :param silent: 是否静默模式（避免打印干扰进度条）
        """
        username = self.user["username"]
        password = self.user["password"]
        for retry in range(max_retry):
            try:
                response = requests.post(
                    f"{BASE_URL}/register",
                    json={"username": username, "password": password},
                    timeout=5
                )
                if response.status_code in [200, 409]:  # 200成功/409已存在（视为成功）
                    return True
                if not silent:
                    print(f"\n用户 {username} 注册重试{retry + 1}次失败，状态码: {response.status_code}")
            except Exception as e:
                if not silent:
                    print(f"\n用户 {username} 注册重试{retry + 1}次异常: {str(e)}")
            time.sleep(0.1)
        raise Exception(f"用户 {username} 注册{max_retry}次仍失败，测试终止")

    def login_with_retry(self, max_retry=3, silent=True):
        """
        登录用户（带重试，确保100%成功）
        :param max_retry: 最大重试次数
        :param silent: 是否静默模式（避免打印打印干扰进度条）
        """
        username = self.user["username"]
        password = self.user["password"]
        for retry in range(max_retry):
            try:
                response = requests.post(
                    f"{BASE_URL}/login",
                    json={"username": username, "password": password},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    self.session_id = data.get("session_id")
                    if self.session_id:
                        self.status["login_success"] = True
                        return True
                if not silent:
                    print(f"\n用户 {username} 登录重试{retry + 1}次失败，状态码: {response.status_code}")
            except Exception as e:
                if not silent:
                    print(f"\n用户 {username} 登录重试{retry + 1}次异常: {str(e)}")
            time.sleep(0.1)
        raise Exception(f"用户 {username} 登录{max_retry}次仍失败，测试终止")

    def get_available_seats(self):
        """获取可用座位（失败不影响购票请求发送）"""
        try:
            response = requests.get(
                f"{BASE_URL}/get_seats?event_id={self.event_id}",
                headers={"Session-ID": self.session_id},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                available_seats = [seat["id"] for seat in data["data"] if seat["is_reserved"] == 0]
                self.seat_ids = available_seats
                self.status["get_seats_success"] = True
                return True
            return False
        except Exception as e:
            return False

    def book_tickets(self):
        """发送购票请求（必发一次，失败归为对应环节）"""
        # 确保每个用户都计为一次请求（用户数=请求数）
        with stats_lock:
            grad_data = gradient_performance[self.gradient_name]
            grad_data["total_requests"] += 1

        # 1. 登录失败：直接标记为登录环节失败
        if not self.status["login_success"]:
            with stats_lock:
                grad_data = gradient_performance[self.gradient_name]
                grad_data["failed_requests"] += 1
                grad_data["failure_details"]["login_failed"] += 1
            return

        # 2. 获取座位（无论成败都继续发请求）
        self.get_available_seats()

        # 3. 构造座位请求（随机1-3张，真实记录数量）
        num_seats_prob = [1, 2, 2, 3]  # 均值2，概率分布：1(25%)、2(50%)、3(25%)
        # 使用用户专属随机数生成器，确保每次运行选择一致
        num_seats = self.local_random.choice(num_seats_prob)
        self.actual_seats_requested = num_seats  # 记录当前用户实际请求的座位数

        # 累加实际购票需求（线程安全）
        with stats_lock:
            grad_data = gradient_performance[self.gradient_name]
            grad_data["total_requested_seats"] += self.actual_seats_requested

        # 生成选中的座位ID（无可用座位时随机生成）
        if self.seat_ids:
            # 使用用户专属随机数生成器选择座位
            selected_seats = self.local_random.sample(self.seat_ids, min(num_seats, len(self.seat_ids)))
        else:
            # 无可用座位时，随机生成100以内的座位ID（触发后端端失败）
            selected_seats = [self.local_random.randint(1, 100) for _ in range(num_seats)]

        start_time = time.time()
        try:
            # 发送购票请求
            response = requests.post(
                f"{BASE_URL}/book_ticket",
                json={"event_id": self.event_id, "seat_ids": selected_seats},
                headers={"Session-ID": self.session_id},
                timeout=10
            )
            self.status["ticket_request_sent"] = True
            self.current_response_time = (time.time() - start_time) * 1000  # 记录响应时间
            response_time = self.current_response_time

            with stats_lock:
                grad_data = gradient_performance[self.gradient_name]
                # 所有请求的响应时间（含失败）
                grad_data["response_times"].append(response_time)

                # 4. 处理购票响应
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "success":
                        grad_data["successful_requests"] += 1
                        grad_data["total_booked_seats"] += len(selected_seats)
                        # 仅成功请求记录响应时间
                        grad_data["success_response_times"].append(response_time)
                        self.status["ticket_response_success"] = True
                    else:
                        # 后端返回失败（如座位已被占、无座位等）
                        grad_data["failed_requests"] += 1
                        grad_data["failure_details"]["ticket_response_failed"] += 1
                        grad_data["error_messages"][data.get("message", "Unknown error")] += 1
                else:
                    # HTTP状态码非200
                    grad_data["failed_requests"] += 1
                    grad_data["failure_details"]["ticket_response_failed"] += 1
                    grad_data["error_messages"][f"HTTP {response.status_code}"] += 1

        except Exception as e:
            # 请求请求发送失败（网络超时、连接拒绝等）
            self.current_response_time = (time.time() - start_time) * 1000
            response_time = self.current_response_time
            with stats_lock:
                grad_data = gradient_performance[self.gradient_name]
                # 所有请求的响应时间（含异常失败）
                grad_data["response_times"].append(response_time)
                grad_data["failed_requests"] += 1
                grad_data["failure_details"]["ticket_request_failed"] += 1
                grad_data["error_messages"][str(e)] += 1

    def run(self):
        """线程主逻辑：强制执行一次购票请求"""
        self.book_tickets()


def print_gradient_report(gradient_name, data, seat_count):
    """打印测试报告（含失败环节明细，优化响应时间统计）"""
    print(f"\n===== {gradient_name} 测试报告 =====")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"并发用户数: {data['concurrent_users']}")
    print(f"总请求数: {data['total_requests']} (用户数=请求数: {data['total_requests'] == data['concurrent_users']})")
    print(f"成功请求数: {data['successful_requests']}")
    print(f"失败请求数: {data['failed_requests']}")

    # 座位与购票统计（修复：区分理论均值和实际值）
    total_theory_demand = data['concurrent_users'] * 2  # 理论平均需求（每人2张）
    total_actual_demand = data['total_requested_seats']  # 实际购票需求（真实累加1/2/3张）
    actual_ratio = total_actual_demand / seat_count  # 实际需求倍数
    print(f"\n座位与购票统计:")
    print(f"  总座位数: {seat_count}")
    print(f"  理论平均购票需求: {total_theory_demand} (理论需求倍数{total_theory_demand / seat_count:.2f}倍)")
    print(f"  实际购票需求: {total_actual_demand} (实际需求倍数{actual_ratio:.2f}倍)")
    print(f"  实际购票总座位数: {data['total_booked_seats']}")
    print(f"  座位利用率: {data['total_booked_seats'] / seat_count * 100:.2f}%")
    print(f"  购票需求满足率: {data['total_booked_seats'] / total_actual_demand * 100:.2f}%"
          if total_actual_demand > 0 else "  购票需求满足率: 0.00%")

    # 失败环节明细
    print(f"\n请求失败环节明细:")
    failure_details = data["failure_details"]
    total_failed = data["failed_requests"]
    print(f"  总失败数: {total_failed}")
    print(
        f"  登录失败: {failure_details['login_failed']} ({failure_details['login_failed'] / total_failed * 100:.2f}%)" if total_failed > 0 else "  登录失败: 0 (0.00%)")
    print(
        f"  获取座位后请求失败: {failure_details['ticket_request_failed']} ({failure_details['ticket_request_failed'] / total_failed * 100:.2f}%)" if total_failed > 0 else "  获取座位后请求失败: 0 (0.00%)")
    print(
        f"  购票响应失败: {failure_details['ticket_response_failed']} ({failure_details['ticket_response_failed'] / total_failed * 100:.2f}%)" if total_failed > 0 else "  购票响应失败: 0 (0.00%)")

    # 响应时间统计（优化：拆分所有请求/仅成功请求）
    print(f"\n响应时间统计:")
    # 1. 所有请求的响应时间（反映服务器整体处理能力）
    if data['response_times']:
        all_avg = sum(data['response_times']) / len(data['response_times'])
        all_min = min(data['response_times'])
        all_max = max(data['response_times'])
        print(f"  【所有请求（成功+失败）】:")
        print(f"    平均响应时间: {all_avg:.2f} ms (计算逻辑：所有请求响应时间总和 ÷ 总请求数)")
        print(f"    最短响应时间: {all_min:.2f} ms")
        print(f"    最长响应时间: {all_max:.2f} ms")
    else:
        print(f"  【所有请求（成功+失败）】: 无数据")

    # 2. 仅成功请求的响应时间（反映核心业务性能）
    if data['success_response_times']:
        success_avg = sum(data['success_response_times']) / len(data['success_response_times'])
        success_min = min(data['success_response_times'])
        success_max = max(data['success_response_times'])
        print(f"  【仅成功请求】:")
        print(f"    平均响应时间: {success_avg:.2f} ms (计算逻辑：成功请求响应时间总和 ÷ 成功请求数)")
        print(f"    最短响应时间: {success_min:.2f} ms")
        print(f"    最长响应时间: {success_max:.2f} ms")
    else:
        print(f"  【仅成功请求】: 无数据")

    # 错误分布
    print("\n错误分布详情:")
    for error, count in data['error_messages'].items():
        print(f"  {error}: {count}次")

    # 性能统计
    total_time = (data['end_time'] - data['start_time']) * 1000
    print(f"\n测试性能统计:")
    print(f"  总测试时间: {total_time:.2f} ms")
    if total_time > 0:
        throughput = data['total_requests'] / (total_time / 1000)
        print(f"  吞吐量: {throughput:.2f} 请求/秒")


def get_event_seat_count(event_id):
    """获取活动座位数"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM Seats WHERE event_id = ?", (event_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        print(f"获取座位数失败: {str(e)}")
        return 0
    finally:
        if conn:
            conn.close()


def setup_test_environment():
    """初始化测试环境（确保管理员/测试用户100%注册成功）"""
    print("正在初始化测试环境...")

    # 1. 注册管理员用户（带重试）
    admin_tester = TicketBookingTester(ADMIN_USER, None, "", 0)  # 管理员用户索引固定为0
    admin_tester.register_with_retry(silent=False)
    test_resources["users"].append(ADMIN_USER["username"])

    # 2. 设置管理员权限
    if not set_admin_permission(ADMIN_USER["username"]):
        raise Exception("无法设置管理员权限，测试终止")

    # 3. 管理员登录（带重试）
    admin_login_success = False
    for retry in range(3):
        try:
            response = requests.post(
                f"{BASE_URL}/login",
                json=ADMIN_USER,
                timeout=5
            )
            if response.status_code == 200:
                test_resources["admin_session"] = response.json()["session_id"]
                admin_login_success = True
                break
        except Exception as e:
            print(f"管理员登录重试{retry + 1}次异常: {str(e)}")
        time.sleep(0.1)
    if not admin_login_success:
        raise Exception("管理员登录失败，测试终止")

    # 4. 创建测试活动
    files = {
        "poster": FileStorage(
            stream=BytesIO(b"test image"),
            filename="test_poster.jpg",
            content_type="image/jpeg"
        )
    }
    data = TEST_EVENT_INFO.copy()
    create_event_response = requests.post(
        f"{BASE_URL}/add_event",
        headers={"Session-ID": test_resources["admin_session"]},
        data=data,
        files=files,
        timeout=10
    )
    if create_event_response.status_code != 200:
        raise Exception(f"活动创建失败: {create_event_response.text}")

    # 获取活动ID
    events = requests.get(
        f"{BASE_URL}/search_events?keyword={TEST_EVENT_INFO['name']}",
        timeout=5
    ).json()
    if not events.get("data"):
        raise Exception("创建的活动未找到")
    event_id = events["data"][0]["id"]
    test_resources["event_id"] = event_id
    print(f"成功创建测试活动，ID: {event_id}")

    # 5. 调整座位数为100（修改提示文案）
    seat_count = get_event_seat_count(event_id)
    print(f"活动座位数固定为：100")
    if seat_count != 100:
        conn = connect_db()
        cursor = conn.cursor()
        # 删除多余座位
        cursor.execute(
            "DELETE FROM Seats WHERE event_id = ? AND id NOT IN (SELECT id FROM Seats WHERE event_id = ? LIMIT 100)",
            (event_id, event_id))
        # 补充不足座位
        cursor.execute("SELECT COUNT(*) as total FROM Seats WHERE event_id = ?", (event_id,))
        current_count = cursor.fetchone()[0]
        if current_count < 100:
            for i in range(current_count + 1, 101):
                cursor.execute("INSERT INTO Seats (event_id, row, col, type, is_reserved) VALUES (?, ?, ?, ?, 0)",
                               (event_id, (i // 10) + 1, (i % 10) + 1, (i % 3) + 1))
        conn.commit()
        conn.close()
        seat_count = 100
    test_resources["original_seat_count"] = seat_count

    # 6. 注册所有测试用户（带重试，进度条动态刷新）
    max_users = max([g[1] for g in TEST_GRADIENTS])
    test_users = []
    print(f"\n开始注册 {max_users} 个测试用户...")
    # 初始化进度条（0%）
    progress_bar(0, max_users, prefix='注册进度:', suffix='完成', length=50)
    for i in range(max_users):
        # 使用固定种子生成用户名，确保用户一致
        user_seed = RANDOM_SEED + i + 1  # 避免与管理员种子冲突
        username = f"test_user_{user_seed}_{i}"
        password = f"pass_{username}"
        user_info = {"username": username, "password": password}
        # 注册用户（静默模式，避免打印干扰进度条）
        user_tester = TicketBookingTester(user_info, None, "", i + 1)  # 用户索引从1开始
        user_tester.register_with_retry(silent=True)
        test_users.append(user_info)
        test_resources["users"].append(username)
        # 更新进度条（核心：每注册一个用户就更新一次）
        progress_bar(i + 1, max_users, prefix='注册进度:', suffix='完成', length=50)
        # 微小延迟，确保进度条渲染（关键修复）
        time.sleep(0.001)

    # 7. 批量登录所有测试用户（带重试，进度条动态刷新）
    print(f"\n开始登录 {max_users} 个测试用户...")
    # 初始化进度条（0%）
    progress_bar(0, max_users, prefix='登录进度:', suffix='完成', length=50)
    login_success_count = 0
    for idx, user in enumerate(test_users):
        user_tester = TicketBookingTester(user, event_id, "", idx + 1)  # 用户索引从1开始
        # 登录用户（静默模式，避免打印干扰进度条）
        if user_tester.login_with_retry(silent=True):
            login_success_count += 1
            test_users[idx]["session_id"] = user_tester.session_id
        # 更新进度条（核心：每登录一个用户就更新一次）
        progress_bar(idx + 1, max_users,
                     prefix='登录进度:',
                     suffix=f'成功{login_success_count}/{max_users}',
                     length=50)
        # 微小延迟，确保进度条渲染（关键修复）
        time.sleep(0.001)

    if login_success_count != max_users:
        raise Exception(f"登录失败数: {max_users - login_success_count}，测试终止")

    print(f"\n测试环境初始化完成：注册{max_users}个用户，登录成功率100%")
    return test_users, event_id


def cleanup_test_environment():
    """清理测试环境"""
    print("\n正在清理测试环境...")
    conn = None
    try:
        # 删除测试活动
        if test_resources["event_id"] and test_resources["admin_session"]:
            delete_response = requests.post(
                f"{BASE_URL}/delete_event",
                headers={"Session-ID": test_resources["admin_session"]},
                json={"event_id": test_resources["event_id"]},
                timeout=5
            )
            if delete_response.status_code == 200:
                print(f"已删除测试活动 ID: {test_resources['event_id']}")
            else:
                print(f"活动删除失败: {delete_response.text}")

        # 删除测试用户
        conn = connect_db()
        cursor = conn.cursor()
        for username in test_resources["users"]:
            cursor.execute("DELETE FROM Sessions WHERE username = ?", (username,))
            cursor.execute("DELETE FROM Users WHERE username = ?", (username,))
        conn.commit()
        print(f"已删除 {len(test_resources['users'])} 个测试用户")

    except Exception as e:
        print(f"清理过程出错: {str(e)}")
    finally:
        if conn:
            conn.close()


def run_gradient_test(gradient_name, concurrent_users, test_users, event_id):
    """运行单个梯度测试"""
    # 初始化性能数据（新增success_response_times存储成功请求响应时间）
    gradient_performance[gradient_name] = {
        "concurrent_users": concurrent_users,
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "response_times": [],  # 所有请求的响应时间（含失败）
        "success_response_times": [],  # 仅成功请求的响应时间
        "error_messages": defaultdict(int),
        "failure_details": {
            "login_failed": 0,  # 登录失败
            "ticket_request_failed": 0,  # 购票请求发送失败（网络等）
            "ticket_response_failed": 0  # 购票响应失败（后端返回失败）
        },
        "start_time": None,
        "end_time": None,
        "total_booked_seats": 0,
        "total_requested_seats": 0  # 初始化为0，真实累加每个用户的座位数
    }

    # 重置测试环境
    reset_test_environment(event_id)

    # 选取对应数量的用户
    selected_users = test_users[:concurrent_users]
    # 初始化测试线程（注入已登录的session_id）
    threads = []
    for idx, user in enumerate(selected_users):
        # 传递用户索引，确保随机数生成一致
        tester = TicketBookingTester(user, event_id, gradient_name, idx + 1)
        tester.session_id = user.get("session_id")  # 注入已登录的session
        tester.status["login_success"] = True  # 标记登录成功
        threads.append(tester)

    # 运行测试
    performance_data = gradient_performance[gradient_name]
    performance_data["start_time"] = time.time()

    # 启动所有线程（轻微延迟避免瞬间压垮服务器）
    for thread in threads:
        thread.start()
        time.sleep(0.001)

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    performance_data["end_time"] = time.time()

    # 打印报告
    print_gradient_report(
        gradient_name,
        performance_data,
        test_resources["original_seat_count"]
    )


def main():
    """主函数：执行全流程测试"""
    try:
        # 初始化环境（确保注册/登录100%成功）
        test_users, event_id = setup_test_environment()
        seat_count = test_resources["original_seat_count"]

        # 依次运行每个梯度测试
        for grad_name, concurrent_users in TEST_GRADIENTS:
            print(f"\n===== 开始 {grad_name} 测试 =====")
            run_gradient_test(grad_name, concurrent_users, test_users, event_id)

        # 汇总报告
        print("\n===== 测试梯度汇总 =====")
        print(f"总座位数: {seat_count}")

        # 打印对比表格标题（新增最长响应时间列）
        print(
            f"\n{'梯度名称':<25} | {'座位利用率':<12} | {'所有请求平均响应时间(ms)':<25} | {'所有请求最长响应时间(ms)':<28} | {'成功请求平均响应时间(ms)':<28} | {'成功请求最长响应时间(ms)':<28} | {'总测试时间(ms)':<18} | {'吞吐量(请求/秒)':<18}")
        print("-" * 200)

        # 准备结构化输出数据
        summary_data = {}

        for grad_name, _ in TEST_GRADIENTS:
            grad_data = gradient_performance[grad_name]

            # 计算各项指标
            seat_utilization = grad_data['total_booked_seats'] / seat_count * 100 if seat_count > 0 else 0

            # 所有请求相关指标
            all_requests_avg = sum(grad_data['response_times']) / len(grad_data['response_times']) if grad_data['response_times'] else 0
            all_requests_max = max(grad_data['response_times']) if grad_data['response_times'] else 0

            # 成功请求相关指标
            success_requests_avg = sum(grad_data['success_response_times']) / len(grad_data['success_response_times']) if grad_data['success_response_times'] else 0
            success_requests_max = max(grad_data['success_response_times']) if grad_data['success_response_times'] else 0

            # 总测试时间和吞吐量
            total_test_time = (grad_data['end_time'] - grad_data['start_time']) * 1000 if (grad_data['end_time'] and grad_data['start_time']) else 0
            throughput = grad_data['total_requests'] / (grad_data['end_time'] - grad_data['start_time']) if (grad_data['end_time'] and grad_data['start_time'] and (grad_data['end_time'] - grad_data['start_time']) > 0) else 0

            # 打印一行数据
            print(
                f"{grad_name:<25} | {seat_utilization:.2f}%<12 | {all_requests_avg:.2f}<25 | {all_requests_max:.2f}<28 | {success_requests_avg:.2f}<28 | {success_requests_max:.2f}<28 | {total_test_time:.2f}<18 | {throughput:.2f}<18")

            # 存储结构化数据
            summary_data[grad_name] = {
                "seat_utilization": seat_utilization,
                "all_requests_avg": all_requests_avg,
                "all_requests_max": all_requests_max,
                "success_requests_avg": success_requests_avg,
                "success_requests_max": success_requests_max,
                "total_test_time": total_test_time,
                "throughput": throughput,
                "concurrent_users": grad_data["concurrent_users"],
                "total_requests": grad_data["total_requests"],
                "successful_requests": grad_data["successful_requests"],
                "failed_requests": grad_data["failed_requests"]
            }

        # 输出结构化数据（供run_tests.py提取）
        print("\n===== PERFORMANCE_DATA_START =====")
        print(json.dumps(summary_data))
        print("===== PERFORMANCE_DATA_END =====")

    except Exception as e:
        print(f"\n测试过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_test_environment()


if __name__ == "__main__":
    main()