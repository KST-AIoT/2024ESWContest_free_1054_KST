import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras

def sep_data(x_data):
    #data = (NoOfData, DataLength, NoOfFeature) = (26, 27, 2)
    train_data = x_data[: 24, :, :]
    valid_data = x_data[24: , :, :]
    return train_data, valid_data
    
def CNN(input_data, learning_rate):
    keras.backend.clear_session()
    tf.keras.utils.set_random_seed(777)

    model = keras.Sequential()
    model.add(keras.layers.InputLayer(shape=(input_data.shape[1],input_data.shape[2])))                                         # Input layer
    model.add(keras.layers.Conv1D(filters = 4, kernel_size= 4, strides= 2, padding='same', activation=keras.activations.relu))  # Convolution layer 1
    model.add(keras.layers.Conv1D(filters = 4, kernel_size= 4, strides= 2, padding='same', activation=keras.activations.relu))  # Convolution layer 2
    
    model.add(keras.layers.MaxPooling1D(pool_size = 3, strides= 3))                                                             # Max Pooling Layer
    
    model.add(keras.layers.Conv1D(filters = 4, kernel_size= 4, strides= 2, padding='same', activation=keras.activations.relu))  # Convolution layer 3
    model.add(keras.layers.Conv1D(filters = 4, kernel_size= 4, strides= 2, padding='same', activation=keras.activations.relu))  # Convolution layer 4
    
    # Convolution/Pooling layer to Output layer
    model.add(keras.layers.GlobalAveragePooling1D())                                                                            # Global Average Pooling (Simple Structure)

    model.add(keras.layers.Dense(units = 32, activation=keras.activations.relu))                                                # Hidden Layer1
    model.add(keras.layers.Dense(units = 32, activation=keras.activations.relu))                                                # Hidden Layer2
    
    model.add(keras.layers.Dense(units = 2, activation=keras.activations.softmax))                                              # Output Layer

    model.compile(optimizer= keras.optimizers.Adam(learning_rate = learning_rate), # 수정 금지
                  loss=keras.losses.CategoricalCrossentropy(),                    # 수정 금지
                  metrics=['accuracy'])                                           # 수정 금지
    return model
def train_cnn(train_data, train_label, epochs, learning_rate):
    CNN_model = CNN(train_data, learning_rate)
    CNN_model.summary()

    hist = CNN_model.fit(train_data, train_label, epochs = epochs, verbose = 1)
    # 모델 평가
    Loss, Accuracy = CNN_model.evaluate(train_data, train_label, verbose=0)
    print('Final Loss and Accuracy: {:.4f}, {:.2f}%'.format(Loss, Accuracy*100))