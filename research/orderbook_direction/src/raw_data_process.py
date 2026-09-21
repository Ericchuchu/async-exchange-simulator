import os
import json
import pandas as pd
from tqdm import tqdm
import numpy as np

def read_folder(folder_path):
    file_names = os.listdir(folder_path)
    json_files = [file for file in file_names if file.endswith('.json')]

    data = []
    for file in json_files:
        file_path = os.path.join(folder_path, file)
        with open(file_path, 'r') as f:
            file_data = [json.loads(line) for line in f]
            data.extend(file_data)
    return data

def bbo_price_rearrangement(symbol):

    bbo_folder_path = f'./data/bbo/{symbol}'
    price_folder_path = f'./data/index_price/{symbol}'

    data1 = read_folder(price_folder_path)
    data2 = read_folder(bbo_folder_path)

    merged_df = pd.DataFrame(columns=['ts', 'price', 'spread', 'size_spread'])
    print(f'processing bbo and price')
    for d in tqdm(data1):
        price = d['data']['price']
        ts = d['ts'] / 1000  # Convert milliseconds to seconds

        closest_data = min(data2, key=lambda x: abs(x['ts'] / 1000 - ts))
        ask = closest_data['data']['ask']
        bid = closest_data['data']['bid']
        ask_size = closest_data['data']['askSize']
        bid_size = closest_data['data']['bidSize']
        spread = ask - bid
        size_spread = ask_size - bid_size

        new_data = pd.DataFrame({'ts': [ts], 'price': [price], 'spread': [spread], 'size_spread': [size_spread]})
        merged_df = pd.concat([merged_df, new_data], ignore_index=True)
    
    merged_df = merged_df.sort_values('ts')
    os.makedirs(f'./preprocessed_data/{symbol}', exist_ok=True)
    chunk_size = 1000000  # Adjust the chunk size as needed
    for i, chunk in enumerate(merged_df.groupby(merged_df.index // chunk_size)):
        chunk[1].to_csv(f'./preprocessed_data/{symbol}/bbo_price_{i}.csv', index=False)

def orederbook_price_rearrangement(symbol):

    orderbook_folder_path = f'./data/orderbooks/{symbol}'
    price_folder_path = f'./data/index_price/{symbol}'

    data1 = read_folder(price_folder_path)
    data2 = read_folder(orderbook_folder_path)

    merged_df = pd.DataFrame(columns=['ts', 'price', 'imblance'])
    print(f'processing orderbook and price')
    for d in tqdm(data1):
        price = d['data']['price']
        ts = d['ts'] / 1000  # Convert milliseconds to seconds
        closest_data = min(data2, key=lambda x: abs(x['ts'] / 1000 - ts))
        # best 10
        top_10_asks = [ask[1] for ask in closest_data['data']['asks'][:10]]
        top_10_bids = [bid[1] for bid in closest_data['data']['bids'][:10]]
        all_asks = [ask[1] for ask in closest_data['data']['asks']]
        all_bids = [bid[1] for bid in closest_data['data']['bids']]
        highest_order_ask = [ask[1] for ask in closest_data['data']['asks']]
        highest_order_bid = [bid[1] for bid in closest_data['data']['bids']]
        highest_order_ask_price = closest_data['data']['asks'][np.argmax(highest_order_ask)][0]
        highest_order_bid_price = closest_data['data']['bids'][np.argmax(highest_order_bid)][0]
        highest_order_ask_size = closest_data['data']['asks'][np.argmax(highest_order_ask)][1]
        highest_order_bid_size = closest_data['data']['bids'][np.argmax(highest_order_bid)][1]


        total_asks = sum(all_asks)
        total_bids = sum(all_bids)
        top_10_total_asks = sum(top_10_asks)
        top_10_total_bids = sum(top_10_bids)

        imbalance = total_asks - total_bids

        new_data = pd.DataFrame({'ts': [ts], 'price': [price], 'imblance': [imbalance], 'total_ask': [total_asks], 'total_bid': [total_bids], 'top_10_total_ask':[top_10_total_asks], 'top_10_total_bid':[top_10_total_bids],
                                 'highest_order_ask_price': [highest_order_ask_price],'highest_order_bid_price': [highest_order_bid_price], 
                                 'highest_order_ask_size': [highest_order_ask_size],'highest_order_bid_size': [highest_order_bid_size]})
        merged_df = pd.concat([merged_df, new_data], ignore_index=True)
        
    os.makedirs(f'./preprocessed_data/{symbol}', exist_ok=True)
    chunk_size = 1000000  # Adjust the chunk size as needed
    for i, chunk in enumerate(merged_df.groupby(merged_df.index // chunk_size)):
        chunk[1].to_csv(f'./preprocessed_data/{symbol}/orederbook_price_{i}.csv', index=False)

def trade_price_rearrangement(symbol):

    trade_folder_path = f'./data/trades/{symbol}'
    price_folder_path = f'./data/index_price/{symbol}'

    data1 = read_folder(price_folder_path)
    data2 = read_folder(trade_folder_path)

    merged_df = pd.DataFrame(columns=['ts', 'price', 'imbalance'])
    prev_ts = 0
    print(f'processing trade and price')
    for d in tqdm(data1):
        ts = d['ts'] / 1000  # Convert milliseconds to seconds
        price = d['data']['price']
        if prev_ts == 0:
            prev_ts = ts
            continue
        relevant_trades = [trade for trade in data2 if prev_ts <= trade['ts'] / 1000 < ts]
        total_buy = 0
        total_sell = 0
        for trade in relevant_trades:
            for unit_trade in trade['data']:
                if unit_trade['b'] == "BUY":
                    total_buy += unit_trade['a']
                if unit_trade['b'] == "SELL":
                    total_sell += unit_trade['a']
        imbalance = total_buy + total_sell
        new_data = pd.DataFrame({'ts': [ts], 'price': [price],'total_buy': [total_buy],'total_sell': [total_sell], 'imbalance': [imbalance]})
        merged_df = pd.concat([merged_df, new_data], ignore_index=True)

    os.makedirs(f'./preprocessed_data/{symbol}', exist_ok=True)
    chunk_size = 1000000  # Adjust the chunk size as needed
    for i, chunk in enumerate(merged_df.groupby(merged_df.index // chunk_size)):
        chunk[1].to_csv(f'./preprocessed_data/{symbol}/trade_price_{i}.csv', index=False)

if __name__ == "__main__":
    symbol =  "SPOT_BTC_USDT"
    # bbo_price_rearrangement(symbol)
    # trade_price_rearrangement(symbol)
    orederbook_price_rearrangement(symbol)