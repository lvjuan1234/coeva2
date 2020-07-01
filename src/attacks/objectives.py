from src.attacks.venus_constraints import evaluate
import numpy as np


def calculate_objectives(result, encoder, initial_state, threshold, model):

    Xs = np.array(list(map(lambda x: x.X, result.pop))).astype(np.float64)
    Xs_ml = encoder.from_genetic_to_ml(initial_state, Xs).astype(np.float64)
    respectsConstraints = (
        encoder.constraint_scaler.transform(evaluate(Xs_ml)).mean(axis=1) <= 0
    ).astype(np.int64)
    isMisclassified = np.array(model.predict_proba(Xs_ml)[:, 1] < threshold).astype(
        np.int64
    )
    isBigAmount = (Xs[:, 0] >= 10000).astype(np.int64)

    o3 = respectsConstraints * isMisclassified
    o4 = o3 * isBigAmount
    objectives = np.array([respectsConstraints, isMisclassified, o3, o4])
    objectives = objectives.sum(axis=1)
    objectives = (objectives > 0).astype(np.int64)

    return objectives