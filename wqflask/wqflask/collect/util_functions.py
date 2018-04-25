from wqflask import user_manager
from utility.elasticsearch_tools import get_item_by_unique_column

index = "collections"
doc_type = "all"

def process_traits(unprocessed_traits):
    #print("unprocessed_traits are:", unprocessed_traits)
    if isinstance(unprocessed_traits, basestring):
        unprocessed_traits = unprocessed_traits.split(",")
    traits = set()
    for trait in unprocessed_traits:
        #print("trait is:", trait)
        data, _separator, hmac = trait.rpartition(':')
        data = data.strip()
        assert hmac==user_manager.actual_hmac_creation(data), "Data tampering?"
        traits.add(str(data))

    return traits
