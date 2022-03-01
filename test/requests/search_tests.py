import requests

searches = [
    { 
        "found_text": "1 records were found",
        "data": {
            "species": "mouse",
            "group": "BXD",
            "type": "Hippocampus mRNA",
            "dataset": "HC_M2_0606_P",
            "search_terms_or": "PD-1",
            "search_terms_and": ""
        }
    },
    { 
        "found_text": "4 records were found",
        "data": {
            "species": "mouse",
            "group": "BXD",
            "type": "Hippocampus mRNA",
            "dataset": "HC_M2_0606_P",
            "search_terms_or": "Ank-1",
            "search_terms_and": ""
        }
    },
    { 
        "found_text": "1017 records were found",
        "data": {
            "species": "mouse",
            "group": "BXD",
            "type": "Hippocampus mRNA",
            "dataset": "HC_M2_0606_P",
            "search_terms_or": "sh*",
            "search_terms_and": ""
        }
    }
]

def check_fulltext_searches(host):
    for this_search in searches:
        result = requests.get(host+"/search", params=this_search["data"])
        found = result.text.find(this_search["found_text"])
        assert(found >= 0)
        assert(result.status_code == 200)
        print("OK")
