"""Correlation-Specific Exceptions"""

class WrongCorrelationType(Exception):
    """Raised when a correlation is requested for incompatible datasets."""

    def __init__(self, trait, target_dataset, corr_method):
        message = (
            f"It is not possible to compute the '{corr_method}' correlations "
            f"between trait '{trait.name}' and the data in the "
            f"'{target_dataset.fullname}' dataset. "
            "Please try again after selecting another type of correlation.")
        super().__init__(message)
