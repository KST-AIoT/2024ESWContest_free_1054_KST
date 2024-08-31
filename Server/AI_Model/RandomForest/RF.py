from sklearn.ensemble import RandomForestRegressor
import numpy as np
import joblib
from utils import calculate_score

#랜덤 포레스트 회귀
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

        # 회귀 평가 지표로 성능 평가
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
        print("-------------------------Random Forest-------------------------\n", end='')
        self.train()
        self.inference()
        joblib.dump(self.classifier, 'RandomForest/rf_model.joblib')  
        return self.test()