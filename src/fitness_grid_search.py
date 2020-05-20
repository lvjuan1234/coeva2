import pickle
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)
import logging

import numpy as np
from joblib import Parallel, delayed, load
import pandas as pd
from utils.venus_encoder import VenusEncoder
from utils.venus_attack import attack
from utils import Pickler
from utils import venus_constraints

logging.basicConfig(level=logging.DEBUG)

# ----- PARAMETERS

input_dir = "../../../out/2020-05-20-venus"
output_dir = "../../../out/venus_attacks/coeva2_all_grid_test"
threshold = 0.24
n_jobs = 6

n_generation = 25
pop_size = 16
n_offsprings = 8

n_random_parameters = 2
n_initial_state = 10
n_repetition = 2

# ----- CONSTANTS

model_file = "/model.joblib"
X_attack_candidate_file = "/X_attack_candidate.npy"
scaler_file = "/scaler.pickle"
out_columns = [
    "weight_1",
    "weight_2",
    "weight_3",
    "weight_4",
    "objective_1",
    "objective_2",
    "objective_3",
    "objective_4",
]

# ----- Load and create necessary objects

model = load(input_dir + model_file)
model.set_params(verbose=0, n_jobs=1)
X_initial_states = np.load(input_dir + X_attack_candidate_file)
scaler = Pickler.load_from_file(input_dir + scaler_file)
encoder = VenusEncoder()
X_initial_states = X_initial_states[:n_initial_state]

# ----- Check if constraints are satisfied
constraints = venus_constraints.evaluate(X_initial_states)
constraints_violated = (constraints > 0).sum()
if constraints_violated > 0:
    logging.error("Constraints violated {} time(s).".format(constraints_violated))
    exit(1)

if __name__ == "__main__":

    # Parameter loop
    for i in range(n_random_parameters):

        # Randomly generate weight
        weight = np.absolute(np.random.normal(size=4))
        logging.info(
            "Parameters: {} ({}/{})".format(weight, i + 1, n_random_parameters)
        )

        parameter_objectives = []

        # Repetition loop
        for j in range(n_repetition):
            logging.info("Round: {}/{}".format(j + 1, n_repetition))

            # Initial state loop (threaded)
            initial_states_objectives = Parallel(n_jobs=n_jobs)(
                delayed(attack)(
                    index,
                    initial_state,
                    weight,
                    model,
                    scaler,
                    encoder,
                    n_generation,
                    n_offsprings,
                    pop_size,
                    threshold,
                )
                for index, initial_state in enumerate(X_initial_states)
            )
            # Add objective to list
            parameter_objectives.extend(initial_states_objectives)

        # Calculate success rate
        parameter_objectives = np.array(parameter_objectives)
        success_rate = np.apply_along_axis(
            lambda x: x.sum() / x.shape[0], 0, parameter_objectives
        )

        # Save results
        results = np.concatenate((weight, success_rate))
        results_df = pd.DataFrame(results.reshape(1, -1), columns=out_columns)
        results_df.to_csv("parameters_{}.csv".format(i), index=False)
