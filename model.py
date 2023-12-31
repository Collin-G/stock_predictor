
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd 
from pandas_datareader import data as pdr
import datetime as dt
from datetime import datetime, timedelta

from sklearn.preprocessing import MinMaxScaler

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout
import yfinance as yfin

class Model():

    def __init__(self, company, predict_length):
        self.raw_data = None
        self.company = company
        self.scaler, self.data = self.build_data()
        self.predict_length = predict_length
        self.model = self.build_model()
        self.predicted_prices, self.labels = self.guess_prices()
        self.tmr_price = self.test_for_tomorrow()
        

    
    def build_data(self):
        today = datetime.now()

        start = dt.datetime(2012,1,1)
        end = today - timedelta(days=80)
        yfin.pdr_override()
        data = pdr.get_data_yahoo(self.company, start, end)
        self.raw_data = data
        scaler = MinMaxScaler(feature_range=(0,1))
        scaled_data = scaler.fit_transform(data["Close"].values.reshape(-1,1))
        return scaler,scaled_data
    
    def x_and_y_train(self, predict_length,data):

        x_train = []
        y_train = []

        for i in range(60, len(data)):
            x_train.append(data[i-predict_length:i,0])
            y_train.append(data[i,0])

        x_train, y_train = np.array(x_train), np.array(y_train)
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1],1))
        return x_train, y_train

    def build_model(self):

        x_train, y_train = self.x_and_y_train(self.predict_length, self.data)
        model = Sequential()
        model.add(LSTM(units=50, return_sequences = True, input_shape=(x_train.shape[1],1)))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50, return_sequences = False))
        model.add(Dense(units=25))
        model.add(Dropout(0.2))
        model.add(Dense(units=1))

        model.compile(optimizer="adam", loss = "mean_squared_error")
        model.fit(x_train, y_train, epochs=25, batch_size=32)

        return model
    
    def test_for_tomorrow(self):
        today = datetime.now()
        start = dt.datetime(2012,1,1)
        yfin.pdr_override()
        data = pdr.get_data_yahoo(self.company, start, today)
        df = data.filter(["Close"])

        last_x_days = df[-self.predict_length:].values
        last_x_days_scaled = self.scaler.transform(last_x_days)
        x_test = []

        x_test.append(last_x_days_scaled)
        x_test = np.array(x_test)

        x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1],1))
        predicted_price = self.model.predict(x_test)

        predicted_price = self.scaler.inverse_transform(predicted_price)
        return predicted_price

    def guess_prices(self):
        x_test = []
        y_test = []
        for x in range(60, len(self.data)):
            x_test.append(self.data[x-self.predict_length:x,0])
            y_test.append(self.data[x,0])

        x_test = np.array(x_test)
        x_test = np.reshape(x_test, (x_test.shape[0],x_test.shape[1],1))

        predicted_prices = self.model.predict(x_test)
        predicted_prices = self.scaler.inverse_transform(predicted_prices)
        return predicted_prices, y_test