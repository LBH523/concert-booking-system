"""
-*- coding: utf-8 -*-
@File  : seat_cache.py
@author: Tequila
@Time  : 2025/12/06 14:39
"""
import redis
import json
from datetime import timedelta

# 初始化Redis连接
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# 缓存键前缀
SEAT_CACHE_PREFIX = "event:seats:"
# 缓存过期时间(秒) - 防止极端情况下缓存不一致
CACHE_EXPIRE_SECONDS = 300

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

def clear_event_cache(event_id):
    """清除指定场次的缓存"""
    cache_key = f"{SEAT_CACHE_PREFIX}{event_id}"
    redis_client.delete(cache_key)