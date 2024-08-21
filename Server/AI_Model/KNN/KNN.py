from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
import joblib
import numpy as np

class KNN:
    def __init__(self, config, dataset):
        self.config = config
        self.X_train = dataset.X_train
        self.X_test = dataset.X_test
        self.X_inference = dataset.X_inference
        self.y_train = dataset.y_train
        self.y_test = dataset.y_test
        
        self.scaler_X = StandardScaler()
        self.X_train = self.scaler_X.fit_transform(self.X_train)
        self.X_test = self.scaler_X.transform(self.X_test)
        
        self.classifier = KNeighborsRegressor(n_neighbors=config['n_neighbors'])
    
    def train(self):
        self.classifier.fit(self.X_train, self.y_train)
    
    def test(self):
        y_test_pred = self.classifier.predict(self.X_test)
        mae = mean_absolute_error(self.y_test, y_test_pred, multioutput='raw_values')
        print(f'Mean Absolute Error for K_percent: {mae[0]:.4f}')
        print(f'Mean Absolute Error for N_percent: {mae[1]:.4f}')
        print(f'Mean Absolute Error for P_percent: {mae[2]:.4f}')
        return mae
    
    def inference(self):
        y_pred = self.classifier.predict(self.X_inference)
        return y_pred
    
    def run(self):
        print("-------------------------KNN Model-------------------------\n", end='')
        self.train()
        self.inference()
        joblib.dump(self.classifier, 'KNN/knn_model.joblib')  
        return self.test()
