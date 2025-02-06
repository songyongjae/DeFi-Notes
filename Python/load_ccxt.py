import ccxt

binance_spot = ccxt.binance({'options': {'defaultType': 'spot'}})
binance_futures = ccxt.binance({'options': {'defaultType': 'future'}})

spot_markets = binance_spot.load_markets()
futures_markets = binance_futures.load_markets()

# 1) 우선 현물 시장에서 USDT를 기준통화(quote)로 하는 심볼들만 추출
spot_usdt_symbols = []
for symbol, market_info in spot_markets.items():
    if market_info.get('quote') == 'USDT' and market_info.get('active'):
        spot_usdt_symbols.append(symbol)

# 2) 선물 시장에서 USDT를 기준통화로 하는 심볼들만 추출
futures_usdt_symbols = []
for symbol, market_info in futures_markets.items():
    # 무기한 선물 마켓 중에서도 USDT가 quote인 페어만
    if market_info.get('quote') == 'USDT' and market_info.get('active'):
        futures_usdt_symbols.append(symbol)

# 3) 교집합을 구하면, 확실히 USDT 마켓에서 현물/선물 모두 존재하는 심볼만 추려짐
common_usdt_symbols = set(spot_usdt_symbols).intersection(futures_usdt_symbols)
print("공통으로 존재하는 USDT 심볼 개수:", len(common_usdt_symbols))

# 4) 각 심볼에 대해 현물, 선물 가격 수집
price_differences = []
errors = []
for symbol in common_usdt_symbols:
    try:
        spot_ticker = binance_spot.fetch_ticker(symbol)
        futures_ticker = binance_futures.fetch_ticker(symbol)
        spot_price = spot_ticker['last']
        futures_price = futures_ticker['last']
        
        if spot_price and futures_price:
            diff_pct = (futures_price - spot_price) / spot_price * 100
            
            # 추가 지표: 거래량(quoteVolume)
            # CCXT에서 fetch_ticker()가 반환하는 구조는 거래소마다 상이함
            spot_volume = spot_ticker.get('quoteVolume', None)
            futures_volume = futures_ticker.get('quoteVolume', None)
            
            price_differences.append(
                (symbol, spot_price, futures_price, diff_pct, spot_volume, futures_volume)
            )
    except Exception as e:
        # 만약 예외가 발생하면 어떤 심볼에서 오류가 나는지 확인
        errors.append((symbol, str(e)))

# 5) 결과 일부 확인
print("\n=== 현물-선물 가격 비교 Top N개 ===")
for i, (sym, sp, fp, diff, sv, fv) in enumerate(price_differences[:20], start=1):
    print(
        f"{i}. 심볼: {sym}, 현물가격: {sp}, 선물가격: {fp}, "
        f"차이(%): {diff:.2f}%, 현물 거래량: {sv}, 선물 거래량: {fv}"
    )

# 6) 예외 발생한 심볼 출력 (상위 20개만)
print("\n=== 예외 발생 심볼 Top N개 ===")
for i, (sym, err) in enumerate(errors[:20], start=1):
    print(f"{i}. 심볼: {sym}, 오류 메시지: {err}")

# 7) 10% 이상 차이 나는 심볼만 별도 추출
big_diff_symbols = [
    (sym, sp, fp, diff, sv, fv) for (sym, sp, fp, diff, sv, fv) in price_differences
    if abs(diff) >= 10
]

print("=== 10% 이상 차이 나는 심볼 리스트 ===")
for i, (sym, sp, fp, diff, sv, fv) in enumerate(big_diff_symbols, start=1):
    print(
        f"{i}. 심볼: {sym}, 현물가격: {sp}, 선물가격: {fp}, "
        f"차이(%): {diff:.2f}%, 현물 거래량: {sv}, 선물 거래량: {fv}"
    )