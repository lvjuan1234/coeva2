import numpy as np
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
import pandas as pd
import copy


class VenusEncoder:
    def __init__(self):
        # Creates encoders
        self.one_hot_position = np.array([14])
        self.one_hot_size = np.array([14])
        self.one_hot_encoders = [OneHotEncoder(sparse=False)]
        features = pd.read_csv("../data/lcld/datatypes.csv", low_memory=False)
        self.features = features.drop(features.tail(1).index)
        constraints = pd.read_csv("../data/lcld/constraints.csv", low_memory=False)
        constraint_scaler = MinMaxScaler(feature_range=(0, 1))
        vector = [constraints["min"], constraints["max"]]
        constraint_scaler.fit(vector)
        self.constraint_scaler = constraint_scaler
        self.mask = self.features["mutable"].to_numpy()
        self.LOG_ALPHA = 0.00000001
        self.AMOUNT_BETA = 0.00000001
        f1_scaler = MinMaxScaler(feature_range=(0, 1))
        f1_scaler.fit([[np.log(self.LOG_ALPHA)], [np.log(1)]])
        self.f1_scaler = f1_scaler
        f2_scaler = MinMaxScaler(feature_range=(0, 1))
        f2_scaler.fit([[0], [np.sqrt(47)]])
        self.f2_scaler = f2_scaler
        for i, encoder in enumerate(self.one_hot_encoders):
            possible_values = np.arange(self.one_hot_size[i])
            possible_values = possible_values.reshape(len(possible_values), 1)
            encoder.fit(possible_values)

    def to_one_hot(self, x):
        concat = [x[:, : self.one_hot_position[0]]]
        for i in np.arange(len(self.one_hot_encoders)):
            lower = self.one_hot_position[0] + i
            upper = lower + 1
            concat.append(self.one_hot_encoders[i].transform(x[:, lower:upper]))
        return np.concatenate(concat, axis=1)

    def from_one_hot(self, x):
        concat = [x[:, : self.one_hot_position[0]]]
        for i in np.arange(len(self.one_hot_encoders)):
            lower = self.one_hot_position[i]
            upper = lower + self.one_hot_size[i]
            concat.append(self.one_hot_encoders[i].inverse_transform(x[:, lower:upper]))
        return np.concatenate(concat, axis=1)

    def from_genetic_to_ml(self, x_original, x):
        x_original = np.stack((x_original,) * len(x))
        x_out = copy.deepcopy(x_original)
        x_one_hot = self.to_one_hot(x)
        x_out[:, self.mask] = x_one_hot
        return x_out

    def from_ml_to_genetic(self, x_original):
        x_filtered = copy.deepcopy(x_original)
        x_filtered = x_filtered[:, self.mask]
        x_out = self.from_one_hot(x_filtered)
        return x_out

    def get_min_max_genetic(self):
        f_filtered = copy.deepcopy(self.features)
        f_filtered = f_filtered[f_filtered["mutable"]]
        f_filtered = f_filtered[["min", "max"]]
        f_filtered = f_filtered.to_numpy()
        f_filtered = np.transpose(f_filtered)
        concat = [f_filtered[:, : self.one_hot_position[0]]]
        for i in np.arange(len(self.one_hot_encoders)):
            concat.append(np.array([[0], [self.one_hot_size[i] - 1]]))
        return np.concatenate(concat, axis=1)
