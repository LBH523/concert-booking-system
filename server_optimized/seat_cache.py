"""
-*- coding: utf-8 -*-
@File  : seat_cache.py
@author: Tequila
@Time  : 2025/12/06 14:39
"""
import redis
import json
import subprocess
import os
import time
from datetime import timedelta

# Redis服务器可执行文件路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件(seat_cache.py)所在目录(server_optimized)
PARENT_DIR = os.path.dirname(CURRENT_DIR)  # 获取server_optimized的父目录
REDIS_SERVER_PATH = os.path.join(PARENT_DIR, "redis", "redis-server.exe")  # 拼接Redis可执行文件路径

# 缓存键前缀
SEAT_CACHE_PREFIX = "event:seats:"
# 缓存过期时间(秒) - 防止极端情况下缓存不一致
CACHE_EXPIRE_SECONDS = 300


def check_redis_connection(client):
    """检查Redis连接状态"""
    try:
        client.ping()
        return True
    except (redis.ConnectionError, redis.TimeoutError):
        return False


def start_redis_server():
    """启动Redis服务器"""
    if not os.path.exists(REDIS_SERVER_PATH):
        raise FileNotFoundError(f"Redis服务器文件不存在: {REDIS_SERVER_PATH}")

    try:
        # 启动Redis服务器，不显示控制台窗口
        subprocess.Popen(
            REDIS_SERVER_PATH,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # 等待服务器启动
        time.sleep(2)
        return True
    except Exception as e:
        print(f"启动Redis服务器失败: {str(e)}")
        return False


def init_redis_client():
    """初始化Redis客户端并确保服务可用"""
    client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True, socket_connect_timeout=5)

    # 检查连接状态
    if check_redis_connection(client):
        print("Redis已在运行，连接成功")
        return client

    # 尝试启动Redis服务器
    print("Redis未运行，尝试启动...")
    if start_redis_server():
        # 重新创建连接并检查
        if check_redis_connection(client):
            print("Redis启动成功，连接已建立")
            return client
        else:
            raise ConnectionError("Redis启动后仍无法连接")
    else:
        raise ConnectionError("无法启动Redis服务器")


def get_seats_from_cache(event_id):
    """从缓存获取座位状态"""
    cache_key = f"{SEAT_CACHE_PREFIX}{event_id}"
    cached_data = redis_client.get(cache_key)
    return json.loads(cached_data) if cached_data else None


def set_seats_to_cache(event_id, seats_data):
    """将座位状态写入缓存"""
    cache_key = f"{SEAT_CACHE_PREFIX}{event_id}"
    redis_client.setex(
        cache_key,
        timedelta(seconds=CACHE_EXPIRE_SECONDS),
        json.dumps(seats_data)
    )


def update_seat_cache(event_id, seat_id, is_reserved):
    """更新缓存中单个座位的状态"""
    cache_key = f"{SEAT_CACHE_PREFIX}{event_id}"
    # 使用Redis的事务保证原子性
    pipe = redis_client.pipeline()
    pipe.watch(cache_key)
    try:
        cached_data = pipe.get(cache_key)
        if cached_data:
            seats = json.loads(cached_data)
            # 找到并更新目标座位
            for seat in seats:
                if seat["id"] == seat_id:
                    seat["is_reserved"] = is_reserved
                    break
            pipe.setex(cache_key, timedelta(seconds=CACHE_EXPIRE_SECONDS), json.dumps(seats))
        pipe.execute()
    except Exception:
        pipe.reset()
    finally:
        pipe.reset()


def batch_update_seat_cache(event_id, seat_updates):
    """批量更新缓存中的座位状态（seat_updates为[(seat_id, is_reserved), ...]）"""
    cache_key = f"{SEAT_CACHE_PREFIX}{event_id}"
    pipe = redis_client.pipeline()
    pipe.watch(cache_key)
    try:
        cached_data = pipe.get(cache_key)
        if cached_data:
            seats = json.loads(cached_data)
            # 批量更新座位状态
            for seat_id, is_reserved in seat_updates:
                for seat in seats:
                    if seat["id"] == seat_id:
                        seat["is_reserved"] = is_reserved
                        break
            pipe.setex(cache_key, timedelta(seconds=CACHE_EXPIRE_SECONDS), json.dumps(seats))
        pipe.execute()
    except Exception:
        pipe.reset()
    finally:
        pipe.reset()


def clear_event_cache(event_id):
    """清除指定场次的缓存"""
    cache_key = f"{SEAT_CACHE_PREFIX}{event_id}"
    redis_client.delete(cache_key)


# 初始化Redis客户端
redis_client = init_redis_client()
