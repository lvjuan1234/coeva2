import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)

from attacks import attack_multiple_input
from attacks.result_process import EfficientResult

import random
import logging
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed, load

from utils import Pickler, in_out

from attacks import venus_constraints
from attacks.venus_encoder import VenusEncoder

logging.getLogger().setLevel(logging.INFO)

config = in_out.get_parameters()


def run(
    MODEL_PATH=config["paths"]["model"],
    SCALER_PATH=config["paths"]["scaler"],
    X_ATTACK_CANDIDATES_PATH=config["paths"]["x_candidates"],
    ATTACK_RESULTS_DIR=config["dirs"]["attack_results"],
    RANDOM_SEED=config["random_seed"],
    LIST_N_OFFSPRING=config["list_n_offsprings"],
    BUDGET=config["budget"],
    N_REPETITION=config["n_repetition"],
    ALGORITHM=config["algorithm"],
    N_INITIAL_STATE=config["n_initial_state"],
    WEIGHT=config["weights"],
    INITIAL_STATE_OFFSET=config["initial_state_offset"],
):

    Path(ATTACK_RESULTS_DIR).mkdir(parents=True, exist_ok=True)

    # ----- Load and create necessary objects

    model = load(MODEL_PATH)
    model.set_params(verbose=0, n_jobs=1)
    X_initial_states = np.load(X_ATTACK_CANDIDATES_PATH)
    scaler = Pickler.load_from_file(SCALER_PATH)
    encoder = VenusEncoder()
    X_initial_states = X_initial_states[
        INITIAL_STATE_OFFSET : INITIAL_STATE_OFFSET + N_INITIAL_STATE
    ]

    # ----- Check constraints

    venus_constraints.respect_constraints_or_exit(X_initial_states)

    # ----- Set random seed
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # ----- Copy the initial states n_repetition times
    X_initial_states = np.repeat(X_initial_states, N_REPETITION, axis=0)

    list_n_offsprings = np.array(LIST_N_OFFSPRING)
    list_n_generation = (BUDGET / list_n_offsprings).astype(np.int)
    list_pop_size = list_n_offsprings * 2

    for i in range(len(list_n_offsprings)):
        n_gen = list_n_generation[i]
        pop_size = list_pop_size[i]
        n_offsprings = list_n_offsprings[i]

        logging.info(
            "Parameters: {} {} {} ({}/{})".format(
                n_gen, pop_size, n_offsprings, i + 1, len(list_n_offsprings)
            )
        )

        # Initial state loop (threaded)
        results = attack_multiple_input.attack(
            model,
            scaler,
            encoder,
            n_gen,
            pop_size,
            n_offsprings,
            X_initial_states,
            weight=WEIGHT,
            attack_type=ALGORITHM,
        )

        efficient_results = [EfficientResult(result) for result in results]

        Pickler.save_to_file(
            efficient_results,
            "{}/results_{}_{}.pickle".format(
                ATTACK_RESULTS_DIR, n_gen, INITIAL_STATE_OFFSET
            ),
        )


if __name__ == "__main__":
    run()
