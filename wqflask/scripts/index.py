"""This script must be run each time the database is updated. It runs
queries against the SQL database, indexes the results and builds a
xapian index. This xapian index is later used in providing search
through the web interface.

"""

from functools import partial
import json
import xapian

from utility.monads import sql_query_mdict
from wqflask.database import database_connection, xapian_writable_database


def index_text(termgenerator, text):
    """Index text and increase term position."""
    termgenerator.index_text(text)
    termgenerator.increase_termpos()


# pylint: disable=invalid-name
def write_document(db, idterm, doctype, doc):
    """Write document into xapian database."""
    # We use the XT prefix to indicate the type.
    doc.add_boolean_term(f"XT{doctype}")
    doc.add_boolean_term(idterm)
    db.replace_document(idterm, doc)


# pylint: disable=missing-function-docstring
def main():
    termgenerator = xapian.TermGenerator()
    termgenerator.set_stemmer(xapian.Stem("en"))

    indexer = partial(index_text, termgenerator)

    authors_indexer = lambda text: termgenerator.index_text(text, 1, "A")
    species_indexer = lambda text: termgenerator.index_text(text, 1, "XS")
    group_indexer = lambda text: termgenerator.index_text(text, 1, "XG")
    tissue_indexer = lambda text: termgenerator.index_text(text, 1, "XI")
    description_indexer = lambda text: termgenerator.index_text(text, 1, "XD")
    dataset_indexer = lambda text: termgenerator.index_text(text, 1, "XDS")
    symbol_indexer = lambda text: termgenerator.index_text(text, 1, "XY")
    chr_indexer = lambda text: termgenerator.index_text(text, 0, "XC")
    peakchr_indexer = lambda text: termgenerator.index_text(text, 0, "XPC")

    mean_adder = lambda mean: doc.add_value(0, xapian.sortable_serialise(mean))
    peak_adder = lambda peak: doc.add_value(1, xapian.sortable_serialise(peak))
    mb_adder = lambda mb: doc.add_value(2, xapian.sortable_serialise(mb))
    peakmb_adder = lambda peakmb: doc.add_value(3, xapian.sortable_serialise(peakmb))
    additive_adder = lambda additive: doc.add_value(4, xapian.sortable_serialise(additive))
    year_adder = lambda year: doc.add_value(5, xapian.sortable_serialise(float(year)))

    # FIXME: Some Max LRS values in the DB are wrongly listed as
    # 0.000, but shouldn't be displayed. Make them NULLs in the
    # database.
    # pylint: disable=invalid-name
    with xapian_writable_database() as db:
        with database_connection() as conn:
            for trait in sql_query_mdict(conn, """
            SELECT ProbeSet.Name AS name,
                   ProbeSet.Symbol AS symbol,
                   ProbeSet.description AS description,
                   ProbeSet.Chr AS chr,
                   ProbeSet.Mb AS mb,
                   ProbeSet.alias AS alias,
                   ProbeSet.GenbankId AS genbankid,
                   ProbeSet.UniGeneId AS unigeneid,
                   ProbeSet.Probe_Target_Description AS probe_target_description,
                   ProbeSetFreeze.Name AS dataset,
                   ProbeSetFreeze.FullName AS dataset_fullname,
                   ProbeSetFreeze.Id AS dataset_id,
                   Species.Name AS species,
                   InbredSet.Name AS `group`,
                   Tissue.Name AS tissue,
                   ProbeSetXRef.Mean AS mean,
                   ProbeSetXRef.LRS AS lrs,
                   ProbeSetXRef.additive AS additive,
                   Geno.Chr as geno_chr,
                   Geno.Mb as geno_mb
            FROM Species
                 INNER JOIN InbredSet ON InbredSet.SpeciesId = Species.Id
                 INNER JOIN ProbeFreeze ON ProbeFreeze.InbredSetId = InbredSet.Id
                 INNER JOIN Tissue ON ProbeFreeze.TissueId = Tissue.Id
                 INNER JOIN ProbeSetFreeze ON ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id
                 INNER JOIN ProbeSetXRef ON ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
                 INNER JOIN ProbeSet ON ProbeSet.Id = ProbeSetXRef.ProbeSetId
                 LEFT JOIN Geno ON ProbeSetXRef.Locus = Geno.Name AND Geno.SpeciesId = Species.Id
            WHERE ProbeSetFreeze.confidentiality < 1 AND ProbeSetFreeze.public > 0
            """):
                doc = xapian.Document()
                termgenerator.set_document(doc)

                # Add values.
                trait["mean"].bind(mean_adder)
                trait["lrs"].bind(peak_adder)
                trait["mb"].bind(mb_adder)
                trait["geno_mb"].bind(peakmb_adder)
                trait["additive"].bind(additive_adder)

                # Index text.
                trait["name"].bind(indexer)
                trait["description"].bind(indexer)
                trait["symbol"].bind(indexer)
                trait.pop("alias").bind(indexer)
                trait.pop("genbankid").bind(indexer)
                trait.pop("unigeneid").bind(indexer)
                trait.pop("probe_target_description").bind(indexer)
                trait["species"].bind(species_indexer)
                trait["group"].bind(group_indexer)
                trait["tissue"].bind(tissue_indexer)
                trait["description"].bind(description_indexer)
                trait["dataset"].bind(dataset_indexer)
                trait["symbol"].bind(symbol_indexer)
                trait["chr"].bind(chr_indexer)
                trait["geno_chr"].bind(peakchr_indexer)

                doc.set_data(json.dumps(trait.data))
                write_document(db, trait["name"].bind(lambda name: f"Q{name}"), "gene", doc)

        with database_connection() as conn:
            # FIXME: Some years are blank strings or strings that
            # contain text other than the year. These should be fixed
            # in the database and the year field must be made an integer.
            for i, trait in enumerate(sql_query_mdict(conn, """
            SELECT Species.Name AS species,
                   InbredSet.Name AS `group`,
                   PublishFreeze.Name AS dataset,
                   PublishFreeze.FullName AS dataset_fullname,
                   PublishXRef.Id AS name,
                   COALESCE(Phenotype.Post_publication_abbreviation, Phenotype.Pre_publication_abbreviation) AS abbreviation,
                   COALESCE(Phenotype.Post_publication_description, Phenotype.Pre_publication_description) AS description,
                   Phenotype.Lab_code,
                   Publication.Abstract,
                   Publication.Title,
                   Publication.Authors AS authors,
                   IF(CONVERT(Publication.Year, UNSIGNED)=0, NULL, CONVERT(Publication.Year, UNSIGNED)) AS year,
                   Publication.PubMed_ID AS pubmed_id,
                   PublishXRef.LRS as lrs,
                   PublishXRef.additive,
                   InbredSet.InbredSetCode AS inbredsetcode,
                   PublishXRef.mean,
                   PublishFreeze.Id AS dataset_id,
                   Geno.Chr as geno_chr,
                   Geno.Mb as geno_mb
            FROM Species
                 INNER JOIN InbredSet ON InbredSet.SpeciesId = Species.Id
                 INNER JOIN PublishFreeze ON PublishFreeze.InbredSetId = InbredSet.Id
                 INNER JOIN PublishXRef ON PublishXRef.InbredSetId = InbredSet.Id
                 INNER JOIN Phenotype ON PublishXRef.PhenotypeId = Phenotype.Id
                 INNER JOIN Publication ON PublishXRef.PublicationId = Publication.Id
                 LEFT JOIN Geno ON PublishXRef.Locus = Geno.Name AND Geno.SpeciesId = Species.Id
            """)):
                doc = xapian.Document()
                termgenerator.set_document(doc)

                # Add values.
                trait["mean"].bind(mean_adder)
                trait["lrs"].bind(peak_adder)
                trait["geno_mb"].bind(peakmb_adder)
                trait["additive"].bind(additive_adder)
                trait["year"].bind(year_adder)

                # Index text.
                trait.pop("abbreviation").bind(indexer)
                trait["description"].bind(indexer)
                trait.pop("Lab_code").bind(indexer)
                trait.pop("Abstract").bind(indexer)
                trait.pop("Title").bind(indexer)
                trait["authors"].bind(indexer)
                trait["inbredsetcode"].bind(indexer)
                trait["species"].bind(species_indexer)
                trait["group"].bind(group_indexer)
                trait["description"].bind(description_indexer)
                trait["authors"].bind(authors_indexer)
                trait["geno_chr"].bind(peakchr_indexer)

                # Convert name from integer to string.
                trait["name"] = trait["name"].map(str)
                # Split comma-separated authors into a list.
                trait["authors"] = trait["authors"].map(
                    lambda s: [author.strip() for author in s.split(",")])

                doc.set_data(json.dumps(trait.data))
                write_document(db, f"Q{i}", "phenotype", doc)


if __name__ == "__main__":
    main()
