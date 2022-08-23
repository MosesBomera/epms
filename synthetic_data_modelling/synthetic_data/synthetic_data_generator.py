"""
    This script generates synthetic data based on this paper,
    the Makerere COVID-19 survey released on 22/05/2020.

    features    lower_bound upper_bound units
    'age'       16          90          years
    weight      40          200         kgs
    height      110         300         cm
    temperature 34          43          C

    categorical data -> Yes ['1'] or No ['0']
    runny_nose, fever, cough, headache, muscle_ache, fatigue

    target -> +/-
"""
import os

import pandas as pd
import numpy as np

def main():
    # 1. Create the positive cases
    dg = DataGenerator(42, 10000)
    positive = pd.DataFrame(dg.generator())

    # 2. Create the negative cases
    hd = HealthyGenerator(42, 30000)
    negative = pd.DataFrame(hd.generator())

    # 3. Make the full dataset.
    dataset = positive.append(negative, ignore_index=False)

    # dg = DataGenerator(rows=10000, seed=42)
    # df = pd.DataFrame(dg.generator())
    # datatset.to_csv('covid19.csv', index=False)

class DataGenerator:
    """
        Generates data given a distribution.
    """
      def __init__(self, seed, rows):
        self.seed = seed
        self.rows = rows

      def generator(self):
        np.random.seed(self.seed)
        data = [
            {
                'age': np.random.choice(np.arange(16, 90)),
                'weight': np.random.choice(np.arange(35, 200)),
                'height': np.random.choice(np.arange(110, 300)),
                'gender': np.random.choice(['M', 'F'], p=['0.632', '0.368']),
                'fever': np.random.choice(['YES', 'NO'], p=[0.214, 0.786]),
                'cough': np.random.choice(['YES', 'NO'], p=[0.196, 0.804]),
                'runny_nose': np.random.choice(['YES', 'NO'], p=[0.161, 0.839]),
                'headache': np.random.choice(['YES', 'NO'], p=[0.125, 0.875]),
                'muscle_aches': np.random.choice(['YES', 'NO'], p=[0.071, 0.929]),
                'fatigue': np.random.choice(['YES', 'NO'], p=[0.071, 0.929]),
                'target': np.random.choice(['1', '0'], p=[1.0, 0.0]),
            }
            for _ in range(self.rows)
        ]
        return data


class HealthyGenerator(DataGenerator):
    """
        Generates the synthetic data for the negative cases.
    """
    def __init__(self, rows, seed):
        super().__init__(rows, seed)

    def generator(self):
        np.random.seed(self.seed)
        data = [
            {
                'age': np.random.choice(np.arange(16, 90)),
                'weight': np.random.choice(np.arange(35, 200)),
                'height': np.random.choice(np.arange(110, 300)),
                'gender': np.random.choice(['M', 'F'], p=['0.632', '0.368']),
                'fever': np.random.choice(['YES', 'NO'], p=[0.12, 0.88]),
                'cough': np.random.choice(['YES', 'NO'], p=[0.02, 0.98]),
                'runny_nose': np.random.choice(['YES', 'NO'], p=[0.051, 0.949]),
                'headache': np.random.choice(['YES', 'NO'], p=[0.073, 0.927]),
                'muscle_aches': np.random.choice(['YES', 'NO'], p=[0.071, 0.929]),
                'fatigue': np.random.choice(['YES', 'NO'], p=[0.271, 0.729]),
                'target': np.random.choice(['1', '0'], p=[0.0, 1.0]),
            }
            for _ in range(self.rows)
        ]
        return data


if __name__ == '__main__':
    main()
