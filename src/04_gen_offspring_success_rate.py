import pandas as pd
from joblib import load
import numpy as np

from attacks.objectives import calculate_success_rates
from attacks.venus_encoder import VenusEncoder
from utils import Pickler, in_out
from utils.in_out import pickle_from_dir

config = in_out.get_parameters()


out_columns = [
    "n_gen",
    "pop_size",
    "n_offsprings",
    "o1",
    "o2",
    "o3",
    "o4",
]


def process(results, encoder, threshold, model):
    success_rates = calculate_success_rates(results, encoder, threshold, model)
    return np.concatenate(
        [
            np.array([results[0].n_gen, results[0].pop_size, results[0].n_offsprings]),
            success_rates,
        ]
    )


def run(
    ATTACK_RESULTS_DIR=config["dirs"]["attack_results"],
    OBJECTIVES_PATH=config["paths"]["objectives"],
    THRESHOLD=config["threshold"],
    MODEL_PATH=config["paths"]["model"],
):
    model = load(MODEL_PATH)
    model.set_params(verbose=0, n_jobs=1)
    encoder = VenusEncoder()

    success_rates = np.array(
        pickle_from_dir(
            ATTACK_RESULTS_DIR,
            handler=lambda i, x: process(x, encoder, THRESHOLD, model),
        )
    )

    success_rates_df = pd.DataFrame(success_rates, columns=out_columns)
    success_rates_df.to_csv(OBJECTIVES_PATH, index=False)


if __name__ == "__main__":
    run()
