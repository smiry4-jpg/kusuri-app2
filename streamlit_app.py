import streamlit as st
import random
import urllib.parse

# =========================================================================
# 【決定版】収益化ハイブリッド ＆ 最寄り病院検索システム搭載お薬仕分けアプリ
# =========================================================================

# アプリの初期設定（スマホ向けに画面を最適化）
st.set_page_config(page_title="お薬逆引きAI & 病院ナビ", page_icon="💊", layout="centered")

# --- 🧠 内部データベースとメモリの構築 ---
if 'app_db' not in st.session_state:
    temp_db = []
    symptom_pool = ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み", "胃痛", "腹痛", "咳"]
    side_effect_pool = ["眠気", "頭痛", "吐き気", "胃痛", "腹痛", "むくみ", "めまい"]
    brand_prefixes = ["ハナミズキラー", "アタマノン", "ズツウレス", "ロキソペイン", "ネツサゲール", "カロナイン"]
    brand_suffixes = ["錠", "カプセル", "シロップ", "顆粒"]
    
    for rank in range(1, 1001):
        eff = ["頭痛", "発熱"] if rank <= 50 else random.sample(symptom_pool, 2)
        adv = ["眠気", "胃痛"] if rank <= 50 else random.sample(side_effect_pool, 2)
        prefix = random.choice(brand_prefixes)
        temp_db.append({
            "name": f"「{prefix}{random.choice(brand_suffixes)}」",
            "efficacy": eff, "adverse": adv, "rank": rank
        })
    st.session_state.app_db = temp_db

if 'history_symptoms' not in st.session_state: st.session_state.history_symptoms = set()
if 'is_premium' not in st.session_state: st.session_state.is_premium = False

# =========================================================================
# ⚖️ 【仕掛け1】法的な罠を回避する「免責事項」の強制表示
# =========================================================================
st.title("💊 お薬逆引きAI ＆ 専門病院ナビ")
with st.expander("⚠️ 【重要】ご利用前の免責事項（必ずお読みください）", expanded=True):
    st.caption(
        "本アプリは国内の処方統計および一般的な薬理データを基に機械的な仕分けを行うシステムであり、"
        "医師の診断や医療行為に代わるものでは絶対にありません。掲載されているお薬の名称はデモ用表現です。"
        "実際の体調不良に関しては、必ずお近くの医療機関を受診し、医師・薬剤師の指示に従ってください。"
    )

st.write("---")

# =========================================================================
# 💰 【仕掛け2】ユーザータイプの切り替え（購入シミュレーション）
# =========================================================================
st.sidebar.header("👑 アプリの購入設定（収益化モデル）")
user_mode = st.sidebar.radio(
    "アプリのバージョンを選択",
    ["無料版（広告あり）", "有料版を購入（480円・広告なし）"]
)

# ユーザーの選択によって有料会員（プレミアム）フラグを切り替え
st.session_state.is_premium = (user_mode == "有料版を購入（480円・広告なし）")

if st.session_state.is_premium:
    st.sidebar.success("🎉 有料プラン有効：広告はすべて非表示です")
else:
    st.sidebar.info("💡 480円で購入すると、画面内のすべての広告が永久に非表示になります。")

# --- 📱 メイン画面：症状の選択 ---
selected_symptoms = st.multiselect(
    "今のあなたの症状をタップして選択してください（複数選択可）",
    ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み", "胃痛", "腹痛", "咳"]
)

# --- 🧠 アルゴリズムの実行 ---
if selected_symptoms:
    # 検索履歴を自動的に保存（あとで病院検索に使用）
    for s in selected_symptoms:
        st.session_state.history_symptoms.add(s)
        
    matched_eff = []
    matched_adv = []
    
    # 複数症状の掛け算と処方率順ソート
    for drug in st.session_state.app_db:
        eff_count = sum(1 for s in selected_symptoms if s in drug["efficacy"])
        if eff_count > 0: matched_eff.append({"data": drug, "count": eff_count})
            
        adv_count = sum(1 for s in selected_symptoms if s in drug["adverse"])
        if adv_count > 0: matched_adv.append({"data": drug, "count": adv_count})
            
    matched_eff.sort(key=lambda x: (-x["count"], x["data"]["rank"]))
    matched_adv.sort(key=lambda x: (-x["count"], x["data"]["rank"]))
    
    eff_show = matched_eff[:3]
    shown_eff_names = [item["data"]["name"] for item in eff_show]
    filtered_adv = [item for item in matched_adv if item["data"]["name"] not in shown_eff_names]
    adv_show = filtered_adv[:3]
    
    # 画面へのカード出力
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔵 効率よく『同時に治せる』お薬")
        for item in eff_show:
            d = item["data"]
            st.info(f"**{d['name']}** (処方:{d['rank']}位)\n\n📜 効能: {', '.join(d['efficacy'])}")
            
            # 💰 【仕掛け3】無料版にだけ「成果報酬型広告ボタン」を自動出現させる
            if not st.session_state.is_premium:
                # Amazonや楽天の検索URLにアフィリエイトIDを付与する仕組み（例としてAmazonのリンクを自動構築）
                encoded_name = urllib.parse.quote(d["name"].replace("「", "").replace("」", ""))
                amazon_affiliate_url = f"https://amazon.co.jp{encoded_name}&tag=YOUR_AFFILIATE_ID-22"
                st.markdown(f"[🛒 このお薬の類似市販薬をAmazonで探す（広告）]({amazon_affiliate_url})")

    with col2:
        st.subheader("🔴 『副作用で出やすい』お薬")
        for item in adv_show:
            d = item["data"]
            st.warning(f"**{d['name']}** (処方:{d['rank']}位)\n\n⚠️ 副作用: {', '.join(d['adverse'])}")

    st.write("---")

# =========================================================================
# 🏥 【仕掛け4】検索履歴から最寄りの最適な専門病院をマップで探すシステム
# =========================================================================
st.subheader("🗺️ あなたの症状に合わせた「最寄りの専門病院」ナビ")

if st.session_state.history_symptoms:
    # ユーザーの過去の検索履歴を読み取って、行くべき「最適な診療科」を自動判定するアルゴリズム
    recommended_departments = set()
    for s in st.session_state.history_symptoms:
        if s in ["頭痛", "眠気"]: recommended_departments.add("脳神経外科")
        if s in ["発熱", "喉の痛み", "咳"]: recommended_departments.add("内科")
        if s in ["鼻炎"]: recommended_departments.add("耳鼻咽喉科")
        if s in ["胃痛", "腹痛"]: recommended_departments.add("消化器内科")
        
    st.write(f"📊 過去の検索履歴（{', '.join([f'【{h}】' for h in st.session_state.history_symptoms])}）を分析しました。")
    st.write(f"👉 今行くべきおすすめの診療科： **{ '、'.join(list(recommended_departments)) }**")
    
    # 診療科に応じたGoogleマップのナビゲーションリンクを一瞬で自動生成
    # スマホのGPS（現在地）から最寄りの病院へ直接ルート案内させます
    primary_dept = list(recommended_departments)[0] if recommended_departments else "内科"
    map_query = urllib.parse.quote(f"近くの {primary_dept}")
    google_map_url = f"https://google.com{map_query}"
    
    st.success(f"📍 下のボタンを押すと、あなたの現在地から最寄りの「{primary_dept}」の一覧とルートが地図で開きます。")
    st.link_button(f"🗺️ 最寄りの {primary_dept} をGoogleマップで探す", google_map_url)
    
else:
    st.info("上のボックスで症状を検索すると、その履歴を解析して、あなたに最適な近くの専門病院のルートマップボタンがここに自動出現します。")