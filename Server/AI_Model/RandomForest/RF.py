from sklearn.ensemble import RandomForestRegressor
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
        self.classifier = RandomForestRegressor(n_estimators=config['n_estimators'], max_depth=config['max_depth'], random_state=config['random_state'])
    def train(self):
        self.classifier.fit(self.X_train, self.y_train)
    def test(self):
        y_test_pred = self.classifier.predict(self.X_test)
        y_test_pred = np.argmax(y_test_pred, axis = 1)
        self.y_test = np.argmax(self.y_test, axis = 1)
        result = calculate_score(self.y_test, y_test_pred)
        print(f'Test Accuracy for Random Forest is {result["accuracy"][0]:.4f}')
        return result
    def inference(self):
        y_pred = self.classifier.predict(self.X_inference)
        y_pred = np.argmax(y_pred, axis=1)
        return y_pred
    
    def run(self):
        print("-------------------------Random Forest-------------------------\n", end='')
        self.train()
        self.inference()
        joblib.dump(self.classifier, 'RandomForest/rf_model.joblib')  
        return self.test()