import datetime
import time
import uuid

import simplejson as json

from flask import (Flask, g, render_template, url_for, request, make_response,
                   redirect, flash, abort)

from wqflask import app
from utility import hmac

#from utility.elasticsearch_tools import get_elasticsearch_connection
from utility.redis_tools import get_redis_conn, get_user_id, get_user_by_unique_column, set_user_attribute, get_user_collections, save_collections
Redis = get_redis_conn()

from utility.logger import getLogger
logger = getLogger(__name__)

THREE_DAYS = 60 * 60 * 24 * 3
THIRTY_DAYS = 60 * 60 * 24 * 30

@app.before_request
def get_user_session():
    logger.info("@app.before_request get_session")
    g.user_session = UserSession()
    #ZS: I think this should solve the issue of deleting the cookie and redirecting to the home page when a user's session has expired
    if not g.user_session:
        response = make_response(redirect(url_for('login')))
        response.set_cookie('session_id_v2', '', expires=0)
        return response

@app.after_request
def set_user_session(response):
    if hasattr(g, 'user_session'):
        if not request.cookies.get(g.user_session.cookie_name):
            response.set_cookie(g.user_session.cookie_name, g.user_session.cookie)
    return response

def verify_cookie(cookie):
    the_uuid, separator, the_signature = cookie.partition(':')
    assert len(the_uuid) == 36, "Is session_id a uuid?"
    assert separator == ":", "Expected a : here"
    assert the_signature == hmac.hmac_creation(the_uuid), "Uh-oh, someone tampering with the cookie?"
    return the_uuid

def create_signed_cookie():
    the_uuid = str(uuid.uuid4())
    signature = hmac.hmac_creation(the_uuid)
    uuid_signed = the_uuid + ":" + signature
    logger.debug("uuid_signed:", uuid_signed)
    return the_uuid, uuid_signed

@app.route("/user/manage", methods=('GET','POST'))
def manage_user():
    params = request.form if request.form else request.args
    if 'new_full_name' in params:
        set_user_attribute(g.user_session.user_id, 'full_name', params['new_full_name'])
    if 'new_organization' in params:
        set_user_attribute(g.user_session.user_id, 'organization', params['new_organization'])

    user_details = get_user_by_unique_column("user_id", g.user_session.user_id)

    return render_template("admin/manage_user.html", user_details = user_details)

class UserSession(object):
    """Logged in user handling"""

    user_cookie_name = 'session_id_v2'
    anon_cookie_name = 'anon_user_v1'

    def __init__(self):
        user_cookie = request.cookies.get(self.user_cookie_name)
        if not user_cookie:
            self.logged_in = False
            anon_cookie = request.cookies.get(self.anon_cookie_name)
            self.cookie_name = self.anon_cookie_name
            if anon_cookie:
                self.cookie = anon_cookie
                session_id = verify_cookie(self.cookie)
            else:
                session_id, self.cookie = create_signed_cookie()
        else:
            self.cookie_name = self.user_cookie_name
            self.cookie = user_cookie
            session_id = verify_cookie(self.cookie)

        self.redis_key = self.cookie_name + ":" + session_id
        self.session_id = session_id
        self.record = Redis.hgetall(self.redis_key)

        #ZS: If user correctled logged in but their session expired
        #ZS: Need to test this by setting the time-out to be really short or something
        if not self.record or self.record == []:
            if user_cookie:
                self.logged_in = False
                self.record = dict(login_time = time.time(),
                                    user_type = "anon",
                                    user_id = str(uuid.uuid4()))
                Redis.hmset(self.redis_key, self.record)
                Redis.expire(self.redis_key, THIRTY_DAYS)

                ########### Grrr...this won't work because of the way flask handles cookies
                # Delete the cookie
                flash("Due to inactivity your session has expired. If you'd like please login again.")
                return None
            else:
                self.record = dict(login_time = time.time(),
                                    user_type = "anon",
                                    user_id = str(uuid.uuid4()))
                Redis.hmset(self.redis_key, self.record)
                Redis.expire(self.redis_key, THIRTY_DAYS)
        else:
            if user_cookie:
                self.logged_in = True

        if user_cookie:
            session_time = THREE_DAYS
        else:
            session_time = THIRTY_DAYS

        if Redis.ttl(self.redis_key) < session_time:
            # (Almost) everytime the user does something we extend the session_id in Redis...
            Redis.expire(self.redis_key, session_time)

    @property
    def user_id(self):
        """Shortcut to the user_id"""
        if b'user_id' not in self.record:
            self.record[b'user_id'] = str(uuid.uuid4())

        return self.record[b'user_id']

    @property
    def redis_user_id(self):
        """User id from Redis (need to check if this is the same as the id stored in self.records)"""

        #ZS: This part is a bit weird. Some accounts used to not have saved user ids, and in the process of testing I think I created some duplicate accounts for myself.
        #ZS: Accounts should automatically generate user_ids if they don't already have one now, so this might not be necessary for anything other than my account's collections

        if 'user_email_address' in self.record:
            user_email = self.record['user_email_address']

            #ZS: Get user's collections if they exist
            user_id = None
            user_id = get_user_id("email_address", user_email)
        elif 'user_id' in self.record:
            user_id = self.record['user_id']
        elif 'github_id' in self.record:
            user_github_id = self.record['github_id']
            user_id = None
            user_id = get_user_id("github_id", user_github_id)
        else: #ZS: Anonymous user
            return None

        return user_id

    @property
    def user_name(self):
        """Shortcut to the user_name"""
        if 'user_name' in self.record:
            return self.record['user_name']
        else:
            return ''

    @property
    def user_collections(self):
        """List of user's collections"""

        #ZS: Get user's collections if they exist
        collections = get_user_collections(self.user_id)
        collections = [item for item in collections if item['name'] != "Your Default Collection"] + [item for item in collections if item['name'] == "Your Default Collection"] #ZS: Ensure Default Collection is last in list
        return collections

    @property
    def num_collections(self):
        """Number of user's collections"""

        return len([item for item in self.user_collections if item['num_members'] > 0])

    def add_collection(self, collection_name, traits):
        """Add collection into Redis"""

        collection_dict = {'id': str(uuid.uuid4()),
                           'name': collection_name,
                           'created_timestamp': datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
                           'changed_timestamp': datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
                           'num_members': len(traits),
                           'members': list(traits) }

        current_collections = self.user_collections
        current_collections.append(collection_dict)
        self.update_collections(current_collections)

        return collection_dict['id']

    def change_collection_name(self, collection_id, new_name):
        updated_collections = []
        for collection in self.user_collections:
            updated_collection = collection
            if collection['id'] == collection_id:
                updated_collection['name'] = new_name
            updated_collections.append(collection)

        self.update_collections(updated_collections)
        return new_name

    def delete_collection(self, collection_id):
        """Remove collection with given ID"""

        updated_collections = []
        for collection in self.user_collections:
            if collection['id'] == collection_id:
                continue
            else:
                updated_collections.append(collection)

        self.update_collections(updated_collections)

        return collection['name']

    def add_traits_to_collection(self, collection_id, traits_to_add):
        """Add specified traits to a collection"""

        this_collection = self.get_collection_by_id(collection_id)

        updated_collection = this_collection
        current_members_minus_new = [member for member in this_collection['members'] if member not in traits_to_add]
        updated_traits = traits_to_add + current_members_minus_new

        updated_collection['members'] = updated_traits
        updated_collection['num_members'] = len(updated_traits)
        updated_collection['changed_timestamp'] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')

        updated_collections = []
        for collection in self.user_collections:
            if collection['id'] == collection_id:
                updated_collections.append(updated_collection)
            else:
                updated_collections.append(collection)

        self.update_collections(updated_collections)

    def remove_traits_from_collection(self, collection_id, traits_to_remove):
        """Remove specified traits from a collection"""

        this_collection = self.get_collection_by_id(collection_id)

        updated_collection = this_collection
        updated_traits = []
        for trait in this_collection['members']:
            if trait in traits_to_remove:
                continue
            else:
                updated_traits.append(trait)

        updated_collection['members'] = updated_traits
        updated_collection['num_members'] = len(updated_traits)
        updated_collection['changed_timestamp'] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')

        updated_collections = []
        for collection in self.user_collections:
            if collection['id'] == collection_id:
                updated_collections.append(updated_collection)
            else:
                updated_collections.append(collection)

        self.update_collections(updated_collections)

        return updated_traits

    def get_collection_by_id(self, collection_id):
        for collection in self.user_collections:
            if collection['id'] == collection_id:
                return collection

    def get_collection_by_name(self, collection_name):
        for collection in self.user_collections:
            if collection['name'] == collection_name:
                return collection

        return None

    def update_collections(self, updated_collections):
        collection_body = json.dumps(updated_collections)

        save_collections(self.user_id, collection_body)

    def import_traits_to_user(self, anon_id):
        collections = get_user_collections(anon_id)
        for collection in collections:
            collection_exists = self.get_collection_by_name(collection['name'])
            if collection_exists:
                continue
            else:
                self.add_collection(collection['name'], collection['members'])

    def delete_session(self):
        # And more importantly delete the redis record
        Redis.delete(self.redis_key)
        self.logged_in = False


