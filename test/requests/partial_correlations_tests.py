"""Regression tests to ensure partial correlations work."""
import requests
import traceback
from pathlib import Path
from typing import Union

from lxml import etree
from urllib.parse import urljoin


def start_traits(return_dicts: bool = False) -> Union[str, tuple[dict, ...]]:
    """Return a list of traits to use as our starting point."""
    traits_str = "1418100_at|||HC_M2_0606_P|||CNS-specific putative synapse associated non-coding RNA; 3' region|||A030009H04Rik|||Chr11: 69.155556|||12.012|||72.900|||Chr11: 68.922567;;;1427044_a_at|||HC_M2_0606_P|||amphiphysin (synaptic vesicle, stiff-man syndrome with breast cancer 128kD autoantigen, actin assembly); distal 3' UTR|||Amph|||Chr13: 19.242342|||12.872|||22.800|||Chr13: 17.979063;;;1446192_at|||HC_M2_0606_P|||amphiphysin (synaptic vesicle, stiff-man syndrome with breast cancer 128kD autoantigen, actin assembly); abundantly expressed transcript from intron 1 (from EST AK033933)|||Amph|||Chr13: 19.044619|||8.611|||9.800|||Chr17: 52.853979;;;1459605_at|||HC_M2_0606_P|||amyloid beta (A4) precursor protein binding, family  A, member 1 (Veli3-CASK-Mint1 complex, PDZ domain, synapse and cell-cell junction associated); exon 2 of long form|||Apba1|||Chr19: 23.967566|||8.090|||11.000|||Chr14: 118.861653;;;1435464_at|||HC_M2_0606_P|||RIKEN cDNA 1110003E01 (high CNS expression related to synapses); far 3' UTR or downstream transcript (from EST AK017411)|||1110003E01Rik|||Chr5: 65.838112|||11.017|||27.400|||Chr5: 59.037549"
    if return_dicts:
        return tuple(
            dict(zip(
                ("trait_id", "dataset", "description", "symbol", "location", "mean",
                 "peak-minus-log-p", "peak-location"),
                line.split("|||")))
                for line in traits_str.split(";;;"))
    return traits_str


def check_partial_correlations_entry_page(baseurl: str):
    """Check that the partial correlations entry page loads."""
    print(f"\tLoading the correlations entry-point page:", end="\t")
    result = requests.post(urljoin(baseurl, "/partial_correlations"),
                           data={"trait_list": start_traits(False)})
    assert result.status_code == 200
    # TODO: Add other asserts
    print("OK")


def __select_primary_controls_targets__(traits: tuple[dict, ...], primary: int, controls: tuple[int, ...], targets: tuple[int, ...]) -> dict:
    return {
        f"trait_{traits[primary]['trait_id']}": f"primary_{traits[primary]['trait_id']}",
        **{
            f"trait_{traits[control]['trait_id']}": f"controls_{traits[control]['trait_id']}"
            for control in controls
        },
        **{
            f"trait_{traits[target]['trait_id']}": f"targets_{traits[target]['trait_id']}"
            for target in targets
        }
    }


def do_request(uri, postdata):
    """Run request and poll until we get a result."""
    result = requests.post(uri, postdata)

    while True:
        doc = etree.HTML(result.text)
        meta_tags = doc.xpath("//meta[@http-equiv='refresh']")
        assert 0 <= len(meta_tags) < 2, "Too many refresh meta tags."
        if len(meta_tags) == 0:
            return result

        new_uri = urljoin(
            uri,
            meta_tags[0].attrib['content'][
                meta_tags[0].attrib['content'].index("URL=")+4:])
        result = requests.get(new_uri)


def check_pc_against_specific_traits_pearsons(baseurl):
    """Check partial correlations against specific traits using Pearson's r."""
    print(f"\tPearson's R partial correlations against select target traits:", end="\t")
    traits = start_traits(True)
    result = do_request(urljoin(baseurl, "/partial_correlations"),
                        postdata={
                            "trait_list": start_traits(False),
                            **__select_primary_controls_targets__(
                                traits, 0, (1, 2), (3, 4)),
                            "method": "pearson's r",
                            "criteria": 500,
                            "submit": "with_target_pearsons"
                        })
    assert result.status_code == 200, (
        f"Status code was not 200, it was {result.status_code}")

    doc = etree.HTML(result.text)
    table_rows = doc.xpath("//table[@id='part-corr-results-publish']/tbody/tr")
    assert len(table_rows) == 2, (
        f"Expected exactly 2 rows of results. Got {len(row)}")

    rtraits = traits[3:]
    rtraits_names = tuple(trait["trait_id"] for trait in rtraits)
    for idx, row in enumerate(table_rows):
        cells = row.xpath(".//td")
        assert len(cells) == 12, "Expected exactly 12 table cells."
        assert cells[2].text == traits[idx]["dataset"], (
            f"Expected dataset '{traits[idx]['dataset']}': "
            f"got '{cells[2].text}'.")

        link = cells[3].xpath(".//a")[0]
        assert link.text.strip() in rtraits_names, (
            f"Expected trait ID '{rtraits[idx]['trait_id']}': "
            f"got '{link.text}'")
    print("OK")


def check_pc_against_specific_traits_spearmans(baseurl):
    """Check partial correlations against specific traits using Spearman's rho."""
    print(f"\tERROR — Non fatal: Please implement this test:", end="\t")
    # TODO: Change prompt above
    # TODO: Implement test below, exit with sys.exit(1) on error
    print("OK")


def check_pc_against_entire_dataset_pearsons(baseurl):
    """Check partial correlations against entire dataset using Pearson's r."""
    print(f"\tERROR — Non fatal: Please implement this test:", end="\t")
    # TODO: Change prompt above
    # TODO: Implement test below, exit with sys.exit(1) on error
    print("OK")


def check_pc_against_entire_dataset_spearmans(baseurl):
    """Check partial correlations against entire dataset using Spearman's rho."""
    print(f"\tERROR — Non fatal: Please implement this test:", end="\t")
    # TODO: Change prompt above
    # TODO: Implement test below, exit with sys.exit(1) on error
    print("OK")


def check_all_partial_correlations(args_obj, parser):
    print("\r\nChecking partial correlations\n")
    baseurl = args_obj.host
    check_partial_correlations_entry_page(baseurl)
    check_pc_against_specific_traits_pearsons(baseurl)
    check_pc_against_specific_traits_spearmans(baseurl)
    check_pc_against_entire_dataset_pearsons(baseurl)
    check_pc_against_entire_dataset_spearmans(baseurl)
