import datetime
import uuid
import simplejson as json
from wqflask import user_manager
from utility.logger import getLogger

from .util_functions import (get_collections_by_user_key, save_collection,
                             process_traits)

logger = getLogger(__name__)

class AnonCollection(object):
    """User is not logged in"""
    def __init__(self, collection_name):
        anon_user = user_manager.AnonUser()
        self.key = anon_user.key
        self.name = collection_name
        self.id = None
        self.traits = []
        self.created_timestamp = get_timestamp_string()
        self.changed_timestamp = self.created_timestamp

        collections_list = get_collections_by_user_key(self.key)
        logger.debug("Collections list", collections_list)
        collection = [coll for coll in collections_list if coll["name"] == self.name]
        if len(collection) == 1:
            self.id = collection[0]['id']
            self.traits = collection[0]['members']
            self.is_new = False

        if self.id == None:
            self.id = str(uuid.uuid4())
            self.is_new = True

    def get_members(self):
        return self.traits

    @property
    def num_members(self):
        return len(self.traits)

    def add_traits(self, params):
        self.traits.extend(list(process_traits(params['traits'])))
        self.traits = list(set(self.traits))

    def remove_traits(self, params):
        traits_to_remove = [(":").join(trait.split(":")[:2]) for trait in params.getlist('traits[]')]
        logger.debug("Traits to remove", traits_to_remove)
        tmp = [trait for trait in self.traits if trait not in traits_to_remove]
        self.traits = tmp

    def get_data(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_timestamp": self.created_timestamp,
            "changed_timestamp": self.changed_timestamp,
            "num_members": len(self.traits),
            "members": self.traits,
            "user_key": self.key}
