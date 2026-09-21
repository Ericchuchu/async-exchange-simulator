import pandas as pd
import numpy as np

def preprocess(symbol, type, time_interval=1, training_process = True):
    bbo_data = pd.read_csv(f'./preprocessed_data/{symbol}/bbo_price_0.csv')
    orderbook_data = pd.read_csv(f'./preprocessed_data/{symbol}/orederbook_price_0.csv') 
    trade_data = pd.read_csv(f'./preprocessed_data/{symbol}/trade_price_0.csv')
    
    # Convert timestamp to datetime
    orderbook_data['timestamp'] = pd.to_datetime(orderbook_data['ts'], unit='s')
    trade_data['timestamp'] = pd.to_datetime(trade_data['ts'], unit='s')
    bbo_data['timestamp'] = pd.to_datetime(bbo_data['ts'], unit='s')

    # Strong factor : Highest order price flow
    highest_order_ask_price_change = orderbook_data['highest_order_ask_price'].pct_change().shift(-1)
    highest_order_bid_price_change = orderbook_data['highest_order_bid_price'].pct_change().shift(-1)
    orderbook_data['highest_order_price_flow'] = highest_order_ask_price_change + highest_order_bid_price_change

    # Calculate total buy volume and total sell volume for each time interval 
    trade_data['total_buy_volume'] = trade_data['total_buy'].rolling(window=time_interval).sum()
    trade_data['total_sell_volume'] = trade_data['total_sell'].rolling(window=time_interval).sum()

    # Merge data
    # print(len(orderbook_data))
    merged_data_1 = pd.merge_asof(orderbook_data, trade_data[['timestamp', 'total_buy_volume', 'total_sell_volume']], on='timestamp', direction='nearest') 
    # print(len(merged_data_1))
    merged_data = pd.merge_asof(merged_data_1, bbo_data[['timestamp', 'size_spread']], on='timestamp', direction='nearest')
    # print(len(merged_data))

    # Calculate buy order flow, sell order flow, and net order flow changes
    merged_data['buy_order_flow_change'] = merged_data['total_ask'].diff(time_interval)
    merged_data['sell_order_flow_change'] = merged_data['total_bid'].diff(time_interval)
    merged_data['net_flow_change'] = merged_data['buy_order_flow_change'] - merged_data['sell_order_flow_change']

    # Adjust buy order flow and sell order flow by dividing by total buy volume and total sell volume
    merged_data['adjusted_buy_order_flow_change'] = merged_data['buy_order_flow_change'] / merged_data['total_buy_volume'] 
    merged_data['adjusted_sell_order_flow_change'] = merged_data['sell_order_flow_change'] / merged_data['total_sell_volume']
    merged_data['adjusted_net_flow_change'] = merged_data['adjusted_buy_order_flow_change'] - merged_data['adjusted_sell_order_flow_change']

    # Prediction label
    merged_data['next_price_change'] = merged_data['price'].pct_change().shift(-1)
    merged_data['next_price_direction'] = merged_data['next_price_change'].apply(lambda x: 2 if x > 0 else 1 if x < 0 else 0)

    # Remove rows with NaN or inf values
    merged_data = merged_data.replace([np.inf, -np.inf], np.nan).dropna()

    # Only consideer facto == 0 in training process
    if training_process:
        merged_data = merged_data[merged_data['highest_order_price_flow'] == 0]

    # Grouped label
    grouped_data = merged_data.groupby('next_price_direction')

    train_data, valid_data, test_data = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    for _, group in grouped_data:
        total_samples = len(group)
        train_end = int(0.7 * total_samples) 
        valid_end = int(0.85 * total_samples)

        if type == 'train':
            train_data = pd.concat([train_data, group[:train_end]])
        elif type == 'valid':
            valid_data = pd.concat([valid_data, group[train_end:valid_end]]) 
        elif type == 'test':
            test_data = pd.concat([test_data, group[valid_end:]])

    if type == 'train':
        merged_data = train_data 
    elif type == 'valid':
        merged_data = valid_data
    elif type == 'test': 
        merged_data = test_data

    num_variables = 6
    input_data = np.zeros((len(merged_data), num_variables))
    input_data[:, 0] = merged_data['imblance'].values
    input_data[:, 1] = merged_data['size_spread'].values 
    input_data[:, 2:] = merged_data[['buy_order_flow_change','sell_order_flow_change',
                                     'adjusted_buy_order_flow_change', 'adjusted_sell_order_flow_change']].values
    label = merged_data['next_price_direction'].values
    factor = merged_data['highest_order_price_flow'].values

    return input_data, label, factor

if __name__ == "__main__":
    input_data, label, factor = preprocess("SPOT_BTC_USDT", 'valid')
    label = np.array(label)
    print(len(label[(label == 0)]))
    print(len(label[(label == 1)]))
        