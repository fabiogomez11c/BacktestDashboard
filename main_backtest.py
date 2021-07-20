from src.backtester import Backtester

if __name__ == '__main__':
    symbols = ['AAPL']
    from_to = ['2020-01-01', '2021-06-30']

    engine = Backtester(symbols=symbols, from_to=from_to)
    engine.run_backtest()

    print('Done')