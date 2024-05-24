// import .env file
import dotenv from 'dotenv';

dotenv.config();

class PlatformPort {
    static TWS_LIVE_PORT = parseInt(process.env.TWS_LIVE_PORT);
    static TWS_PAPER_PORT = parseInt(process.env.TWS_PAPER_PORT);
    static IBGW_LIVE_PORT = parseInt(process.env.IBGW_LIVE_PORT);
    static IBGW_PAPER_PORT = parseInt(process.env.IBGW_PAPER_PORT);
}

const platform = 'TWS';
const paperTrading = true;
export default {
    host: 'localhost',
    clientId: parseInt(process.env.CLIENT_ID) || 999,
    port: (() => {
        if (platform === 'TWS') {
            return paperTrading ? PlatformPort.TWS_PAPER_PORT : PlatformPort.TWS_LIVE_PORT;
        }
        return paperTrading ? PlatformPort.IBGW_PAPER_PORT : PlatformPort.IBGW_LIVE_PORT;
    })(),
}

