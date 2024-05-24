import {BarSizeSetting, EventName, IBApi, SecType, WhatToShow} from "@stoqey/ib";
import config from "./config.js";
import {fileURLToPath} from 'url';
import {dirname} from 'path';

// create IBApi object

export const ib = new IBApi({
    clientId: config.clientId,
    // host: '127.0.0.1',
    host: config.host,
    port: config.port,
});

export const init = async () => {
    ib.on(EventName.error, (err) => {
        console.error(err);
        ib.disconnect();
    });
    ib.on(EventName.historicalData, (reqId, time, open, high, low, close, volume, count, WAP, hasGaps) => {
            console.log(reqId, time, open, high, low, close, volume, count, WAP, hasGaps);
        }
    );
    ib.on(EventName.historicalDataUpdate, (reqId, time, open, high, low, close, volume, count, WAP) => {
        console.log(reqId, time, open, high, low, close, volume, count, WAP);
    })

    console.log('connecting...');
    await ib.connect(config.clientId);
    let intervalId = setInterval(() => {
        console.log('checking connection');
        // break out of the loop if is connected
        if (ib.isConnected) {
            console.log('connected');
            const contract = {
                symbol: "SPY",
                exchange: "SMART",
                primaryExchange: "ARCA",
                currency: "USD",
                secType: SecType.STK,
            };

            try {
                ib.reqHistoricalData(1, contract, "20240519 23:59:59 US/Eastern", "10 D", BarSizeSetting.DAYS_ONE, WhatToShow.TRADES, 1, 1);
            } catch (e) {
                console.error(e);
            } finally {
            }
            clearInterval(intervalId);
        } else {
            console.log('not connected');
        }
    }, 1000);

    // setTimeout(() => {
    //     console.log('disconnecting...');
    //     ib.disconnect();
    // }, 15000);
    //
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

if (process.argv[1] === __filename) {
    init().catch((err) => {
        console.error(err);
    });
}