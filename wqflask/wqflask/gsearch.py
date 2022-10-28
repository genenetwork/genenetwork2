from urllib.parse import urlencode, urljoin

from pymonad.maybe import Just, Maybe
from pymonad.tools import curry
import requests

from gn3.monads import MonadicDict
from utility.tools import GN3_LOCAL_URL

# KLUDGE: Due to the lack of pagination, we hard-limit the maximum
# number of search results.
MAX_SEARCH_RESULTS = 10000

class GSearch:
    def __init__(self, kwargs):
        if ("type" not in kwargs) or ("terms" not in kwargs):
            raise ValueError
        self.type = kwargs["type"]
        self.terms = kwargs["terms"]

        # FIXME: Handle presentation (that is, formatting strings for
        # display) in the template rendering, not when retrieving
        # search results.
        chr_mb = curry(2, lambda chr, mb: f"Chr{chr}: {mb:.6f}")
        format3f = lambda x: f"{x:.3f}"
        hmac = curry(2, lambda dataset, dataset_fullname: f"{dataset_fullname}:{dataset}")
        convert_lod = lambda x: x / 4.61
        self.trait_list = []
        for i, trait in enumerate(requests.get(
                urljoin(GN3_LOCAL_URL, "/api/search?" + urlencode({"query": self.terms,
                                                                   "type": self.type,
                                                                   "per_page": MAX_SEARCH_RESULTS}))).json()):
            trait = MonadicDict(trait)
            trait["index"] = Just(i)
            trait["location_repr"] = (Maybe.apply(chr_mb)
                                      .to_arguments(trait.pop("chr"), trait.pop("mb")))
            trait["LRS_score_repr"] = trait.pop("lrs").map(convert_lod).map(format3f)
            trait["additive"] = trait["additive"].map(format3f)
            trait["mean"] = trait["mean"].map(format3f)
            trait["max_lrs_text"] = (Maybe.apply(chr_mb)
                                     .to_arguments(trait.pop("geno_chr"), trait.pop("geno_mb")))
            if self.type == "gene":
                trait["hmac"] = (Maybe.apply(hmac)
                                 .to_arguments(trait["dataset"], trait["dataset_fullname"]))
            elif self.type == "phenotype":
                trait["display_name"] = trait["name"]
                inbredsetcode = trait.pop("inbredsetcode")
                if inbredsetcode.map(len) == Just(3):
                    trait["display_name"] = (Maybe.apply(
                        curry(2, lambda inbredsetcode, name: f"{inbredsetcode}_{name}"))
                                             .to_arguments(inbredsetcode, trait["name"]))
                trait["hmac"] = (Maybe.apply(hmac)
                                 .to_arguments(trait.pop("dataset_fullname"), trait["name"]))
                trait["authors_display"] = (trait.pop("authors").map(
                    lambda authors:
                    ", ".join(authors[:2] + ["et al."] if len(authors) >=2 else authors)))
                trait["pubmed_text"] = trait["year"].map(str)
            self.trait_list.append(trait.data)
        self.trait_count = len(self.trait_list)
