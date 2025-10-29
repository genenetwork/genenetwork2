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


def check_pc_against_specific_traits_pearsons(baseurl):
    print(f"\tERROR — Non fatal: Please implement this test:", end="\t")
    # TODO: Change prompt above
    # TODO: Implement test below, exit with sys.exit(1) on error
    print("OK")

def check_pc_against_specific_traits_spearmans(baseurl):
    print(f"\tERROR — Non fatal: Please implement this test:", end="\t")
    # TODO: Change prompt above
    # TODO: Implement test below, exit with sys.exit(1) on error
    print("OK")

def check_pc_against_entire_dataset_pearsons(baseurl):
    print(f"\tERROR — Non fatal: Please implement this test:", end="\t")
    # TODO: Change prompt above
    # TODO: Implement test below, exit with sys.exit(1) on error
    print("OK")

def check_pc_against_entire_dataset_spearmans(baseurl):
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
