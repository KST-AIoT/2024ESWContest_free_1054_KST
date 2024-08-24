import tensorflow_decision_forests as tfdf
import numpy as np
import joblib
from utils import calculate_score

class RF:
    def __init__(self, config, dataset):
        self.X_train = dataset.X_train
        self.X_test = dataset.X_test
        self.X_inference = dataset.X_inference
        self.y_train = dataset.y_train
        self.y_test = dataset.y_test
        self.classifier = tfdf.keras.RandomForestModel(n_estimators=config['n_estimators'], max_depth=config['max_depth'], random_state=config['random_state'])
    def train(self):
        self.classifier.fit(self.X_train, self.y_train)
    def test(self):
        evaluation = self.classifier.evaluate(self.X_test, return_dict = True)
        print(f"Test Accuracy: {evaluation['accuracy']:.4f}")
        return evaluation
    def inference(self):
        y_pred = self.classifier.predict(self.X_inference)
        y_pred = np.argmax(y_pred, axis=1)
        return y_pred
    
    def run(self):
        print("-------------------------Random Forest-------------------------\n", end='')
        self.train()
        self.inference()
        joblib.dump(self.classifier, 'RandomForest/rf_model2.joblib')  
        return self.test()