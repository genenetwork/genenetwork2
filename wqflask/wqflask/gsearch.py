import json
from types import SimpleNamespace

from pymonad.maybe import Just, Maybe, Nothing
from pymonad.tools import curry
import xapian

from base import webqtlConfig
from utility.authentication_tools import check_resource_availability
from utility.monads import MonadicDict
from wqflask.database import xapian_database


def is_permitted_for_listing(trait, search_type):
    """Check if it is permissible to list trait in search results."""
    dataset_type = {"gene": "ProbeSet", "phenotype": "Publish"}
    dataset_ob = (Maybe.apply(curry(2, lambda id, species:
                                    SimpleNamespace(id=id,
                                                    type=dataset_type[search_type],
                                                    name=trait["dataset"],
                                                    species=species)))
                  .to_arguments(trait["dataset_id"], trait["species"]))
    return (Maybe.apply(curry(2, check_resource_availability))
            .to_arguments(dataset_ob, trait["name"])
            .map(lambda permissions:
                 ((isinstance(permissions["data"], list)) and ("view" in permissions["data"]))
                 or (permissions["data"] != 'no-access'))
            .maybe(False, lambda x: x))


class GSearch:
    def __init__(self, kwargs):
        if ("type" not in kwargs) or ("terms" not in kwargs):
            raise ValueError
        self.type = kwargs["type"]
        self.terms = kwargs["terms"]

        queryparser = xapian.QueryParser()
        queryparser.set_stemmer(xapian.Stem("en"))
        queryparser.set_stemming_strategy(queryparser.STEM_SOME)
        querystring = self.terms
        query = queryparser.parse_query(querystring)
        # FIXME: Handle presentation (that is, formatting strings for
        # display) in the template rendering, not when retrieving
        # search results.
        chr_mb = curry(2, lambda chr, mb: f"Chr{chr}: {mb:.6f}")
        format3f = lambda x: f"{x:.3f}"
        hmac = curry(2, lambda dataset, dataset_fullname: f"{dataset_fullname}:{dataset}")
        self.trait_list = []
        # pylint: disable=invalid-name
        with xapian_database() as db:
            enquire = xapian.Enquire(db)
            # Filter documents by type.
            enquire.set_query(xapian.Query(xapian.Query.OP_FILTER,
                                           query,
                                           xapian.Query(f"XT{self.type}")))
            for i, trait in enumerate(
                    [trait for xapian_match in enquire.get_mset(0, db.get_doccount())
                     if is_permitted_for_listing(
                             trait := MonadicDict(json.loads(xapian_match.document.get_data())),
                             search_type=self.type)]):
                trait["index"] = Just(i)
                trait["location_repr"] = (Maybe.apply(chr_mb)
                                          .to_arguments(trait.pop("chr"), trait.pop("mb")))
                trait["LRS_score_repr"] = trait.pop("lrs").map(format3f)
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
                        trait["display_name"] = (Maybe.apply(lambda inbredsetcode, name:
                                                             f"{inbredsetcode}_{name}")
                                                 .to_arguments(inbredsetcode, trait["name"]))
                    trait["hmac"] = (Maybe.apply(hmac)
                                     .to_arguments(trait.pop("dataset_fullname"), trait["name"]))
                    trait["authors_display"] = (trait.pop("authors").map(
                        lambda authors:
                        ", ".join(authors[:2] + ["et al."] if len(authors) >=2 else authors)))
                    trait["pubmed_text"] = (trait["year"].bind(
                        lambda year: Just(year) if year.isdigit() else Nothing))
                    trait["pubmed_link"] = (trait["pubmed_id"].map(
                        lambda pubmedid: webqtlConfig.PUBMEDLINK_URL % pubmedid))
                self.trait_list.append(trait.data)
            self.trait_count = len(self.trait_list)
