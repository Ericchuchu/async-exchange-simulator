import asyncio
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.console import Console
from rich import box
import pandas as pd
import numpy as np
import time
from datetime import datetime
import os
import glob
import matplotlib.pyplot as plt

class PerformanceAnalyzer:
    def __init__(self, trade_data_folder, position_data_folder, init_cash_holding, 
                 pnl_interval_minutes=1, metrics_interval_minutes=5):
        self.trade_data_folder = trade_data_folder
        self.position_data_folder = position_data_folder
        self.init_cash_holding = init_cash_holding
        self.pnl_interval = pnl_interval_minutes
        self.metrics_interval = metrics_interval_minutes
        self.pnl_time_series = []
        self.latest_metrics = {}
        self.console = Console()
        self.running = True

    def load_trade_data(self):
        try:
            trade_csv_files = glob.glob(f"{self.trade_data_folder}/*.csv")
            trade_data_list = []
            for file_path in trade_csv_files:
                trade_data = pd.read_csv(file_path)
                trade_data_list.append(trade_data)
            
            trade_data = pd.concat(trade_data_list, ignore_index=True)
            
            return trade_data
        
        except Exception as e:
            print(f"Error loading trade data: {e}")
            return None

    def load_position_data(self):
        try:
            position_csv_files = glob.glob(f"{self.position_data_folder}/*.csv")
            position_data_list = []
            for file_path in position_csv_files:
                position_data = pd.read_csv(file_path)
                position_data_list.append(position_data)
            
            position_data = pd.concat(position_data_list, ignore_index=True)
            
            return position_data
        
        except Exception as e:
            print(f"Error loading position data: {e}")
            return None

    def calculate_metrics(self):
        pnl_df = pd.DataFrame(self.pnl_time_series, columns=['timestamp', 'pnl'])
        pnl_df['timestamp'] = pd.to_datetime(pnl_df['timestamp'])
        pnl_df.set_index('timestamp', inplace=True)

        total_return = self.calculate_total_return(pnl_df['pnl'])
        sharpe_ratio = self.calculate_sharpe_ratio(pnl_df['pnl'])
        calmar_ratio = self.calculate_calmar_ratio(pnl_df['pnl'])
        max_drawdown, max_drawdown_duration = self.calculate_drawdown(pnl_df['pnl'])

        return {
            'PnL Series': pnl_df,
            'Total Return': total_return,
            'Sharpe Ratio': sharpe_ratio,
            'Calmar Ratio': calmar_ratio,
            'Max Drawdown': max_drawdown,
            'Max Drawdown Duration (Minute)': max_drawdown_duration,
        }

    def calculate_pnl(self):

        trade_data = self.load_trade_data()
        position_data = self.load_position_data()

        trade_data['timestamp'] = pd.to_datetime(trade_data['timestamp'])
        position_data['timestamp'] = pd.to_datetime(position_data['timestamp'])

        trade_data.set_index('timestamp', inplace=True)
        position_data.set_index('timestamp', inplace=True)

        pnl_data = []

        for symbol in trade_data['symbol'].unique():
            symbol_trades = trade_data[trade_data['symbol'] == symbol]
            symbol_positions = position_data[position_data['symbol'] == symbol]

            leverage = symbol_trades.iloc[-1]['leverage'] if not symbol_trades.empty else 1

            # Realized PnL
            symbol_trades['single_trade_pnl'] = (
                symbol_trades['executedPrice'] * symbol_trades['executedQuantity'] *
                np.where(symbol_trades['side'] == 'SELL', 1, -1) -
                symbol_trades['fee']
            ) * leverage

            realized_pnl = symbol_trades['single_trade_pnl'].sum() if not symbol_trades.empty else 0

            # Unrealized PnL
            if not symbol_positions.empty:
                avg_long_price = symbol_trades[(symbol_trades['side'] == 'BUY') & (symbol_trades['position_side'] == 'LONG')]['executedPrice'].mean()
                avg_short_price = symbol_trades[(symbol_trades['side'] == 'SELL') & (symbol_trades['position_side'] == 'SHORT')]['executedPrice'].mean()

                unrealized_long_pnl = (
                    (symbol_positions[symbol_positions['position_side'] == 'LONG'].iloc[-1]['mark_price']) *
                    symbol_positions[symbol_positions['position_side'] == 'LONG'].iloc[-1]['holding'] *
                    leverage
                ) if not symbol_positions[symbol_positions['position_side'] == 'LONG'].empty else 0

                unrealized_short_pnl = (
                    - (symbol_positions[symbol_positions['position_side'] == 'SHORT'].iloc[-1]['mark_price']) *
                    symbol_positions[symbol_positions['position_side'] == 'SHORT'].iloc[-1]['holding'] *
                    leverage
                ) if not symbol_positions[symbol_positions['position_side'] == 'SHORT'].empty else 0

                pnl = realized_pnl + unrealized_long_pnl + unrealized_short_pnl
            else:
                pnl = realized_pnl

            pnl_data.append(pnl)

        total_pnl = sum(pnl_data)

        return total_pnl

    def calculate_total_return(self, pnl):
        """
        total return
        
        parameters:
        pnl: pandas.Series - pnl time series data(minute-interval)
        
        return:
        float: total return
        """
        try:
            if pnl.empty:
                return 0.0
                
            total_value = pnl + self.init_cash_holding
            total_return = (total_value.iloc[-1] / self.init_cash_holding) - 1
            
            if np.isinf(total_return) or np.isnan(total_return):
                return 0.0
                
            return float(total_return)
            
        except Exception as e:
            print(f"Calculation for total return error: {str(e)}")
            return 0.0

    def calculate_sharpe_ratio(self, pnl, risk_free_rate=0.02, trading_minutes_per_year=252*390):
        """
        sharpe ratio (annual)
        
        parameters:
        pnl: pandas.Series - pnl time series data (minute-interval)
        risk_free_rate: float - 年化無風險利率(預設0.02)
        trading_minutes_per_year: int - 年交易分鐘數(預設252個交易日 * 390分鐘)
        
        return::
        float: annual sharpe ratio
        """
        try:
            if pnl.empty or len(pnl) < 2:
                return 0.0
            
            total_value = pnl + self.init_cash_holding
             
            returns = total_value.pct_change().dropna()
            returns = returns[returns != np.inf]
            returns = returns[returns != -np.inf]
            
            if len(returns) < 2:
                return 0.0
                
            annualization_factor = trading_minutes_per_year / (self.pnl_interval)
            annual_return = (1 + returns.mean()) ** annualization_factor - 1
            annual_volatility = returns.std() * np.sqrt(annualization_factor)
            
            # 處理極小波動率的情況
            if annual_volatility < 1e-10:  
                return 0.0
                
            # 計算夏普比率
            sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
            sharpe_ratio = np.clip(sharpe_ratio, -100, 100)  # 限制極端值
            
            return float(sharpe_ratio)
            
        except Exception as e:
            print(f"Calculation for sharpe ratio error: {str(e)}")
            return 0.0
       
    def calculate_calmar_ratio(self, pnl, trading_minutes_per_year=252*390):
        """
        Calmar Ratio
        
        parameters:
        pnl: pandas.Series - pnl time series data (minute-interval)
        trading_minutes_per_year: int - 年交易分鐘數(預設252個交易日 * 390分鐘)
        
        return:
        float: Calmar Ratio
        """
        try:
            if pnl.empty or len(pnl) < 2:
                return 0.0

            total_value = pnl + self.init_cash_holding
            
            returns = total_value.pct_change().dropna()
            returns = returns[returns != np.inf]
            returns = returns[returns != -np.inf]
            
            if len(returns) < 2:
                return 0.0
                
            annualization_factor = trading_minutes_per_year / self.pnl_interval
            annual_return = (1 + returns.mean()) ** annualization_factor - 1
            max_drawdown = self.calculate_drawdown(pnl)[0]
            
            if abs(max_drawdown) < 1e-10:  # 處理極小回撤情況
                return 0.0
                
            # 計算 calmar ratio
            calmar_ratio = annual_return / abs(max_drawdown)
            calmar_ratio = np.clip(calmar_ratio, -100, 100) # 限制極端值
            
            return float(calmar_ratio)
            
        except Exception as e:
            print(f"Calculation for calmar ratio error: {str(e)}")
            return 0.0
        
    def calculate_drawdown(self, pnl):
        """
        max drawdown and max duration
        
        parameter:
        pnl: pandas.Series - pnl time series data(minute-interval)
        
        return:
        tuple: (max drawdown percevtage, max drawdown duration(minute))
        """
        try:
            if pnl.empty:
                return 0.0, 0.0
                
            total_value = pnl + self.init_cash_holding
            values = total_value.values
            initial_value = values[0]
            
            cumulative_returns = values / initial_value
            peak = np.maximum.accumulate(cumulative_returns)
            
            # 計算回撤
            drawdown = cumulative_returns / peak - 1
            max_drawdown = np.min(drawdown)
            
            # 計算回撤期
            drawdown_start = np.zeros_like(drawdown, dtype=bool)
            drawdown_start[1:] = drawdown[1:] < drawdown[:-1]
            drawdown_start[0] = drawdown[0] < 0
            
            drawdown_end = np.zeros_like(drawdown, dtype=bool)
            drawdown_end[:-1] = drawdown[:-1] < drawdown[1:]
            drawdown_end[-1] = drawdown[-1] < 0

            if np.any(drawdown_start) and np.any(drawdown_end):
                start_dates = pnl.index[drawdown_start]
                end_dates = pnl.index[drawdown_end]
                
                durations = []
                for start in start_dates:
                    possible_ends = end_dates[end_dates > start]
                    if len(possible_ends) > 0:
                        duration = (possible_ends[0] - start).total_seconds() / 60
                        durations.append(duration)
                
                max_duration_minutes = max(durations) if durations else 0
            else:
                max_duration_minutes = 0
                
            return max_drawdown, max_duration_minutes
        
        except Exception as e:
            print(f"Calculation for max dradown and max drawdown duration error: {str(e)}")
            return 0.0, 0.0
        
    async def calculate_pnl_loop(self):
        while self.running:
            current_pnl = self.calculate_pnl()  
            current_timestamp = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            self.pnl_time_series.append((current_timestamp, current_pnl))
            await asyncio.sleep(self.pnl_interval * 60)

    async def calculate_metrics_loop(self):
        while self.running:
            self.latest_metrics = self.calculate_metrics()  
            await asyncio.sleep(self.metrics_interval * 60)

    def generate_display(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size = 3),
            Layout(name="main", size = 8), 
            Layout(name="pnl")
        )

        # Header
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header_table = Table(box=box.SIMPLE)
        header_table.add_column(f"Performance Monitor - Last Updated: {current_time}")
        layout["header"].update(header_table)

        # Main metrics table  
        metrics_table = Table(box=box.SIMPLE)
        metrics_table.add_column("Metric")
        metrics_table.add_column("Value")

        if self.latest_metrics:
            metrics_table.add_row("Total Return", f"{self.latest_metrics['Total Return']:.2%}")
            metrics_table.add_row("Sharpe Ratio", f"{self.latest_metrics['Sharpe Ratio']:.2f}")
            metrics_table.add_row("Calmar Ratio", f"{self.latest_metrics['Calmar Ratio']:.2f}")
            metrics_table.add_row("Max Drawdown", f"{self.latest_metrics['Max Drawdown']:.2%}")
            metrics_table.add_row("Max Drawdown Duration",
                                f"{self.latest_metrics['Max Drawdown Duration (Minute)']:.0f} min")
        layout["main"].update(metrics_table)

        # Latest PnL
        pnl_table = Table(box=box.SIMPLE)
        pnl_table.add_column("Latest PnL")
        if self.pnl_time_series:
            latest_pnl = self.pnl_time_series[-1][1]
            pnl_table.add_row(f"[{'green' if latest_pnl >= 0 else 'red'}]{latest_pnl:,.2f}")
        layout["pnl"].update(pnl_table)

        return layout
    
    def save_pnl_history(self):
        """Save PnL time series and plot"""
        # Save PnL data
        os.makedirs('result', exist_ok=True)
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S") 
        pnl_df = pd.DataFrame(self.pnl_time_series, columns=['timestamp', 'pnl'])
        pnl_df['timestamp'] = pd.to_datetime(pnl_df['timestamp'])
        pnl_df.to_csv(f'result/pnl_{current_datetime}.csv', index=False)
        
        # Plot PnL
        plt.figure(figsize=(12, 6))
        plt.plot(pnl_df['timestamp'], pnl_df['pnl'])
        plt.title('PnL Over Time')
        plt.xlabel('Time')
        plt.ylabel('PnL')
        plt.grid(True)
        plt.savefig(f'result/pnl_{current_datetime}.png')
        plt.close()

    async def run_monitor(self):
        try:
            pnl_task = asyncio.create_task(self.calculate_pnl_loop())
            metrics_task = asyncio.create_task(self.calculate_metrics_loop())

            with Live(self.generate_display(), refresh_per_second=1) as live:
                while self.running:
                    live.update(self.generate_display())
                    await asyncio.sleep(1)
        
        except asyncio.CancelledError:
            print("Monitor stopped.")

        finally:
            await self.stop()

    async def stop(self):
        self.running = False
        # Filter active, non-completed tasks
        tasks = [t for t in asyncio.all_tasks() if not t.done() and t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
            try:
                await task  # Wait for task cancellation to complete
            except asyncio.CancelledError:
                pass
        # Optionally save data or cleanup
        self.save_pnl_history()

async def main():
    analyzer = PerformanceAnalyzer(
        'trade_data',
        'position_data',
        10000,
        pnl_interval_minutes=1,
        metrics_interval_minutes=1
    )

    try:
        await analyzer.run_monitor()

    except KeyboardInterrupt:
        print("Stopping monitor...")
        await analyzer.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Exiting gracefully...")