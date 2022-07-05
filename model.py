import pandas as pd
import numpy as np
import onnxruntime as rt
import category_encoders as ce
from typing import List, Optional, Union

class MlModel:
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
        # Load model.
        self.model = rt.InferenceSession(model_path)
        self.input_name = self.model.get_inputs()[0].name 
        self.label_name = self.model.get_outputs()[0].name
        self.prediction = None
        # Set features based on model code. 
        if self.model_code == "DS3":
            self.features = [
                'fever', 'fatigue', 'diarrhoea', 'chest_pain', 'loss_of_smell', 
                'headache', 'sore_throat', 'muscle_pains', 'gender', 'interacted_with_covid']

    def _preprocessing(self, df):
        # Make a copy of the df.
        df = df.copy(deep=True)

        # Model specific preprocessing.
        if self.model_code == "DS3":
            # Feature encoding mapping.
            mapping = [
                {"col":"fatigue", "mapping": {'mild':0, 'no':1, 'severe': 2}},
                {"col":"gender", "mapping": {"male":0, "female": 1}},
                {"col":"interacted_with_covid", 
                "mapping":{ "no":0, "yes_documented_suspected":1,"yes_suspected":2, "yes_documented":3 }}
            ] + [{"col": feature, "mapping": {False:0, True:1}} \
                for feature in ['fever', 'diarrhoea', 'chest_pain', 'loss_of_smell',\
                'headache', 'sore_throat', 'muscle_pains']]

            # Feature encoding.
            encoder = ce.OrdinalEncoder(mapping=mapping, return_df=True)
            # Select only the expected features and in the expected order.
            df_enc = encoder.fit_transform(df[self.features])
            df_enc = df_enc.astype('int64')
        
        # Set df_enc to the result of preprocessing.
        return df_enc

    def _postprocessing(self):
        """
        Process the output to a human-reader format.
        """
        predstring = ''
        pred = self.prediction[0][0]
        if pred==1:
            predstring += f"Positive"
        else:
            predstring += f"Negative"
        return f"{predstring}, Confidence {round(round(self.prediction[1][0][pred], 2)*100)}%"

    def __call__(self, df):
        """
        Predict by calling the model class.
        """
        df = self._preprocessing(df)[self.features]
        self.prediction = self.model.run(None, {self.input_name: df.astype(np.float32).values})
        return self._postprocessing()


class RulesModel:
    def __init__(
        self, 
        temperature: Union[int, float, str], 
        spo2: Union[int, float, str],
        mlmodel_prediction: int
    ):
        """
        Rules based model.

        Parameters
        ----------
        temperature
            The measured temperature.
        sp02
            The measured pulse oximetry.
        mlmodel_prediction
            The machine learning model prediction.
        """
        self.temperature = float(temperature)
        self.spo2 = float(spo2)
        self.mlmodel_prediction = True if mlmodel_prediction == 1 else False

    def __call__(self):
        """
        Run rules-based predictions.
        """
        rules_prediction = None

        if self.temperature >= 37.4 and self.sp02 <= 93:
            # Positive
            rules_prediction = True
        else:
            # Negative.
            rules_prediction = False

        # Combination. 
        if rules_prediction and self.mlmodel_prediction:
            return "Highly Suspicious"
        
        if rules_prediction and not self.mlmodel_prediction:
            return "Suspicious"

        if not rules_prediction and self.mlmodel_prediction:
            return "Suspicious"

        if not rules_prediction and not self.mlmodel_prediction:
            return "Not Suspicious"