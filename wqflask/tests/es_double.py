class ESDouble(object):
    def __init__(self):
        self.items = {
            "users": {
                "local": []
            }}

    def ping(self):
        return true

    def create(self, index, doc_type, body, id):
        item = {"id": id, "_source": body}
        if not self.items.get("index", None):
            self.items[index] = {doc_type: [item]}
        else:
            self.items[index][doc_type].append(item)

    def search(self, index, doc_type, body):
        d = body["query"]["match"]
        column = [(key, d[key]) for key in d]

        items = []
        for thing in self.items[index][doc_type]:
            if thing["_source"][column[0][0]] == column[0][1]:
                items.append(thing)
                break
        return {
            "hits": {
                "hits": items
            }}
