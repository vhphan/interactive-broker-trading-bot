import numpy as np


class Strategy:
    def __init__(self, trader):
        self.trader = trader

    def run(self):
        pass


class SimpleStrategy(Strategy):
    def __init__(self, trader):
        super().__init__(trader)
        self.short_window = 10
        self.long_window = 30

    def calculate_moving_average(self, data, window):
        return data.rolling(window=window).mean()

    def run(self):
        # Get the historical data from the trader
        data = self.trader.hist_df['close'].iloc[-(2 * self.long_window):-1]

        # Calculate short and long moving averages
        short_mavg = self.calculate_moving_average(data, self.short_window)
        long_mavg = self.calculate_moving_average(data, self.long_window)

        # Create signals based on the crossover
        current_delta = short_mavg.iloc[-1] - long_mavg.iloc[-1]
        previous_delta = short_mavg.iloc[-2] - long_mavg.iloc[-2]
        is_crossover_up = current_delta > 0 and previous_delta < 0
        is_crossover_down = current_delta < 0 and previous_delta > 0
        last_signal = np.where(is_crossover_up, 1.0, np.where(is_crossover_down, -1.0, 0))

        # Check the latest bar and generate a signal if needed
        if last_signal == 1.0:
            self.trader.buy()
        elif last_signal == -1.0:
            self.trader.sell()
        else:
            self.trader.do_nothing()