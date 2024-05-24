import pandas as pd
from lightweight_charts import Chart
from loguru import logger

if __name__ == '__main__':
    chart = Chart()
    logger.info('Chart created')
    # Columns: time | open | high | low | close | volume
    df = pd.read_csv('data/ohlcv.csv')
    logger.info('Data loaded')
    logger.info(df.head())
    chart.set(df)
    logger.info('Data set')
    chart.show(block=True)
    logger.info('Chart shown')
