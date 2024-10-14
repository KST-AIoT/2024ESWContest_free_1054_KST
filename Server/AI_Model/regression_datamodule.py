import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from pickle import dump
import os
import glob

DataLength = 27  # 각 데이터의 길이(총 27개의 주파수 데이터 측정)
NoOfFeature = 2  # 각 데이터의 특징(magnitude, phase)

'''
데이터를 로드하고 전처리
'''


class Dataset:
    def __init__(self, folder_path='data/'):
        '''
        데이터 로드 및 전처리 함수 호출
        '''
        self.folder_path = folder_path  # 데이터를 불러올 폴더 경로
        X_train, y_train = self._load_data()
        self.X_train, self.y_train = self._data_preprocessing(X_train, y_train)

    def _load_data(self):
        '''
        csv 파일 데이터 로드
        '''
        # 폴더 내의 모든 csv 파일 경로 리스트 가져오기
        csv_files = glob.glob(os.path.join(self.folder_path, '*.csv'))
        NoOfData = len(csv_files)  # CSV 파일 개수에 따라 자동으로 할당

        # 데이터를 저장할 numpy 배열 초기화
        TotalData = np.zeros([NoOfData, DataLength, NoOfFeature])
        TotalLabel = np.zeros((NoOfData, 3))

        # 데이터셋 로드 및 라벨 할당
        for i, file_path in enumerate(csv_files):
            # 각 데이터셋 CSV 파일 로드
            data = pd.read_csv(file_path)

            # 데이터에서 magnitude와 phase 값을 TotalData 배열에 저장
            TotalData[i, :, 0] = data['magnitude'][:DataLength]
            TotalData[i, :, 1] = data['phase'][:DataLength]

            # K, N, P 값을 추출
            K_value = data['K'].values[0]
            N_value = data['N'].values[0]
            P_value = data['P'].values[0]

            TotalLabel[i] = [K_value, N_value, P_value]

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
        num_sample = X.shape[0]  # 샘플 수
        num_feature = X.shape[2]  # 특징 수

        # MinMaxScaler를 사용하여 데이터를 [0, 1] 범위로 스케일링(x)
        scaler_X = MinMaxScaler()
        X_reshaped = X.reshape(-1, num_feature)  # 데이터를 2D 배열로 변환 (샘플*타임스텝, 피처)
        scaler_X.fit(X_reshaped)
        X_scaled = scaler_X.transform(X_reshaped)  # 데이터 스케일링
        X_scaled = X_scaled.reshape(num_sample, DataLength, num_feature)  # 원래 형태로 다시 변환
        # 학습된 스케일러를 저장
        dump(scaler_X, open('./scaler/minmax_scaler_x.pkl', 'wb'))

        # MinMaxScaler를 사용하여 y(K, N, P) 데이터를 각각 스케일링
        scaler_K = MinMaxScaler()
        scaler_N = MinMaxScaler()
        scaler_P = MinMaxScaler()

        K_scaled = scaler_K.fit_transform(y[:, 0].reshape(-1, 1))  # K 값을 스케일링
        N_scaled = scaler_N.fit_transform(y[:, 1].reshape(-1, 1))  # N 값을 스케일링
        P_scaled = scaler_P.fit_transform(y[:, 2].reshape(-1, 1))  # P 값을 스케일링

        # 스케일링된 라벨 값을 다시 결합
        y_scaled = np.hstack([K_scaled, N_scaled, P_scaled])
        # K, N, P 스케일러를 각각 저장
        dump(scaler_K, open('./scaler/minmax_scaler_K.pkl', 'wb'))
        dump(scaler_N, open('./scaler/minmax_scaler_N.pkl', 'wb'))
        dump(scaler_P, open('./scaler/minmax_scaler_P.pkl', 'wb'))

        print("Scaled Data:")
        print(X_scaled)
        print(y_scaled)

        return X_scaled, y_scaled

    def get_data(self):
        '''
        전처리된 데이터 반환
        '''
        return self.X_train, self.y_train


# 사용 예시
dataset = Dataset(folder_path='data/')
X_train, y_train = dataset.get_data()
