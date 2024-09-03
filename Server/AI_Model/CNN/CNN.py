import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt

class CNN:
    def __init__(self, config, X_train, X_valid, y_train, y_valid):
        self.config = config
        self.X_train = X_train
        self.X_valid = X_valid
        self.y_train = y_train
        self.y_valid = y_valid
    def build_model(self):
        keras.backend.clear_session()
        tf.keras.utils.set_random_seed(777)

        model = keras.Sequential()
        model.add(keras.layers.InputLayer(shape=(self.X_train.shape[1], self.X_train.shape[2])))                                         # Input layer
        model.add(keras.layers.Conv1D(filters=8, kernel_size=3, strides=1, padding='same', activation=keras.activations.relu))  # Convolution layer 1
        model.add(keras.layers.Conv1D(filters=8, kernel_size=3, strides=1, padding='same', activation=keras.activations.relu))  # Convolution layer 2
        
        model.add(keras.layers.MaxPooling1D(pool_size=2, strides=2))                                                             # Max Pooling Layer
        
        model.add(keras.layers.Conv1D(filters=16, kernel_size=3, strides=1, padding='same', activation=keras.activations.relu))  # Convolution layer 3
        model.add(keras.layers.Conv1D(filters=16, kernel_size=3, strides=1, padding='same', activation=keras.activations.relu))  # Convolution layer 4
        
        # Convolution/Pooling layer to Output layer
        model.add(keras.layers.GlobalAveragePooling1D())                                                                            # Global Average Pooling (Simple Structure)

        model.add(keras.layers.Dense(units=32, activation=keras.activations.relu))                                                  # Hidden Layer 1
        model.add(keras.layers.Dense(units=32, activation=keras.activations.relu))                                                  # Hidden Layer 2
        
        model.add(keras.layers.Dense(units=3))                                                                                      # Output Layer with 3 units (for 3 continuous values)

        model.compile(optimizer=keras.optimizers.Adam(learning_rate=self.config['learning_rate']),
                    loss=keras.losses.MeanSquaredError(),                     # Use MSE for regression
                    metrics=['mae'])                                          # Mean Absolute Error for evaluation
        return model

def run(self):
    model = self.build_model()
    model.summary()

    hist = model.fit(self.X_train, self.y_train, 
                         validation_data=(self.X_valid, self.y_valid),
                         epochs=self.config['epochs'], verbose=1)
    # 모델 평가
    Loss, MAE = model.evaluate(self.X_valid, self.y_valid, verbose=0)
    print('Final Loss and MAE: {:.4f}, {:.2f}'.format(Loss, MAE))
    # 학습 과정에서의 손실 값 그래프
    plt.plot(hist.history['loss'], label='Training Loss')
    plt.plot(hist.history['val_loss'], label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()

    # 학습 과정에서의 MAE 그래프
    plt.plot(hist.history['mae'], label='Training MAE')
    plt.plot(hist.history['val_mae'], label='Validation MAE')
    plt.xlabel('Epochs')
    plt.ylabel('MAE')
    plt.legend()
    plt.show()
