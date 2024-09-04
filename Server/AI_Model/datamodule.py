import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from pickle import dump

NoOfData = 25               # 데이터 셋 총 개수
DataLength = 27             # 각 데이터의 길이(총 27개의 주파수 데이터 측정)
NoOfFeature = 2             # 각 데이터의 특징(magnitude, phase)

'''
데이터를 로드하고 전처리
'''
class Dataset:
    def __init__(self):
        '''
        데이터 로드 및 전처리 함수 호출
        '''
        X_train, y_train = self._load_data()
        self.X_train, self.y_train = self._data_preprocessing(X_train, y_train)

    def _load_data(self):
        '''
        csv 파일 데이터 로드
        '''
        # 데이터를 저장할 numpy 배열 초기화
        TotalData = np.zeros([NoOfData, DataLength, NoOfFeature])
        TotalLabel = np.zeros(NoOfData)

        # K, N, P 값에 대한 임계값 설정
        k_threshold = 400
        n_threshold = 800
        p_threshold = 100

        # 데이터셋 로드 및 라벨 할당
        for i in range(NoOfData):
            # 각 데이터셋 CSV 파일 로드
            file_path = f'data/dataset{i+1}.csv'
            data = pd.read_csv(file_path)

            # 데이터에서 magnitude와 phase 값을 TotalData 배열에 저장
            TotalData[i, :, 0] = data['magnitude'][:DataLength]
            TotalData[i, :, 1] = data['phase'][:DataLength]

            # K, N, P 값을 추출
            K_value = int(data['K'].values[0])
            N_value = int(data['N'].values[0])
            P_value = int(data['P'].values[0])
            
            # K, N, P 값에 따른 라벨 할당
            # class 1: K 400ppm 미만, N 800ppm 미만, P 100ppm 미만
            if K_value < k_threshold and N_value < n_threshold and P_value < p_threshold:       
                label = 0
            # class 2: K 400ppm 미만, N 800ppm 미만, P 100ppm 이상
            elif K_value < k_threshold and N_value < n_threshold and P_value >= p_threshold:
                label = 1
            # class 3: K 400ppm 미만, N 800ppm 이상, P 100ppm 미만
            elif K_value < k_threshold and N_value >= n_threshold and P_value < p_threshold:
                label = 2
            # class 4: K 400ppm 미만, N 800ppm 이상, P 100ppm 이상
            elif K_value < k_threshold and N_value >= n_threshold and P_value >= p_threshold:
                label = 3
            # class 5: K 400ppm 이상, N 800ppm 미만, P 100ppm 미만
            elif K_value >= k_threshold and N_value < n_threshold and P_value < p_threshold:
                label = 4
            # class 1: K 400ppm 이상, N 800ppm 미만, P 100ppm 이상
            elif K_value >= k_threshold and N_value < n_threshold and P_value >= p_threshold:
                label = 5
            # class 1: K 400ppm 이상, N 800ppm 이상, P 100ppm 미만
            elif K_value >= k_threshold and N_value >= n_threshold and P_value < p_threshold:
                label = 6
            # class 1: K 400ppm 이상, N 800ppm 이상, P 100ppm 이상
            elif K_value >= k_threshold and N_value >= n_threshold and P_value >= p_threshold:
                label = 7
            
            TotalLabel[i] = label

        # 로드한 데이터와 라벨의 형태 출력
        print(f"TotalData shape: {TotalData.shape}")
        print(f"TotalLabel shape: {TotalLabel.shape}")
        
        X_train = TotalData
        y_train = TotalLabel
        
        return X_train, y_train

    def _data_preprocessing(self, X, y):
        '''
        데이터 전처리: MinMaxScaler를 사용하여 데이터 스케일링 수행
        '''
        num_sample = X.shape[0]                                             # 샘플 수
        num_feature = X.shape[2]                                            # 특징 수
        
        # MinMaxScaler를 사용하여 데이터를 [0, 1] 범위로 스케일링
        scaler_X = MinMaxScaler()
        X_reshaped = X.reshape(-1, num_feature)                             # 데이터를 2D 배열로 변환 (샘플*타임스텝, 피처)
        scaler_X.fit(X_reshaped)
        X_scaled = scaler_X.transform(X_reshaped)                           # 데이터 스케일링
        X_scaled = X_scaled.reshape(num_sample, DataLength, num_feature)    # 원래 형태로 다시 변환
        # 학습된 스케일러를 저장
        dump(scaler_X, open('./scaler/minmax_scaler_x.pkl', 'wb'))          

        print("Scaled Data:")
        print(X_scaled)
        print(y)

        return X_scaled, y

    def get_data(self):
        '''
        전처리된 데이터 반환
        '''
        return self.X_train, self.y_train
