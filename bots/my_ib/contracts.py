from ibapi.contract import Contract


class MyContracts:

    @staticmethod
    def USStock(symbol="SPY"):
        # ! [stkcontract]
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "ARCA"
        # ! [stkcontract]
        return contract

    @staticmethod
    def EthUsdCrypto():
        contract = Contract()
        contract.symbol = "ETH"
        contract.secType = "CRYPTO"
        contract.exchange = "PAXOS"
        contract.currency = "USD"
        return contract

    @staticmethod
    def USStockWithPrimaryExch(symbol="SPY", primary_exchange="ARCA"):
        # ! [stkcontractwithprimary]
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        contract.primaryExchange = primary_exchange
        # ! [stkcontractwithprimary]
        return contract

    @staticmethod
    def USStockAtSmart(symbol="IBM"):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        return contract

    @staticmethod
    def etf(symbol="QQQ"):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        return contract

    @staticmethod
    def EurGbpFx():
        # ! [cashcontract]
        contract = Contract()
        contract.symbol = "EUR"
        contract.secType = "CASH"
        contract.currency = "GBP"
        contract.exchange = "IDEALPRO"
        # ! [cashcontract]
        return contract