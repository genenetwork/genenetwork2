from redis import Redis

import simplejson as json

class TempData:

    def __init__(self, temp_uuid):
        self.temp_uuid = temp_uuid
        self.redis = Redis()
        self.key = "tempdata:{}".format(self.temp_uuid)

    def store(self, field, value):
        self.redis.hset(self.key, field, value)
        self.redis.expire(self.key, 60 * 15)  # Expire in 15 minutes

    def get_all(self):
        return self.redis.hgetall(self.key)


if __name__ == "__main__":
    redis = Redis()
    for key in list(redis.keys()):
        for field in redis.hkeys(key):
            print("{}.{}={}".format(key, field, redis.hget(key, field)))
