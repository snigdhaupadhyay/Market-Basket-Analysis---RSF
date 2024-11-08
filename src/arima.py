import pandas as pd
from statsmodels.tsa.stattools import adfuller
from pmdarima import auto_arima
import matplotlib.pyplot as plt
import os

# Download datasets directly from Kaggle only if there are not already downloaded
# if not os.path.exists("./dataset/DataSet1.csv"):
#     os.system("kaggle datasets download -d mkechinov/ecommerce-purchase-history-from-electronics-store -p ./dataset --unzip")
# if not os.path.exists("./dataset/DataSet2.csv"):
#     os.system("kaggle datasets download -d datafiniti/electronic-products-prices -p ./dataset --unzip")
# print("Datasets downloaded and extracted to './dataset' directory")


# paths to your datasets
ds1 = "./dataset/DataSet1.csv"  
ds2 = "./dataset/DataSet2.csv"  
# read the CSV files
dataset1 = pd.read_csv(ds1)
dataset2 = pd.read_csv(ds2)

# clean up duplicates
data1_cleaned = dataset1.drop_duplicates()
data2_cleaned = dataset2.drop_duplicates()

# colums - 'event_time', 'prices.amountMin', 'prices.amountMax'
time_series_data = data2_cleaned[['dateUpdated', 'prices.amountMin', 'prices.amountMax']]

# making sure 'event_time' is in datetime format
time_series_data['dateUpdated'] = pd.to_datetime(time_series_data['dateUpdated'])

# setting event_time as the index
time_series_data.set_index('dateUpdated', inplace=True)

# calculate the average price (min and max)
time_series_data['avg_price'] = (time_series_data['prices.amountMin'] + time_series_data['prices.amountMax']) / 2

# resample to weekly for smoother trends
weekly_prices = time_series_data['avg_price'].resample('W').mean()

# forward fill any missing values
weekly_prices_filled = weekly_prices.ffill()

# ADF test to check if data is stationary
def adf_test(series):
    result = adfuller(series)
    print('ADF Statistic:', result[0])
    print('p-value:', result[1])
    if result[1] > 0.05:
        print("Series is not stationary")
    else:
        print("Series is stationary")

# run the test on weekly data
adf_test(weekly_prices_filled)

# differencing if needed
if adfuller(weekly_prices_filled)[1] > 0.05:
    stationary_data = weekly_prices_filled.diff().dropna()
else:
    stationary_data = weekly_prices_filled

# auto arima to pick best model
model = auto_arima(
    stationary_data,
    seasonal=False,
    trace=True,
    error_action='ignore',
    suppress_warnings=True,
    stepwise=True
)

# fit model
model.fit(stationary_data)

# forecast 4 weeks ahead
forecast_steps = 4
forecast, conf_int = model.predict(n_periods=forecast_steps, return_conf_int=True)

# create forecast dates
forecast_index = pd.date_range(stationary_data.index[-1], periods=forecast_steps+1, freq='W')[1:]
forecast_series = pd.Series(forecast, index=forecast_index)

# plot historical data and forecast
plt.figure(figsize=(10, 6))
plt.plot(weekly_prices_filled, label='historical avg prices')
plt.plot(forecast_series, label='forecasted prices', color='orange')
plt.fill_between(forecast_index, conf_int[:, 0], conf_int[:, 1], color='pink', alpha=0.3)
plt.title('avg price forecast for next month')
plt.xlabel('date')
plt.ylabel('avg price')
plt.legend()
plt.show()