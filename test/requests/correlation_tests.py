import csv
import sys
import html
import json
import requests
from lxml import etree
from pathlib import Path
from lxml.html import parse
from functools import reduce
from link_checker import check_page

def corrs_base_data():
    return [
        {
            "dataset": "HC_M2_0606_P",
            "trait_id": "1435464_at",
            "corr_dataset": "HC_M2_0606_P",
        },
        {
            "dataset": "HC_M2_0606_P",
            "trait_id": "1457545_at",
            "corr_dataset": "HC_M2_0606_R",
        },
        {
            "dataset": "HC_M2_0606_P",
            "trait_id": "1442370_at",
            "corr_dataset": "BXDPublish",
        }
    ]
def sample_vals():
    return '{"C57BL/6J":"10.835","DBA/2J":"11.142","B6D2F1":"11.126","D2B6F1":"11.143","BXD1":"10.811","BXD2":"11.503","BXD5":"10.766","BXD6":"10.986","BXD8":"11.050","BXD9":"10.822","BXD11":"10.670","BXD12":"10.946","BXD13":"10.890","BXD14":"x","BXD15":"10.884","BXD16":"11.222","BXD18":"x","BXD19":"10.968","BXD20":"10.962","BXD21":"10.906","BXD22":"11.080","BXD23":"11.046","BXD24":"11.146","BXD24a":"x","BXD25":"x","BXD27":"11.078","BXD28":"11.034","BXD29":"10.808","BXD30":"x","BXD31":"11.087","BXD32":"11.029","BXD33":"10.662","BXD34":"11.482","BXD35":"x","BXD36":"x","BXD37":"x","BXD38":"10.836","BXD39":"10.926","BXD40":"10.638","BXD41":"x","BXD42":"10.974","BXD43":"10.828","BXD44":"10.900","BXD45":"11.358","BXD48":"11.042","BXD48a":"10.975","BXD49":"x","BXD50":"11.228","BXD51":"11.126","BXD52":"x","BXD53":"x","BXD54":"x","BXD55":"11.580","BXD56":"x","BXD59":"x","BXD60":"10.829","BXD61":"11.152","BXD62":"11.156","BXD63":"10.942","BXD64":"10.506","BXD65":"11.126","BXD65a":"11.272","BXD65b":"11.157","BXD66":"11.071","BXD67":"11.080","BXD68":"10.997","BXD69":"11.096","BXD70":"11.152","BXD71":"x","BXD72":"x","BXD73":"11.262","BXD73a":"11.444","BXD73b":"x","BXD74":"10.974","BXD75":"11.150","BXD76":"10.920","BXD77":"10.928","BXD78":"x","BXD79":"11.371","BXD81":"x","BXD83":"10.946","BXD84":"11.181","BXD85":"10.992","BXD86":"10.770","BXD87":"11.200","BXD88":"x","BXD89":"10.930","BXD90":"11.183","BXD91":"x","BXD93":"11.056","BXD94":"10.737","BXD95":"x","BXD98":"10.986","BXD99":"10.892","BXD100":"x","BXD101":"x","BXD102":"x","BXD104":"x","BXD105":"x","BXD106":"x","BXD107":"x","BXD108":"x","BXD109":"x","BXD110":"x","BXD111":"x","BXD112":"x","BXD113":"x","BXD114":"x","BXD115":"x","BXD116":"x","BXD117":"x","BXD119":"x","BXD120":"x","BXD121":"x","BXD122":"x","BXD123":"x","BXD124":"x","BXD125":"x","BXD126":"x","BXD127":"x","BXD128":"x","BXD128a":"x","BXD130":"x","BXD131":"x","BXD132":"x","BXD133":"x","BXD134":"x","BXD135":"x","BXD136":"x","BXD137":"x","BXD138":"x","BXD139":"x","BXD141":"x","BXD142":"x","BXD144":"x","BXD145":"x","BXD146":"x","BXD147":"x","BXD148":"x","BXD149":"x","BXD150":"x","BXD151":"x","BXD152":"x","BXD153":"x","BXD154":"x","BXD155":"x","BXD156":"x","BXD157":"x","BXD160":"x","BXD161":"x","BXD162":"x","BXD165":"x","BXD168":"x","BXD169":"x","BXD170":"x","BXD171":"x","BXD172":"x","BXD173":"x","BXD174":"x","BXD175":"x","BXD176":"x","BXD177":"x","BXD178":"x","BXD180":"x","BXD181":"x","BXD183":"x","BXD184":"x","BXD186":"x","BXD187":"x","BXD188":"x","BXD189":"x","BXD190":"x","BXD191":"x","BXD192":"x","BXD193":"x","BXD194":"x","BXD195":"x","BXD196":"x","BXD197":"x","BXD198":"x","BXD199":"x","BXD200":"x","BXD201":"x","BXD202":"x","BXD203":"x","BXD204":"x","BXD205":"x","BXD206":"x","BXD207":"x","BXD208":"x","BXD209":"x","BXD210":"x","BXD211":"x","BXD212":"x","BXD213":"x","BXD214":"x","BXD215":"x","BXD216":"x","BXD217":"x","BXD218":"x","BXD219":"x","BXD220":"x"}'

def do_request(url, data):
    response = requests.post(
        url,
        data={
            "dataset": "HC_M2_0606_P",
            "trait_id": "1435464_at",
            "corr_dataset": "HC_M2_0606_P",
            "corr_sample_method": "pearson",
            "corr_return_results": "100",
            "corr_samples_group": "samples_primary",
            "sample_vals": sample_vals(),
            "location_type": "gene",
            **data,
        })
    while response.text.find('<meta http-equiv="refresh" content="5">') >= 0:
        response = requests.get(response.url)
        pass
    return response

def check_sample_correlations(baseurl, base_data):
    data = {
        **base_data,
        "corr_type": "sample",
        "corr_sample_method": "pearson",
        "location_type": "gene",
        "corr_return_results": "200"
    }
    top_n_message = "The top 200 correlations ranked by the Genetic Correlation"
    result = do_request(f"{baseurl}/corr_compute", data)
    assert result.status_code == 200
    assert (result.text.find(f"Values of record {base_data['trait_id']}") >= 0), result.text
    assert (result.text.find(top_n_message) >= 0), result.text

def check_tissue_correlations(baseurl, base_data):
    data = {
        **base_data,
        "corr_type": "tissue",
        "location_type": "gene",
    }
    result = do_request(f"{baseurl}/corr_compute", data)

    assert result.status_code == 200
    if (data["trait_id"] == "1442370_at"
        and data["corr_dataset"] in ("BXDPublish",)):
        top_n_message = (
            "It is not possible to compute the 'Tissue' correlations between "
            f"trait '{data['trait_id']}' and the data")
    else:
        top_n_message = "The top 100 correlations ranked by the Tissue Correlation"
        assert (result.text.find(f"Values of record {base_data['trait_id']}") >= 0), result.text

    assert (html.unescape(result.text).find(top_n_message) >= 0), (
        f"NOT FOUND: {top_n_message}")

def check_lit_correlations(baseurl, base_data):
    data = {
        **base_data,
        "corr_type": "lit",
        "corr_return_results": "200"
    }
    result = do_request(f"{baseurl}/corr_compute", data)

    assert result.status_code == 200
    if (data["trait_id"] == "1442370_at"
        and data["corr_dataset"] in ("BXDPublish",)):
        top_n_message = (
            "It is not possible to compute the 'Literature' correlations "
            f"between trait '{data['trait_id']}' and the data")
    else:
        top_n_message = "The top 200 correlations ranked by the Literature Correlation"
        assert (result.text.find(f"Values of record {base_data['trait_id']}") >= 0), result.text

    assert (html.unescape(result.text).find(top_n_message) >= 0), (
        f"NOT FOUND: {top_n_message}")

def check_correlations(args_obj, parser):
    print("")
    print("Checking the correlations...")
    corr_type_fns = {
        "sample": check_sample_correlations,
        "tissue": check_tissue_correlations,
        "lit": check_lit_correlations
    }
    host = args_obj.host
    failure = False
    for corr_type, corr_type_fn in corr_type_fns.items():
        for corr_base in corrs_base_data():
            try:
                print(f"\tChecking {corr_type} correlations...", end="")
                corr_type_fn(host, corr_base)
                print(" ok")
            except AssertionError as asserterr:
                print (f" fail: {asserterr.args[0]}")
                failure = True

    if failure:
        print("FAIL!")
        sys.exit(1)
    print("OK")

def thread(value, *functions):
    return reduce(lambda result, func: func(result), functions, value)

def parse_results_from_html(raw_html):
    doc = etree.HTML(raw_html)
    scripts = doc.xpath('//script')
    for script in scripts:
        script_content = thread(
            script.xpath('.//child::text()'),
            lambda val: "".join(val).strip())
        if script_content.find("var tableJson") >= 0:
            return {
                str(row["trait_id"]): row for row in
                json.loads(thread(
                    script_content,
                    lambda val: val[len("var tableJson = "):].strip().replace(
                        "\\r\\n", "\\n")))}

    return {}

def parse_expected(filepath):
    with open(filepath, encoding="utf-8") as infl:
        reader = csv.DictReader(infl, dialect=csv.unix_dialect)
        for line in reader:
            yield line

def collect_failures(actual, expected, keys):
    # assert len(actual) == len(expected), (
    #     f"Expected {len(expected)} results but instead got {len(actual)} "
    #     "results")
    def __equal(trait_id, act_row, exp_row):
        if act_row is None:
            return (f"Could not find trait '{trait_id}' in actual results",)
        __eq = tuple()
        for act_key, exp_key, title in keys:
            act_val, exp_val = (
                str(act_row[act_key]).strip(), str(exp_row[exp_key]).strip())
            if act_val == exp_val:
                # __eq = __eq + ("PASSED",)
                continue
            __eq = __eq + ((
                f"Trait '{trait_id}': "
                f"Different '{title}' values: expected:\n\t\t'{repr(exp_val)}'"
                "\n\nbut got\n"
                f"\n\t\t'{repr(act_val)}'"),)
            continue
        return __eq

    return tuple(
        item for item in (
            __equal(str(exp_row["Record"]),
                    actual.get(str(exp_row["Record"])),
                    exp_row)
            for exp_row in expected)
        if bool(item))

def check_correctness(host):
    # pearsons_keys = (
    #     ("trait_id", "Record ID", "Trait/Record ID"),
    #     ("sample_r", "Sample r ?", "Sample r value"),
    #     ("num_overlap", "N Cases", "N Cases"),
    #     ("sample_p", "Sample p(r) ?", "Sample p value"),
    #     ("symbol", "Symbol", "Symbol"),
    #     ("description", "Description", "Description"),
    #     ("location", "Location Chr and Mb", "Location Chr and Mb"),
    #     ("mean", "Mean Expr", "Mean"),
    #     ("lrs_location", "Max LRS Location Chr and Mb", "Max LRS Location Chr and Mb"),
    #     ("lit_corr", "Lit Corr ?", "Literature Correlation"),
    #     ("tissue_corr", "Tissue r ?", "Tissue Correlation r"),
    #     ("tissue_pvalue", "Tissue p(r) ?", "Tissue Correlation p value"))

    
    pearsons_keys = (
        ("trait_id", "Record", "Trait/Record ID"),
        ("sample_r", "Sample r", "Sample r value"),
        ("num_overlap", "N", "N Cases"),
        ("sample_p", "Sample p(r)", "Sample p value"),
        ("description", "Description", "Description"))

    spearmans_keys = (
        ("trait_id", "Record ID", "Trait/Record ID"),
        ("sample_r", "Sample rho ?", "Sample rho value"),
        ("num_overlap", "N Cases", "N Cases"),
        ("sample_p", "Sample p(rho) ?", "Sample p(rho) value"),
        ("symbol", "Symbol", "Symbol"),
        ("description", "Description", "Description"),
        ("location", "Location Chr and Mb", "Location Chr and Mb"),
        ("mean", "Mean Expr", "Mean"),
        ("lrs_location", "Max LRS Location Chr and Mb", "Max LRS Location Chr and Mb"),
        ("lit_corr", "Lit Corr ?", "Literature Correlation"),
        ("tissue_corr", "Tissue rho ?", "Tissue Correlation rho"),
        ("tissue_pvalue", "Tissue p(rho) ?", "Tissue Correlation p(rho) value"))
    failures = {}
    tests = [
        ("Trait '10710' (Dataset 'BXDPublish'): Sample Correlation, Pearson, 500 results",
         {"dataset": "BXDPublish", "trait_id": "10710",
          "corr_dataset": "BXDPublish", "corr_type": "sample",
          "corr_sample_method": "pearson", "location_type": "highest_lod",
          "corr_samples_group": "samples_primary",
          "sample_vals": '{"C57BL/6J":"23.000","DBA/2J":"21.390","B6D2F1":"x","D2B6F1":"x","BXD1":"25.505","BXD2":"20.197","BXD5":"27.270","BXD6":"18.768","BXD8":"21.440","BXD9":"23.974","BXD11":"24.309","BXD12":"20.669","BXD13":"18.857","BXD14":"21.035","BXD15":"21.350","BXD16":"20.869","BXD18":"20.812","BXD19":"22.859","BXD20":"19.768","BXD21":"23.424","BXD22":"25.430","BXD23":"18.924","BXD24":"22.433","BXD24a":"x","BXD25":"19.590","BXD27":"19.938","BXD28":"20.123","BXD29":"18.741","BXD30":"19.160","BXD31":"20.330","BXD32":"25.748","BXD33":"23.531","BXD34":"22.670","BXD35":"20.276","BXD36":"21.417","BXD37":"x","BXD38":"19.805","BXD39":"21.827","BXD40":"23.241","BXD41":"x","BXD42":"24.039","BXD43":"21.778","BXD44":"26.300","BXD45":"22.730","BXD48":"x","BXD48a":"x","BXD49":"x","BXD50":"x","BXD51":"24.827","BXD52":"x","BXD53":"x","BXD54":"x","BXD55":"x","BXD56":"x","BXD59":"x","BXD60":"24.055","BXD61":"x","BXD62":"25.336","BXD63":"22.865","BXD64":"x","BXD65":"x","BXD65a":"21.949","BXD65b":"21.836","BXD66":"x","BXD67":"x","BXD68":"x","BXD69":"22.643","BXD70":"x","BXD71":"x","BXD72":"x","BXD73":"23.606","BXD73a":"x","BXD73b":"x","BXD74":"x","BXD75":"22.097","BXD76":"x","BXD77":"24.020","BXD78":"x","BXD79":"x","BXD81":"x","BXD83":"23.811","BXD84":"x","BXD85":"22.137","BXD86":"26.518","BXD87":"21.136","BXD88":"x","BXD89":"20.182","BXD90":"22.480","BXD91":"x","BXD93":"x","BXD94":"x","BXD95":"x","BXD98":"x","BXD99":"x","BXD100":"x","BXD101":"x","BXD102":"x","BXD104":"x","BXD105":"x","BXD106":"x","BXD107":"x","BXD108":"x","BXD109":"x","BXD110":"x","BXD111":"x","BXD112":"x","BXD113":"x","BXD114":"x","BXD115":"x","BXD116":"x","BXD117":"x","BXD119":"x","BXD120":"x","BXD121":"x","BXD122":"x","BXD123":"x","BXD124":"x","BXD125":"x","BXD126":"x","BXD127":"x","BXD128":"x","BXD128a":"x","BXD130":"x","BXD131":"x","BXD132":"x","BXD133":"x","BXD134":"x","BXD135":"x","BXD136":"x","BXD137":"x","BXD138":"x","BXD139":"x","BXD141":"x","BXD142":"x","BXD144":"x","BXD145":"x","BXD146":"x","BXD147":"x","BXD148":"x","BXD149":"x","BXD150":"x","BXD151":"x","BXD152":"x","BXD153":"x","BXD154":"x","BXD155":"x","BXD156":"x","BXD157":"x","BXD160":"x","BXD161":"x","BXD162":"x","BXD165":"x","BXD168":"x","BXD169":"x","BXD170":"x","BXD171":"x","BXD172":"x","BXD173":"x","BXD174":"x","BXD175":"x","BXD176":"x","BXD177":"x","BXD178":"x","BXD180":"x","BXD181":"x","BXD183":"x","BXD184":"x","BXD186":"x","BXD187":"x","BXD188":"x","BXD189":"x","BXD190":"x","BXD191":"x","BXD192":"x","BXD193":"x","BXD194":"x","BXD195":"x","BXD196":"x","BXD197":"x","BXD198":"x","BXD199":"x","BXD200":"x","BXD201":"x","BXD202":"x","BXD203":"x","BXD204":"x","BXD205":"x","BXD206":"x","BXD207":"x","BXD208":"x","BXD209":"x","BXD210":"x","BXD211":"x","BXD212":"x","BXD213":"x","BXD214":"x","BXD215":"x","BXD216":"x","BXD217":"x","BXD218":"x","BXD219":"x","BXD220":"x"}',
          "corr_return_results": "500"},
         "BXD_10710_vs_BXDPublish.csv",
         pearsons_keys),
    ]

    for test_title, test_data, expected_file, method_keys in tests:
        print(f"Test: {test_title} ...", end="\t")
        response = requests.post(f"{host}/corr_compute", data=test_data)
        while response.text.find('<meta http-equiv="refresh" content="5">') >= 0:
            response = requests.get(response.url)
            pass
        results = parse_results_from_html(response.text)
        if len(results) == 0:
            failures = {
                **failures,
                test_title: (("No results found.",),)}
            continue
        filepath = Path.cwd().parent.joinpath(
            f"test/requests/correlation_results_text_files/{expected_file}")
        failures = {
            key: value for key,value in {
                **failures,
                test_title: collect_failures(
                    results, tuple(parse_expected(filepath)), method_keys)
            }.items() if len(value) > 0
        }

    if len(failures) > 0:
        print("\n\nFAILURES: ")
        for test_title, failures in failures.items():
            print(f"\nTest: {test_title}")
            for result, result_failures in enumerate(failures):
                for failure in result_failures:
                    print(f"\tResult {result}: {failure}")
                    print_newline = True
                if len(result_failures) > 0:
                    print("")
        return False

    print("")
    return True

def check_correlations_correctness(args_obj, parser):
    print("")
    print("Checking the correctness of the correlations...")
    if not check_correctness(args_obj.host):
        sys.exit(1)
