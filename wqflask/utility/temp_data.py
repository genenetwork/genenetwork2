from __future__ import print_function, division, absolute_import
from redis import Redis

import simplejson as json

class TempData(object):
    
    def __init__(self, temp_uuid, part=None):
        self.temp_uuid = temp_uuid
        self.redis = Redis()
        self.key = "tempdata:{}".format(self.temp_uuid)
        if part:
            self.key += ":{}".format(part)
        
    def store(self, field, value):
        self.redis.hset(self.key, field, value)
        self.redis.expire(self.key, 60*60)  # Expire in 60 minutes
        
    def get_all(self):
        return self.redis.hgetall(self.key)


if __name__ == "__main__":
    redis = Redis()
    for key in redis.keys():
        for field in redis.hkeys(key):
            print("{}.{}={}".format(key, field, redis.hget(key, field)))
