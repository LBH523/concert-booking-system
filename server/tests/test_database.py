import pytest
import os
import tempfile
import shutil
from database.db import connect_db, execute_query, fetch_query, get_user_id, reserve_seats

class TestDatabaseConnection:
    """测试数据库连接功能"""
    
    def test_connect_db(self, test_db):
        """测试数据库连接"""
        conn = connect_db()
        assert conn is not None
        conn.close()
    
    def test_execute_query(self, test_db):
        """测试执行查询"""
        # 插入测试数据
        user_id = execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            ('dbtest', 'testpass', 0)
        )
        assert user_id is not None
        assert user_id > 0
        
        # 验证数据被插入
        users = fetch_query("SELECT * FROM Users WHERE username = ?", ('dbtest',))
        assert len(users) == 1
        assert users[0]['username'] == 'dbtest'
    
    def test_fetch_query(self, test_db):
        """测试获取查询结果"""
        # 插入测试数据
        execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            ('fetchtest', 'testpass', 1)
        )
        
        # 获取数据
        users = fetch_query("SELECT * FROM Users WHERE username = ?", ('fetchtest',))
        assert len(users) == 1
        
        user = users[0]
        assert user['username'] == 'fetchtest'
        assert user['password'] == 'testpass'
        assert user['is_admin'] == 1
    
    def test_fetch_query_empty_result(self, test_db):
        """测试空查询结果"""
        users = fetch_query("SELECT * FROM Users WHERE username = ?", ('nonexistent',))
        assert len(users) == 0

class TestDatabaseUtilityFunctions:
    """测试数据库工具函数"""
    
    def test_get_user_id(self, test_db):
        """测试获取用户ID"""
        # 插入用户
        execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            ('utiltest', 'testpass', 0)
        )
        
        # 获取用户ID
        user_id = get_user_id('utiltest')
        assert user_id is not None
        assert user_id > 0
    
    def test_get_user_id_nonexistent(self, test_db):
        """测试获取不存在用户的ID"""
        with pytest.raises(IndexError):
            get_user_id('nonexistent_user')

class TestReserveSeats:
    """测试座位预订功能"""
    
    def test_reserve_seats_success(self, test_db):
        """测试成功预订座位"""
        # 创建测试活动
        event_id = execute_query(
            "INSERT INTO Events (name, poster_url, event_date, start_time) VALUES (?, ?, ?, ?)",
            ('Reserve Test Concert', '/test.jpg', '2025-12-31', '20:00')
        )
        
        # 创建座位类型
        execute_query(
            "INSERT INTO SeatTypes (event_id, type, price, stock) VALUES (?, ?, ?, ?)",
            (event_id, 1, 1000, 10)
        )
        
        # 创建座位
        seat_ids = []
        for i in range(5):
            seat_id = execute_query(
                "INSERT INTO Seats (event_id, row, col, type, is_reserved) VALUES (?, ?, ?, ?, 0)",
                (event_id, 1, i+1, 1)
            )
            seat_ids.append(seat_id)
        
        # 创建测试用户
        user_id = execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            ('reservetest', 'testpass', 0)
        )
        
        # 预订座位
        result = reserve_seats(event_id, seat_ids[:3], 'reservetest', user_id)
        
        assert result['status'] == 'success'
        assert 'order_id' in result
        assert 'total_price' in result
        assert result['total_price'] == 3000  # 3 * 1000
    
    def test_reserve_seats_already_reserved(self, test_db):
        """测试预订已预订座位"""
        # 创建测试活动
        event_id = execute_query(
            "INSERT INTO Events (name, poster_url, event_date, start_time) VALUES (?, ?, ?, ?)",
            ('Reserve Test Concert 2', '/test.jpg', '2025-12-31', '20:00')
        )
        
        # 创建座位类型
        execute_query(
            "INSERT INTO SeatTypes (event_id, type, price, stock) VALUES (?, ?, ?, ?)",
            (event_id, 1, 1000, 10)
        )
        
        # 创建座位
        seat_id = execute_query(
            "INSERT INTO Seats (event_id, row, col, type, is_reserved) VALUES (?, ?, ?, ?, 1)",
            (event_id, 1, 1, 1)
        )
        
        # 创建测试用户
        user_id = execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            ('reservetest2', 'testpass', 0)
        )
        
        # 尝试预订已预订座位
        result = reserve_seats(event_id, [seat_id], 'reservetest2', user_id)
        
        assert result['status'] == 'fail'
        assert 'already taken' in result['message']
    
    def test_reserve_seats_invalid_seats(self, test_db):
        """测试预订无效座位"""
        # 创建测试活动
        event_id = execute_query(
            "INSERT INTO Events (name, poster_url, event_date, start_time) VALUES (?, ?, ?, ?)",
            ('Reserve Test Concert 3', '/test.jpg', '2025-12-31', '20:00')
        )
        
        # 创建测试用户
        user_id = execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            ('reservetest3', 'testpass', 0)
        )
        
        # 尝试预订不存在的座位
        result = reserve_seats(event_id, [99999, 99998], 'reservetest3', user_id)
        
        assert result['status'] == 'fail'
        assert 'not found' in result['message']
    
    def test_reserve_seats_stock_update(self, test_db):
        """测试预订后库存更新"""
        # 创建测试活动
        event_id = execute_query(
            "INSERT INTO Events (name, poster_url, event_date, start_time) VALUES (?, ?, ?, ?)",
            ('Stock Test Concert', '/test.jpg', '2025-12-31', '20:00')
        )
        
        # 创建座位类型
        seat_type_id = execute_query(
            "INSERT INTO SeatTypes (event_id, type, price, stock) VALUES (?, ?, ?, ?)",
            (event_id, 1, 1000, 10)
        )
        
        # 创建座位
        seat_ids = []
        for i in range(3):
            seat_id = execute_query(
                "INSERT INTO Seats (event_id, row, col, type, is_reserved) VALUES (?, ?, ?, ?, 0)",
                (event_id, 1, i+1, 1)
            )
            seat_ids.append(seat_id)
        
        # 创建测试用户
        user_id = execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            ('stocktest', 'testpass', 0)
        )
        
        # 获取初始库存
        seat_types_before = fetch_query(
            "SELECT stock FROM SeatTypes WHERE id = ?", 
            (seat_type_id,)
        )
        initial_stock = seat_types_before[0]['stock']
        
        # 预订座位
        result = reserve_seats(event_id, seat_ids, 'stocktest', user_id)
        
        assert result['status'] == 'success'
        
        # 验证库存减少
        seat_types_after = fetch_query(
            "SELECT stock FROM SeatTypes WHERE id = ?", 
            (seat_type_id,)
        )
        final_stock = seat_types_after[0]['stock']
        
        assert final_stock == initial_stock - 3

class TestDatabaseConstraints:
    """测试数据库约束"""
    
    def test_unique_username_constraint(self, test_db):
        """测试用户名唯一约束"""
        # 插入第一个用户
        execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            ('constrainttest', 'testpass', 0)
        )
        
        # 尝试插入相同用户名应该失败
        with pytest.raises(Exception):  # 具体异常类型取决于SQLite实现
            execute_query(
                "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
                ('constrainttest', 'testpass2', 0)
            )
    
    def test_foreign_key_constraint_events(self, test_db):
        """测试外键约束 - 活动"""
        # 尝试为不存在的活动创建座位应该失败
        with pytest.raises(Exception):
            execute_query(
                "INSERT INTO Seats (event_id, row, col, type, is_reserved) VALUES (?, ?, ?, ?, 0)",
                (99999, 1, 1, 1)
            )
    
    def test_foreign_key_constraint_users(self, test_db):
        """测试外键约束 - 用户"""
        # 创建活动
        event_id = execute_query(
            "INSERT INTO Events (name, poster_url, event_date, start_time) VALUES (?, ?, ?, ?)",
            ('FK Test Concert', '/test.jpg', '2025-12-31', '20:00')
        )
        
        # 尝试为不存在的用户创建订单应该失败
        with pytest.raises(Exception):
            execute_query(
                "INSERT INTO Orders (user_id, event_id, total_price, status) VALUES (?, ?, ?, ?)",
                (99999, event_id, 1000, 1)
            )

class TestDatabaseTriggers:
    """测试数据库触发器"""
    
    def test_cancel_order_trigger(self, test_db):
        """测试取消订单触发器"""
        # 创建测试活动
        event_id = execute_query(
            "INSERT INTO Events (name, poster_url, event_date, start_time) VALUES (?, ?, ?, ?)",
            ('Trigger Test Concert', '/test.jpg', '2025-12-31', '20:00')
        )
        
        # 创建座位类型
        execute_query(
            "INSERT INTO SeatTypes (event_id, type, price, stock) VALUES (?, ?, ?, ?)",
            (event_id, 1, 1000, 5)
        )
        
        # 创建座位
        seat_id = execute_query(
            "INSERT INTO Seats (event_id, row, col, type, is_reserved) VALUES (?, ?, ?, ?, 0)",
            (event_id, 1, 1, 1)
        )
        
        # 创建用户
        user_id = execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            ('triggertest', 'testpass', 0)
        )
        
        # 创建订单
        order_id = execute_query(
            "INSERT INTO Orders (user_id, event_id, total_price, status) VALUES (?, ?, ?, ?)",
            (user_id, event_id, 1000, 1)
        )
        
        # 创建订单详情
        execute_query(
            "INSERT INTO OrderDetails (order_id, seat_id, seat_type, price) VALUES (?, ?, ?, ?)",
            (order_id, seat_id, 1, 1000)
        )
        
        # 标记座位为已预订
        execute_query("UPDATE Seats SET is_reserved = 1 WHERE id = ?", (seat_id,))
        
        # 减少库存
        execute_query("UPDATE SeatTypes SET stock = stock - 1 WHERE event_id = ? AND type = ?", (event_id, 1))
        
        # 取消订单（应该触发触发器）
        execute_query("UPDATE Orders SET status = 0 WHERE id = ?", (order_id,))
        
        # 验证座位被释放
        seats = fetch_query("SELECT is_reserved FROM Seats WHERE id = ?", (seat_id,))
        assert seats[0]['is_reserved'] == 0
        
        # 验证库存恢复
        seat_types = fetch_query("SELECT stock FROM SeatTypes WHERE event_id = ? AND type = ?", (event_id, 1))
        assert seat_types[0]['stock'] == 5  # 恢复到原始值