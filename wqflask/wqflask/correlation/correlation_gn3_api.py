"""module that calls the gn3 api's to do the correlation """
from base import data_set
from base.trait import create_trait
from base.trait import retrieve_sample_data







def compute_sample_r(start_vars,target_dataset, trait_data, target_samplelist, method="pearson"):
    import requests
    from wqflask.correlation.correlation_gn3_api import compute_correlation

    cor_results = compute_correlation(start_vars)

    data = {
        "target_dataset": target_dataset,
        "target_samplelist": target_samplelist,
        "trait_data": {
            "trait_sample_data": trait_data,
            "trait_id": "HC_Q"
        }
    }
    requests_url = f"http://127.0.0.1:8080/api/correlation/sample_x/{method}"

    results = requests.post(requests_url, json=data)

    data = results.json()

    print(data)

    return data


def process_samples(start_vars,sample_names,excluded_samples=None):
    sample_data = {}
    if not excluded_samples:
        excluded_samples = ()

        sample_vals_dict  = json.loads(start_vars["sample_vals"])

        for sample in sample_names:
            if sample not in excluded_samples:
                val = sample_val_dict[sample]
                if not val.strip().lower() == "x":
                    sample_data[str(sample)]=float(value)

    return sample_data


def create_fetch_dataset_data(dataset_name):
    this_dataset  = data_set.create_dataset(dataset_name=dataset_name)

    this_dataset.get_trait_data()


def create_target_this_trait(start_vars):
    """this function prefetch required data for correlation"""

    this_dataset = data_set.create_dataset(dataset_name=start_vars['dataset'])
    target_dataset = data_set.create_dataset(
        dataset_name=start_vars['corr_dataset'])

    this_trait = create_trait(dataset=this_dataset,
                              name=start_vars['trait_id'])

    this_trait = retrieve_sample_data(this_trait, this_dataset)

    target_dataset.get_trait_data()

    return (this_dataset,this_trait,target_dataset)
def compute_correlation(start_vars):

    this_dataset, this_trait, target_dataset = create_target_this_trait(
        start_vars=start_vars)
