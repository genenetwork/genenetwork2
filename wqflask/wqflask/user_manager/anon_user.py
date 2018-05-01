import datetime
import simplejson as json
import redis # used for collections
from flask import Flask, request
from utility.logger import getLogger
from utility import after
from utility.tools import LOG_SQL_ALCHEMY

from .util_functions import create_signed_cookie, verify_cookie

Redis = redis.StrictRedis()
logger = getLogger(__name__)

class AnonUser(object):
    """Anonymous user handling"""
    cookie_name = 'anon_user_v8'

    def __init__(self):
        self.cookie = request.cookies.get(self.cookie_name)
        if self.cookie:
            logger.debug("already is cookie")
            self.anon_id = verify_cookie(self.cookie)

        else:
            logger.debug("creating new cookie")
            self.anon_id, self.cookie = create_signed_cookie()
        self.key = "anon_collection:v1:{}".format(self.anon_id)

        @after.after_this_request
        def set_cookie(response):
            response.set_cookie(self.cookie_name, self.cookie)

    def add_collection(self, new_collection):
        collection_dict = dict(name = new_collection.name,
                               created_timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
                               changed_timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
                               num_members = new_collection.num_members,
                               members = new_collection.get_members())

        Redis.set(self.key, json.dumps(collection_dict))
        Redis.expire(self.key, 60 * 60 * 24 * 5)

    def delete_collection(self, collection_name):
        from wqflask.collect import delete_collection_by_id
        existing_collections = self.get_collections()
        to_delete = [coll for coll in existing_collections if coll["name"] == collection_name]
        for collection in to_delete:
            delete_collection_by_id(collection_id = collection["id"])

    def get_collections(self):
        from wqflask.collect import get_collections_by_user_key
        return get_collections_by_user_key(self.key)

    def import_traits_to_user(self):
        result = Redis.get(self.key)
        collections_list = json.loads(result if result else "[]")
        for collection in collections_list:
            uc = model.UserCollection()
            uc.name = collection['name']
            collection_exists = g.user_session.user_ob.get_collection_by_name(uc.name)
            if collection_exists:
                continue
            else:
                uc.user = g.user_session.user_id
                uc.members = json.dumps(collection['members'])
                db_session.add(uc)
                db_session.commit()

    def display_num_collections(self):
        """
        Returns the number of collections or a blank string if there are zero.

        Because this is so unimportant...we wrap the whole thing in a try/expect...last thing we
        want is a webpage not to be displayed because of an error here

        Importand TODO: use redis to cache this, don't want to be constantly computing it
        """
        try:
            num = len(self.get_collections())
            if num > 0:
                return num
            else:
                return ""
        except Exception as why:
            print("Couldn't display_num_collections:", why)
            return ""
