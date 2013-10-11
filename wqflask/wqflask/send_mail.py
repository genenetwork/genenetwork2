from __future__ import absolute_import, division, print_function

import datetime

import simplejson as json

from redis import StrictRedis
Redis = StrictRedis()

import mailer

def timestamp():
    ts = datetime.datetime.utcnow()
    return ts.isoformat()
    
def main():
    while True:
        print("Waiting for message to show up in queue...")
        msg = Redis.blpop("mail_queue")
        
        # Queue name is the first element, we want the second, which is the actual message
        msg = msg[1]
        
        print("\nGot a msg in queue at {}: {}".format(timestamp(), msg))
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