# Simple MACD Strategy
import shift
from jinja2 import Environment
import time
import pandas as pd

# Connect to shift
trader = shift.Trader("kachow")
trader.connect("initiator.cfg", "tTdSGwv9")

# Time Stuffs
env = Environment(extensions=['jinja2_time.TimeExtension'])
template = env.from_string("{% now 'local', '%H%M' %}")
currTime = template.render()


# Load past ~30 bars into array
def currPrice(ticker):
    return trader.get_last_price(ticker)


def loadPrices(ticker, prevPrices):
    while len(prevPrices) < 30:
        price = currPrice(ticker)
        prevPrices.append(price)
        print(str(len(prevPrices)) + "/30 bars loaded @ " + str(currPrice(ticker)))
        time.sleep(60)
    return prevPrices


# Update prevPrices
def updatePrices(prevPrices):
    updatedP = []

    updatedP[0] = currPrice

    for i in range(1, 30):
        updatedP[i] = prevPrices[i - 1]
    prevPrices = updatedP.copy()
    return prevPrices


'''
def makeSma(prevPrices, length):
    i = 0
    sma = []

    while i < len(prevPrices) - length + 1:
        window = prevPrices[i: i + length]
        windowAverage = round(sum(window) / length, 2)
        sma.append(windowAverage)
        i += 1

    return sma



def makeEma(hist, length):
    ema = []

    # get first sma to build ema off of
    sma = (hist[len(hist) - 1] + hist[len(hist) - 2] + hist[len(hist) - 3]) / 3
    multiplier = 2 / float(1 + length)
    ema.append(sma)

    #EMA(current) = (price(current) - EMA(prev) ) x Multiplier) + EMA(prev)
    #ema.append(((hist[0] - sma) * multiplier) + ema[i])

    for i in hist[::len(hist) - length]:
        temp = (hist[0] * multiplier) + (ema[i] * (1 - multiplier))
        i += 1
        ema.append(temp)

    return ema
'''


def macdStrategy(chart, ticker):
    # Order parameters
    priceAb = currPrice(ticker) + 0.01
    priceBel = currPrice(ticker) - 0.01
    orderNum = ''

    # Types of Orders
    aLimitBuy = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, 1, priceAb, orderNum)
    bLimitBuy = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, 1, priceBel, orderNum)

    aLimitSell = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, 1, priceAb, orderNum)
    bLimitSell = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, 1, priceBel, orderNum)
    # Buy if slope of histogram from - to +
    if chart.loc[0].at["Histogram"] > chart.loc[1].at["Histogram"] \
            and chart.loc[1].at["Histogram"] < chart.loc[2].at["Histogram"]:
        trader.submit_order(aLimitBuy)
        trader.submit_order(bLimitBuy)
    # Sell if slope of histogram from + to -
    elif chart.loc[0].at["Histogram"] < chart.loc[1].at["Histogram"] \
            and chart.loc[1].at["Histogram"] > chart.loc[2].at["Histogram"]:
        trader.submit_order(aLimitSell)
        trader.submit_order(bLimitSell)

    # Close unexecuted bracketed order
    while trader.get_waiting_list_size() == 2:
        if trader.get_waiting_list_size() < 2:
            trader.cancel_all_pending_orders()
        time.sleep(1)


'''TODO: Implement the TR indicator'''


def run(ticker, prevPrices):
    # Load first 30 prices
    prevPrices = loadPrices(ticker, prevPrices)

    while 801 < int(currTime) < 2355:
        # Update prices array
        updatePrices(prevPrices)

        # Create dataframe that will hold all the data from the quote
        chart = pd.DataFrame({'Close': prevPrices})

        # Calculate everything for the MACD indicator
        slowEma = chart['Close'].ewm(span=26, adjust=False, min_periods=26).mean()
        fastEma = chart['Close'].ewm(span=12, adjust=False, min_periods=12).mean()
        macd = fastEma - slowEma
        chart['MACD'] = chart.index.map(macd)

        # Calculate everything for the signal and the histogram
        signalEma = chart['MACD'].ewm(span=9, adjust=False, min_periods=9).mean()
        chart['Signal'] = chart.index.map(signalEma)
        histogram = chart['MACD'] - chart['Signal']
        chart['Histogram'] = chart.index.map(histogram)

        print(chart)

        macdStrategy(chart, ticker)

        time.sleep(60)


def main():
    ticker = "AAPL"
    prevPrices = []

    # Allow for correct instantiation
    time.sleep(1)
    print("Current time: " + str(currTime))

    run(ticker, prevPrices)

    trader.cancel_all_pending_orders()
    trader.disconnect()


if __name__ == "__main__":
    main()
