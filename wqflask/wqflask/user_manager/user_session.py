import redis # used for collections
from flask import request
from utility.logger import getLogger
from utility.elasticsearch_tools import (get_elasticsearch_connection,
                                         get_user_by_unique_column)

from .util_functions import verify_cookie

Redis = redis.StrictRedis()
logger = getLogger(__name__)
THREE_DAYS = 60 * 60 * 24 * 3

class UserSession(object):
    """Logged in user handling"""

    cookie_name = 'session_id_v2'

    def __init__(self):
        cookie = request.cookies.get(self.cookie_name)
        if not cookie:
            self.logged_in = False
            return
        else:
            session_id = verify_cookie(cookie)

            self.redis_key = self.cookie_name + ":" + session_id
            logger.debug("self.redis_key is:", self.redis_key)
            self.session_id = session_id
            self.record = Redis.hgetall(self.redis_key)


            if not self.record:
                # This will occur, for example, when the browser has been left open over a long
                # weekend and the site hasn't been visited by the user
                self.logged_in = False

                ########### Grrr...this won't work because of the way flask handles cookies
                # Delete the cookie
                #response = make_response(redirect(url_for('login')))
                #response.set_cookie(self.cookie_name, '', expires=0)
                #flash(
                #   "Due to inactivity your session has expired. If you'd like please login again.")
                #return response
                return

            if Redis.ttl(self.redis_key) < THREE_DAYS:
                # (Almost) everytime the user does something we extend the session_id in Redis...
                logger.debug("Extending ttl...")
                Redis.expire(self.redis_key, THREE_DAYS)

            logger.debug("record is:", self.record)
            self.logged_in = True

    @property
    def user_id(self):
        """Shortcut to the user_id"""
        if 'user_id' in self.record:
            return self.record['user_id']
        else:
            return ''

    @property
    def user_ob(self):
        """Actual sqlalchemy record"""
        # Only look it up once if needed, then store it
        # raise "OBSOLETE: use ElasticSearch instead"
        try:
            # Already did this before
            return self.db_object
        except AttributeError:
            # Doesn't exist so we'll create it
            self.db_object = get_user_by_unique_column(
                es=get_elasticsearch_connection(),column_name = "user_id",
                column_value=self.user_id)
            return self.db_object


    def delete_session(self):
        # And more importantly delete the redis record
        Redis.delete(self.cookie_name)
        logger.debug("At end of delete_session")
