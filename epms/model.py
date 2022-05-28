import pandas as pd
import numpy as np
from joblib import load
import category_encoders as ce
from typing import List, Optional

class Model:
    """
    Model class.
    """
    def __init__(
        self, 
        model_path: str,
        model_code: Optional[str] = "DS3"
    ):
        """
        Initializes a model object, the class loads the model at model_path.

        Parameters
        ----------
        model_path
            The path to the folder with the saved model objects.
        model_code
            Optionally, a string code identifying the model being loaded, for preprocessing
            and feature list mapping.
        """
        self.model_path = model_path
        self.model_code = model_code
        self.model = load(model_path)
        # Set features based on model code. 
        if self.model_code == "DS3":
            self.features = [
                'fever', 'fatigue', 'diarrhoea', 'chest_pain', 'loss_of_smell', 
                'headache', 'sore_throat', 'unusual_muscle_pains', 'gender', 
                'interacted_with_covid'
                ]

    def _preprocessing(self, df):
        # Make a copy of the df.
        df = df.copy(deep=True)

        # Model specific preprocessing.
        if self.model_code == "DS3":
            # Feature encoding mapping.
            mapping = [
                {"col":"fatigue", "mapping": {'mild':0, 'no':1, 'severe': 2}},
                {"col":"gender", "mapping": {"0.0":0, "1.0": 1}},
                {"col":"interacted_with_covid", 
                "mapping":{ "no":0, "yes_documented_suspected":1,"yes_suspected":2, "yes_documented":3 }}
            ] + [{"col": feature, "mapping": {False:0, True:1}} \
                for feature in ['fever', 'diarrhoea', 'chest_pain', 'loss_of_smell',\
                'headache', 'sore_throat', 'unusual_muscle_pains']]

            # Feature encoding.
            encoder = ce.OrdinalEncoder(mapping=mapping, return_df=True)
            # Select only the expected features and in the expected order.
            df_enc = encoder.fit_transform(df[self.features])
            df_enc = df_enc.astype('int64')
        
        # Set df_enc to the result of preprocessing.
        return df_enc

    def __call__(self, df):
        """Predict by calling the model class."""
        df = self._preprocessing(df)[self.features]
        return self.model.predict(df), self.model.predict_proba(df)
