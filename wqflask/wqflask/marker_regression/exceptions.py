"""Mapping Exception classes."""

class NoMappingResultsError(Exception):
    "Exception to raise if no results are computed."

    def __init__(self, trait, dataset, mapping_method):
        self.trait = trait
        self.dataset = dataset
        self.mapping_method = mapping_method
        self.message = (
            f"The mapping of trait '{trait}' from dataset '{dataset}' using "
            f"the '{mapping_method}' mapping method returned no results.")
        super().__init__(self.message, trait, mapping_method)
