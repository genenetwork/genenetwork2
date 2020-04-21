class ESDouble(object):
    def __init__(self):
        self.items = {}

    def ping(self):
        return true

    def create(self, index, doc_type, body, id):
        self.items["index"] = {doc_type: {"id": id, "_source": data}}

    def search(self, index, doc_type, body):
        return {
            "hits": {
                "hits": self.items[index][doc_type][body]
            }}
