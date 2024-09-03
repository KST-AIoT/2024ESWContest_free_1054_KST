import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler

NoOfData = 10
DataLength = 38
NoOfFeature = 2
NoOfTrain = 20
NoOfValid = 26
Feature = ['magnitude', 'phase']

class Dataset:
    def __init__(self):
        # 데이터 로드 및 전처리
        X_train, self.y_train, X_valid, self.y_valid = self._load_data()

        self.X_train = self._data_preprocessing(X_train)
        self.X_valid = self._data_preprocessing(X_valid)
        return self.X_train, self.X_valid, self.y_train, self.y_valid
    def _load_data(self):
        # 데이터 로드
        TotalData = np.zeros([NoOfData, DataLength, NoOfFeature]) # 데이터 빈집
        TotalLabel = np.zeros((NoOfData, 3)) #K, N, P
        #X데이터 수집
        for i in range(NoOfData):
            file_path = f'data/dataset{i+1}.csv'
            data = pd.read_csv(file_path)

            #X데이터 수집
            TotalData[i, :, 0] = data['magnitude'].values
            TotalData[i, :, 1] = data['phase'].values

            #Y데이터 수집
            TotalLabel[i, 0] = data['K'].values[0]
            TotalLabel[i, 1] = data['N'].values[0]
            TotalLabel[i, 2] = data['P'].values[0]

        print(f"TotalData shape: {TotalData.shape}")
        print(f"TotalLabel shape: {TotalLabel.shape}")
        
        print(TotalData)
        # 데이터셋 분할 (80% 훈련, 20% 테스트)
        X_train = TotalData[:NoOfTrain, :, :]
        X_valid = TotalData[NoOfTrain:, :, :]
        y_train = TotalLabel[:NoOfValid, :]
        y_valid = TotalLabel[NoOfValid:, :]
        
        return X_train, y_train, X_valid, y_valid
    def _data_preprocessing(self, X):
        # 3차원 데이터를 2차원으로 변환 (samples, time steps * features)
        n_samples, n_timesteps, n_features = X.shape
        X_reshaped = X.reshape(-1, n_features)
        
        # MinMaxScaler를 적용
        scaler_X = MinMaxScaler()
        X_scaled = scaler_X.fit_transform(X_reshaped)
        
        # 다시 3차원으로 변환
        X_scaled = X_scaled.reshape(n_samples, n_timesteps, n_features)
        
        return X_scaled
