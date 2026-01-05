import redis 
import json
import sqlite3

redis_client = redis.Redis(
    host = "redis",
    port = 6379,
    decode_responses = True
)

# def get_db():
#     conn = sqlite3.conncect(DB_PATH,check_same_thread)