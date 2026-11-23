"""Scientific experiment components used by the rolling-origin runner."""
import numpy as np


def quantile(errors, alpha, corrected):
    errors = np.sort(np.asarray(errors))
    rank = int(np.ceil((len(errors) + 1) * (1 - alpha))) if corrected else int(np.ceil(len(errors) * (1-alpha)))
    # Known bounded outcome: a radius of 100 yields the entire valid support.
    return 100.0 if rank > len(errors) else float(errors[rank - 1])
