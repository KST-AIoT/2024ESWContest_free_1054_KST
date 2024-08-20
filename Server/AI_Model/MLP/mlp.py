import pandas as pd
import numpy as np
from keras import layers
from keras import models
from utils import calculate_score

class MLP:
    def __init__(self, config, dataset):
        self.config = config
        self.X_train = dataset.X_train
        self.X_test = dataset.X_test
        self.X_inference = dataset.X_inference
        self.y_train = dataset.y_train
        self.y_test = dataset.y_test
        self.classifier = models.Sequential()
    def train(self):
        self.classifier.fit(self.X_train, 
                            self.y_train,
                            epochs = self.config['epochs'],
                            validation_data=(self.X_test, self.y_test)
                            )
    def test(self):
        y_test_pred = self.classifier.predict(self.X_test)
        y_test_pred = np.argmax(y_test_pred, axis = 1)
        self.y_test = np.argmax(self.y_test, axis = 1)
        result = calculate_score(self.y_test, y_test_pred)
        print(f'Test Accuracy for MLP is {result["accuracy"][0]:.4f}')
        return result
    def inference(self):
        y_pred = self.classifier.predict(self.X_inference)
        y_pred = np.argmax(y_pred, axis=1)
        return y_pred
    
    def run(self):
        self.classifier.add(layers.Dense(self.config['hidden_size'], activation='relu', input_shape=(self.X_train.shape[1],)))
        self.classifier.add(layers.BatchNormalization())
        self.classifier.add(layers.Dropout(0.5))
        self.classifier.add(layers.Dense(self.config['hidden_size'], activation='relu'))
        self.classifier.add(layers.BatchNormalization())
        self.classifier.add(layers.Dropout(0.5))
        self.classifier.add(layers.Dense(self.config['output_size'], activation='linear'))
        self.classifier.compile(optimizer='adam',
                                loss='mean_squared_error',
                                metrics=['mean_absolute_error'])
        print("-------------------------MLP-------------------------\n", end='')
        self.train()
        self.inference()
        self.classifier.save('MLP/mlp_model.h5')
        return self.test()