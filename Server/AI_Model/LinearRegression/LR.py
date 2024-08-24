import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import joblib

class LR:
    def __init__(self, dataset):
        self.X_train = dataset.X_train
        self.X_test = dataset.X_test
        self.X_inference = dataset.X_inference
        self.y_train = dataset.y_train
        self.y_test = dataset.y_test
        self.classifier = LinearRegression()

    def train(self):
        self.classifier.fit(self.X_train, self.y_train)
    def test(self):
        y_test_pred = self.classifier.predict(self.X_test)
        mse = np.mean((self.y_test - y_test_pred) ** 2)
        r2 = self.classifier.score(self.X_test, self.y_test)
        
        print(f"Mean Squared Error: {mse:.4f}")
        print(f"R^2 Score: {r2:.4f}")
        
        result = {'mse': mse, 'r2': r2}
        return result
    def inference(self):
        y_pred = self.classifier.predict(self.X_inference)
        return y_pred
    
    def run(self):
        print("-------------------------Linear Regression-------------------------\n", end='')
        self.train()
        self.inference()
        joblib.dump(self.classifier, 'LinearRegression/LR_model.joblib')  
        return self.test()