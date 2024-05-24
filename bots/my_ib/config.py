import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    TWS_LIVE_PORT: int = int(os.getenv("TWS_LIVE_PORT"))
    TWS_PAPER_PORT: int = int(os.getenv("TWS_PAPER_PORT"))
    IBGW_LIVE_PORT: int = int(os.getenv("IBGW_LIVE_PORT"))
    IBGW_PAPER_PORT: int = int(os.getenv("IBGW_PAPER_PORT"))


ip_address = "127.0.0.1"
