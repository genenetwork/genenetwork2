from __future__ import print_function, division, absolute_import
from redis import Redis
import redis

import simplejson as json

class TempData(object):

    def __init__(self, temp_uuid, preface="tempdata", part=None):
        self.temp_uuid = temp_uuid
        self.redis = Redis()
        self.key = "{}:{}".format(preface, self.temp_uuid)
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
        print("key is:", key)
        if "plink" not in key:
            print("  Skipping...\n")
            continue
        for field in redis.hkeys(key):
            print("  {}.{}={}\n".format(key, field, len(redis.hget(key, field))))
