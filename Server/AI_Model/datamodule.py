import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from pickle import dump

NoOfData = 25
DataLength = 27
NoOfFeature = 2

class Dataset:
    def __init__(self):
        X_train, y_train = self._load_data()
        self.X_train, self.y_train = self._data_preprocessing(X_train, y_train)

    def _load_data(self):
        TotalData = np.zeros([NoOfData, DataLength, NoOfFeature])
        TotalLabel = np.zeros(NoOfData)

        k_threshold = 400
        n_threshold = 800
        p_threshold = 100

        for i in range(NoOfData):
            file_path = f'data/dataset{i+1}.csv'
            data = pd.read_csv(file_path)
            TotalData[i, :, 0] = data['magnitude'][:DataLength]
            TotalData[i, :, 1] = data['phase'][:DataLength]
            K_value = int(data['K'].values[0])
            N_value = int(data['N'].values[0])
            P_value = int(data['P'].values[0])
            
            # Assigning label based on the thresholds
            if K_value < k_threshold and N_value < n_threshold and P_value < p_threshold:
                label = 0
            elif K_value < k_threshold and N_value < n_threshold and P_value >= p_threshold:
                label = 1
            elif K_value < k_threshold and N_value >= n_threshold and P_value < p_threshold:
                label = 2
            elif K_value < k_threshold and N_value >= n_threshold and P_value >= p_threshold:
                label = 3
            elif K_value >= k_threshold and N_value < n_threshold and P_value < p_threshold:
                label = 4
            elif K_value >= k_threshold and N_value < n_threshold and P_value >= p_threshold:
                label = 5
            elif K_value >= k_threshold and N_value >= n_threshold and P_value < p_threshold:
                label = 6
            elif K_value >= k_threshold and N_value >= n_threshold and P_value >= p_threshold:
                label = 7
            
            TotalLabel[i] = label

        print(f"TotalData shape: {TotalData.shape}")
        print(f"TotalLabel shape: {TotalLabel.shape}")
        
        X_train = TotalData
        y_train = TotalLabel
        
        return X_train, y_train

    def _data_preprocessing(self, X, y):
        num_sample = X.shape[0]
        num_feature = X.shape[2]
        
        scaler_X = MinMaxScaler()
        X_reshaped = X.reshape(-1, num_feature)
        scaler_X.fit(X_reshaped)
        X_scaled = scaler_X.transform(X_reshaped)
        X_scaled = X_scaled.reshape(num_sample, DataLength, num_feature)

        dump(scaler_X, open('./scaler/minmax_scaler_x.pkl', 'wb'))

        print("Scaled Data:")
        print(X_scaled)
        print(y)

        return X_scaled, y

    def get_data(self):
        return self.X_train, self.y_train
