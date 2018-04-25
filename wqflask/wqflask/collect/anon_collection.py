import datetime
import uuid
import redis
import simplejson as json
from wqflask import user_manager
from utility.logger import getLogger

from .util_functions import process_traits

Redis = redis.StrictRedis()
logger = getLogger(__name__)

class AnonCollection(object):
    """User is not logged in"""
    def __init__(self, collection_name):
        anon_user = user_manager.AnonUser()
        self.key = anon_user.key
        self.name = collection_name
        self.id = None
        self.created_timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        self.changed_timestamp = self.created_timestamp #ZS: will be updated when changes are made

        #ZS: Find id and set it if the collection doesn't already exist
        if Redis.get(self.key) == "None" or Redis.get(self.key) == None:
            Redis.set(self.key, None) #ZS: For some reason I get the error "Operation against a key holding the wrong kind of value" if I don't do this
        else:
            collections_list = json.loads(Redis.get(self.key))
            collection_position = 0 #ZS: Position of collection in collection_list, if it exists
            collection_exists = False
            for i, collection in enumerate(collections_list):
                if collection['name'] == self.name:
                    collection_position = i
                    collection_exists = True
                    self.id = collection['id']
                    break

        if self.id == None:
            self.id = str(uuid.uuid4())

    def get_members(self):
        traits = []
        collections_list = json.loads(Redis.get(self.key))
        for collection in collections_list:
            if collection['id'] == self.id:
                traits = collection['members']
        return traits

    @property
    def num_members(self):
        num_members = 0
        collections_list = json.loads(Redis.get(self.key))
        for collection in collections_list:
            if collection['id'] == self.id:
                num_members = collection['num_members']
        return num_members

    def add_traits(self, params):
        #assert collection_name == "Default", "Unexpected collection name for anonymous user"
        self.traits = list(process_traits(params['traits']))
        #len_before = len(Redis.smembers(self.key))
        existing_collections = Redis.get(self.key)
        logger.debug("existing_collections:", existing_collections)
        if existing_collections != None and existing_collections != "None":
            collections_list = json.loads(existing_collections)
            collection_position = 0 #ZS: Position of collection in collection_list, if it exists
            collection_exists = False
            for i, collection in enumerate(collections_list):
                if collection['id'] == self.id:
                    collection_position = i
                    collection_exists = True
                    break
            if collection_exists:
                collections_list[collection_position]['members'].extend(self.traits)
                collections_list[collection_position]['num_members'] = len(collections_list[collection_position]['members'])
                collections_list[collection_position]['changed_timestamp'] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
            else:
                collection_dict = {"id" : self.id,
                                   "name" : self.name,
                                   "created_timestamp" : self.created_timestamp,
                                   "changed_timestamp" : self.changed_timestamp,
                                   "num_members" : len(self.traits),
                                   "members" : self.traits}
                collections_list.append(collection_dict)
        else:
            collections_list = []
            collection_dict = {"id" : self.id,
                               "name" : self.name,
                               "created_timestamp" : self.created_timestamp,
                               "changed_timestamp" : self.changed_timestamp,
                               "num_members" : len(self.traits),
                               "members" : self.traits}
            collections_list.append(collection_dict)

        Redis.set(self.key, json.dumps(collections_list))
        #Redis.sadd(self.key, *list(traits))
        #Redis.expire(self.key, 60 * 60 * 24 * 5)
        #len_now = len(Redis.smembers(self.key))
        #report_change(len_before, len_now)

    def remove_traits(self, params):
        traits_to_remove = [(":").join(trait.split(":")[:2]) for trait in params.getlist('traits[]')]
        existing_collections = Redis.get(self.key)
        collection_position = 0
        collections_list = json.loads(existing_collections)
        for i, collection in enumerate(collections_list):
            if collection['id'] == self.id:
                collection_position = i
                collection_exists = True
                break
        collections_list[collection_position]['members'] = [trait for trait in collections_list[collection_position]['members'] if trait not in traits_to_remove]
        collections_list[collection_position]['num_members'] = len(collections_list[collection_position]['members'])
        collections_list[collection_position]['changed_timestamp'] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        len_now = collections_list[collection_position]['num_members']
        #print("before in redis:", json.loads(Redis.get(self.key)))
        Redis.set(self.key, json.dumps(collections_list))
        #print("currently in redis:", json.loads(Redis.get(self.key)))

        # We need to return something so we'll return this...maybe in the future
        # we can use it to check the results
        return str(len_now)
