"""GitHub Actions: 盘后总结 · 新浪K线 → 技术指标"""
import json, urllib.request, sys, os
from datetime import datetime, timezone, timedelta

STOCKS = {
    "sh601166": "兴业银行",
    "sh600406": "国电南瑞",
    "sh600900": "长江电力",
    "sh601985": "中国核电",
    "sh600089": "特变电工",
}

def sina_kline(symbol, days=120):
    url = f"https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen={days}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            text = r.read().decode("gbk", errors="replace")
            return json.loads(text)
    except: return None

def compute(klines):
    if not klines or len(klines) < 20: return {}
    c = [float(k["close"]) for k in klines]
    h = [float(k["high"]) for k in klines]
    l = [float(k["low"]) for k in klines]
    p = c[-1]
    def ma(a,w): return round(sum(a[-w:])/w,2) if len(a)>=w else None
    m5,m10,m20,m60 = ma(c,5),ma(c,10),ma(c,20),ma(c,60)
    bb_u = bb_l = None
    if m20:
        v = sum((x-m20)**2 for x in c[-20:])/20
        s = v**0.5; bb_u=round(m20+2*s,2); bb_l=round(m20-2*s,2)
    rsi = None
    if len(c)>=15:
        g=l_=0.0
        for i in range(-14,0):
            d=c[i]-c[i-1]
            if d>=0: g+=d
            else: l_-=d
        rsi = round(100-100/(1+g/14/(l_/14+0.001)),1) if l_>0 else 100
    h60 = round(max(h[-60:]),2); l60 = round(min(l[-60:]),2) if len(l)>=60 else round(min(l),2)
    h20 = round(max(h[-20:]),2) if len(h)>=20 else h60
    l20 = round(min(l[-20:]),2) if len(l)>=20 else l60
    supp = sorted(set([round(v,2) for v in [bb_l,m60,l60] if v and v < p]))[:3]
    res = sorted(set([round(v,2) for v in [bb_u,h60] if v and v > p]))[:3]
    buy_ok = m10 or round(p*0.98,2)
    buy_good = round((supp[-1]+buy_ok)/2,2) if supp else round(p*0.95,2)
    buy_best = supp[0] if supp else round(p*0.93,2)
    sell = res[-1] if res else round(p*1.08,2)
    sig_t = "🔴 支撑位 无脑加仓" if p<=buy_best else "🟡 优秀买点" if p<=buy_good else "🟢 合理买点" if p<=buy_ok else "📌 持有" if p<sell else "📤 止盈"
    sig_c = "buy" if p<=buy_ok else "sell" if p>=sell else "hold"
    return {"price":p,"ma5":m5,"ma10":m10,"ma20":m20,"ma60":m60,
            "bb_upper":bb_u,"bb_lower":bb_l,"rsi14":rsi,
            "h60":h60,"l60":l60,"h20":h20,"l20":l20,
            "supports":supp,"resists":res,
            "buy_ok":buy_ok,"buy_good":buy_good,"buy_best":buy_best,"sell":sell,
            "signal_text":sig_t,"signal_type":sig_c}

def main():
    r = {"generated_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),"stocks":{}}
    for sym,name in STOCKS.items():
        k = sina_kline(sym)
        if not k: r["stocks"][sym]={"name":name,"error":"数据获取失败"}; continue
        r["stocks"][sym] = {"name":name, **compute(k)}
    os.makedirs("data", exist_ok=True)
    with open("data/summary.json","w") as f:
        json.dump(r,f,ensure_ascii=False,indent=2)
    print(f"✅ {len(r['stocks'])}支股票")
    for s,d in r["stocks"].items():
        if "error" in d: print(f"  ❌ {d['name']}")
        else: print(f"  {d['name']}: ¥{d['price']} RSI{d['rsi14']} 支撑{d['supports']} 阻力{d['resists']} {d['signal_text']}")

if __name__=="__main__": main()
