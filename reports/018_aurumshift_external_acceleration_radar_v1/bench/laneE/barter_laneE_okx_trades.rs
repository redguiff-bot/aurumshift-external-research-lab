// Lane E : smoke barter-data sur OKX (trades BTC-USDT spot + perp), affiche time_exchange / time_received.
use barter_data::{exchange::okx::Okx, streams::{Streams, reconnect::stream::ReconnectingStream}, subscription::trade::PublicTrades};
use barter_instrument::instrument::market_data::kind::MarketDataInstrumentKind;
use futures::StreamExt;
#[tokio::main]
async fn main() {
    let streams = Streams::<PublicTrades>::builder()
        .subscribe([(Okx, "btc", "usdt", MarketDataInstrumentKind::Spot, PublicTrades),
                    (Okx, "btc", "usdt", MarketDataInstrumentKind::Perpetual, PublicTrades)])
        .init().await.unwrap();
    let mut joined = streams.select_all().with_error_handler(|e| eprintln!("err {e:?}"));
    let t0 = std::time::Instant::now();
    let (mut n, mut lags) = (0u64, Vec::new());
    while let Ok(Some(ev)) = tokio::time::timeout(std::time::Duration::from_secs(5), joined.next()).await {
        if let barter_data::streams::reconnect::Event::Item(e) = ev {
            n += 1;
            lags.push((e.time_received - e.time_exchange).num_milliseconds());
            if n == 1 { println!("first: {:?}", e); }
        }
        if t0.elapsed().as_secs() >= 20 { break; }
    }
    lags.sort();
    println!("{{\"events\":{},\"lag_ms_p50\":{},\"lag_ms_min\":{}}}", n, lags.get(lags.len()/2).unwrap_or(&-1), lags.first().unwrap_or(&-1));
}
