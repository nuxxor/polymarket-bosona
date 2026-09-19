from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Polymarket endpoints
    gamma_api_url: str = "https://gamma-api.polymarket.com"
    clob_api_url: str = "https://clob.polymarket.com"
    clob_ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
    rtds_ws_url: str = "wss://ws-live-data.polymarket.com"
    binance_ws_url: str = ""
    binance_ws_base_url: str = "wss://stream.binance.com:9443"
    binance_symbol: str = "btcusdt"
    binance_kline_interval: str = "1m"
    binance_spot_depth_levels: int = 10
    binance_spot_depth_update_ms: int = 1000
    binance_usdm_rest_base_url: str = "https://fapi.binance.com"
    binance_usdm_ws_base_url: str = "wss://fstream.binance.com"
    binance_usdm_ws_url: str = ""
    binance_usdm_symbol: str = "BTCUSDT"
    binance_usdm_depth_levels: int = 10
    binance_usdm_depth_update_ms: int = 500
    binance_usdm_kline_interval: str = "1m"
    binance_futures_oi_poll_interval_s: float = 15.0
    binance_futures_regime_poll_interval_s: float = 60.0
    binance_futures_regime_period: str = "5m"
    binance_futures_mark_poll_interval_s: float = 2.0
    binance_futures_agg_trade_poll_interval_s: float = 1.0
    binance_futures_kline_poll_interval_s: float = 10.0
    deribit_api_base_url: str = "https://www.deribit.com/api/v2"
    deribit_index_poll_interval_s: float = 60.0
    deribit_index_names: str = ""

    # Collector tuning
    vwap_target_usd: float = 100.0
    snapshot_interval_s: float = 1.0
    market_poll_interval_s: float = 60.0
    book_refresh_interval_s: float = 12.0
    ws_keepalive_s: float = 120.0
    max_tokens_per_ws: int = 400
    subscribe_window_s: int = 7200  # Only subscribe to markets expiring within this window
    clob_inactivity_timeout_s: float = 300.0
    rtds_inactivity_timeout_s: float = 30.0
    btc_price_max_age_ms: int = 15000
    binance_micro_max_age_ms: int = 5000

    @property
    def binance_ws_streams(self) -> str:
        symbol = self.binance_symbol.strip().lower()
        interval = self.binance_kline_interval.strip().lower()
        streams = [
            f"{symbol}@kline_{interval}",
            f"{symbol}@aggTrade",
            f"{symbol}@bookTicker",
            self.binance_spot_depth_stream,
        ]
        return "/".join(streams)

    @property
    def binance_spot_depth_stream(self) -> str:
        symbol = self.binance_symbol.strip().lower()
        levels = max(5, int(self.binance_spot_depth_levels))
        update_ms = int(self.binance_spot_depth_update_ms)
        suffix = "@100ms" if update_ms == 100 else ""
        return f"{symbol}@depth{levels}{suffix}"

    @property
    def effective_binance_ws_url(self) -> str:
        url = self.binance_ws_url.strip()
        if not url:
            return f"{self.binance_ws_base_url}/stream?streams={self.binance_ws_streams}"
        if "{streams}" in url:
            return url.format(streams=self.binance_ws_streams)
        if "/stream?" in url or "@aggTrade" in url or "@bookTicker" in url:
            return url
        if "@kline_" in url:
            return f"{self.binance_ws_base_url}/stream?streams={self.binance_ws_streams}"
        return url

    @property
    def binance_usdm_public_streams(self) -> str:
        symbol = self.binance_usdm_symbol.strip().lower()
        levels = max(5, int(self.binance_usdm_depth_levels))
        update_ms = int(self.binance_usdm_depth_update_ms)
        suffix = f"@{update_ms}ms" if update_ms > 0 else ""
        interval = self.binance_usdm_kline_interval.strip().lower()
        return "/".join(
            [
                f"{symbol}@depth{levels}{suffix}",
                f"{symbol}@markPrice@1s",
                f"{symbol}@aggTrade",
                f"{symbol}@kline_{interval}",
                f"{symbol}@forceOrder",
            ]
        )

    @property
    def effective_binance_usdm_depth_ws_url(self) -> str:
        url = self.binance_usdm_ws_url.strip()
        if not url:
            return f"{self.binance_usdm_ws_base_url}/stream?streams={self.binance_usdm_public_streams}"
        if "{streams}" in url:
            return url.format(streams=self.binance_usdm_public_streams)
        if "/stream?" in url or "@depth" in url:
            return url
        return f"{self.binance_usdm_ws_base_url}/stream?streams={self.binance_usdm_public_streams}"

    @property
    def deribit_index_name_list(self) -> list[str]:
        return [
            item.strip().lower()
            for item in self.deribit_index_names.split(",")
            if item.strip()
        ]

    # Storage
    data_dir: str = "./data"

    @property
    def db_path(self) -> str:
        return f"{self.data_dir}/db/polymarket.db"

    @property
    def raw_dir(self) -> str:
        return f"{self.data_dir}/raw"


settings = Settings()
