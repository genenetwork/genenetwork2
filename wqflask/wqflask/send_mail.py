from __future__ import absolute_import, division, print_function

import datetime
import time

import simplejson as json

from redis import StrictRedis
Redis = StrictRedis()

import mailer

def timestamp():
    ts = datetime.datetime.utcnow()
    return ts.isoformat()

def main():
    while True:
        print("I'm alive!")

        # Set something so we know it's running (or at least been running recently)
        Redis.setex("send_mail:ping", 300, time.time())

        msg = Redis.blpop("mail_queue", 30)

        if msg:
            # Queue name is the first element, we want the second, which is the actual message
            msg = msg[1]

            print("\n\nGot a msg in queue at {}: {}".format(timestamp(), msg))
            # Todo: Truncate mail_processed when it gets to long
            Redis.rpush("mail_processed", msg)
            process_message(msg)



def process_message(msg):
    msg = json.loads(msg)

    message = mailer.Message()
    message.From = msg['From']
    message.To = msg['To']
    message.Subject = msg['Subject']
    message.Body = msg['Body']

    sender = mailer.Mailer('localhost')
    sender.send(message)
    print("Sent message at {}: {}\n".format(timestamp(), msg))


if __name__ == '__main__':
    main()
