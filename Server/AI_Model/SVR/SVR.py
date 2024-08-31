from sklearn.svm import SVR
import numpy as np
import joblib
from sklearn.metrics import mean_squared_error, r2_score

# 서포트 벡터 머신 회귀(SVR)
class SVRModel:
    def __init__(self, dataset):
        self.X_train = dataset.X_train
        self.X_test = dataset.X_test
        self.X_inference = dataset.X_inference
        self.y_train_K = dataset.y_train[:, 0]  # K_percent
        self.y_train_N = dataset.y_train[:, 1]  # N_percent
        self.y_train_P = dataset.y_train[:, 2]  # P_percent
        self.y_test_K = dataset.y_test[:, 0]
        self.y_test_N = dataset.y_test[:, 1]
        self.y_test_P = dataset.y_test[:, 2]
        self.classifier_K = SVR(kernel='poly')
        self.classifier_N = SVR(kernel='poly')
        self.classifier_P = SVR(kernel='poly')

    def train(self):
        self.classifier_K.fit(self.X_train, self.y_train_K)
        self.classifier_N.fit(self.X_train, self.y_train_N)
        self.classifier_P.fit(self.X_train, self.y_train_P)

    def test(self):
        y_test_pred_K = self.classifier_K.predict(self.X_test)
        y_test_pred_N = self.classifier_N.predict(self.X_test)
        y_test_pred_P = self.classifier_P.predict(self.X_test)
        
        mse_K = mean_squared_error(self.y_test_K, y_test_pred_K)
        mse_N = mean_squared_error(self.y_test_N, y_test_pred_N)
        mse_P = mean_squared_error(self.y_test_P, y_test_pred_P)
        
        r2_K = r2_score(self.y_test_K, y_test_pred_K)
        r2_N = r2_score(self.y_test_N, y_test_pred_N)
        r2_P = r2_score(self.y_test_P, y_test_pred_P)
        
        print(f"K_percent - MSE: {mse_K:.4f}, R^2: {r2_K:.4f}")
        print(f"N_percent - MSE: {mse_N:.4f}, R^2: {r2_N:.4f}")
        print(f"P_percent - MSE: {mse_P:.4f}, R^2: {r2_P:.4f}")
        
        result = {'mse_K': mse_K, 'r2_K': r2_K, 'mse_N': mse_N, 'r2_N': r2_N, 'mse_P': mse_P, 'r2_P': r2_P}
        return result

    def inference(self):
        y_pred_K = self.classifier_K.predict(self.X_inference)
        y_pred_N = self.classifier_N.predict(self.X_inference)
        y_pred_P = self.classifier_P.predict(self.X_inference)
        return y_pred_K, y_pred_N, y_pred_P

    def run(self):
        print("-------------------------SVR-------------------------\n", end='')
        self.train()
        self.inference()
        joblib.dump(self.classifier_K, 'SVR/svr_model_K.joblib')
        joblib.dump(self.classifier_N, 'SVR/svr_model_N.joblib')
        joblib.dump(self.classifier_P, 'SVR/svr_model_P.joblib')
        return self.test()
