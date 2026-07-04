import streamlit as st
import random
import urllib.parse

# =========================================================================
# 【UIバグ完全克服版】キーボード立ち上がりを防ぐチェックボックス選択型アプリ
# =========================================================================

st.set_page_config(page_title="お薬逆引きAI & 病院ナビ", page_icon="💊", layout="centered")

# --- 🧠 内部データベースの構築（2,000件） ---
if 'app_db' not in st.session_state:
    temp_db = []
    symptom_pool = ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み", "胃痛", "腹痛", "咳", "腰痛", "関節痛", "歯痛", "高血圧"]
    side_effect_pool = ["眠気", "頭痛", "吐き気", "胃痛", "腹痛", "むくみ", "めまい"]
    
    friendly_categories = [
        {"prefix": "ロキソペイン錠 60mg", "desc": "【標準鎮痛消炎】大人の激しい頭痛や発熱、関節の炎症を素早く鎮める消炎鎮痛薬", "eff": ["頭痛", "発熱", "歯痛", "関節痛"], "adv": ["胃痛", "腹痛"], "target": "adult_only", "type": "一般薬"},
        {"prefix": "カロナイン錠 500mg", "desc": "【標準解熱鎮痛】中枢神経に働きかけ、胃への負担が極めて少ないマイルドな大人向け解熱鎮痛薬", "eff": ["頭痛", "発熱", "喉の痛み"], "adv": ["眠気", "食欲不振"], "target": "all", "type": "一般薬"},
        {"prefix": "カロナイン細粒 200mg", "desc": "【小児用解熱鎮痛】体重に合わせて細かく量を調節できる、子ども向けの安全性の高い解熱鎮痛薬", "eff": ["頭痛", "発熱", "喉の痛み"], "adv": ["眠気"], "target": "all", "type": "一般薬"},
        {"prefix": "ズツウマプロ点鼻液 20mg", "desc": "【偏頭痛・トリプタン系】拡張した脳の血管をピンポイントで収縮させ、激しい偏頭痛の発作を直接止める特殊な点鼻薬", "eff": ["頭痛"], "adv": ["めまい", "喉の不快感", "動悸"], "target": "adult_only", "type": "専門薬（脳神経外科）"},
        {"prefix": "ガルペネズ皮下注 120mg", "desc": "【偏頭痛・抗体医薬品】月1回の注射で、偏頭痛を引き起こす脳内の原因物質（CGRP）を根元から長期間ブロックする最先端の予防薬", "eff": ["頭痛"], "adv": ["注射部位の腫れ", "便秘"], "target": "adult_only", "type": "特殊薬（最先端治療）"},
        {"prefix": "オキシペイン徐放錠 5mg", "desc": "【強オピオイド・医療用麻薬】一般的な痛み止めが一切効かない、がんの激しい痛み（吐出痛）を脳の神経で直接遮断する強力な医療用麻薬", "eff": ["頭痛", "腰痛", "関節痛"], "adv": ["便秘", "吐き気", "強烈な眠気"], "target": "adult_only", "type": "特殊薬（麻薬処方箋必須）"},
        {"prefix": "ゾレキシル皮下注 150mg", "desc": "【重症アレルギー特効薬】花粉症や喘息の重症患者向けに、アレルギーを引き起こすIgE抗体そのものを中和して完全に症状を止める高額な特殊注射薬", "eff": ["鼻炎", "くしゃみ", "咳"], "adv": ["だるさ", "頭痛"], "target": "adult_only", "type": "特殊薬（分子標的薬）"},
        {"prefix": "スピロペント錠 10mcg", "desc": "【気管支拡張薬】気管支の筋肉を強力にゆるめて空気の通り道を広げ、止まらない喘息の咳を楽にする専門薬", "eff": ["咳"], "adv": ["手の震え", "動悸", "頭痛"], "target": "all", "type": "専門薬（呼吸器内科）"},
        {"prefix": "ネムラール錠 15mg", "desc": "【オレキシン受容体拮抗薬】脳の『覚醒スイッチ』を強制的にオフにすることで、依存性が極めて低く自然な睡眠をもたらす新世代の催眠薬", "eff": ["眠気"], "adv": ["翌朝のだるさ", "悪夢", "頭痛"], "target": "adult_only", "type": "専門薬（精神神経科）"}
    ]
    
    for rank in range(1, 2001):
        base_drug = friendly_categories[rank % len(friendly_categories)]
        drug_name = f"「{base_drug['prefix']}」 (実績: {rank}位 / 各社共通統合データ)"
        
        child_rank = rank if base_drug["target"] == "all" else rank + 5000
        if "カロナイン細粒" in base_drug["prefix"]: child_rank = int(rank / 10) + 1
        
        temp_db.append({
            "name": drug_name,
            "prefix": base_drug["prefix"],
            "category": base_drug["desc"],
            "efficacy": base_drug["eff"],
            "adverse": base_drug["adv"],
            "adult_rank": rank,
            "child_rank": child_rank,
            "target": base_drug["target"],
            "type": base_drug["type"]
        })
    st.session_state.app_db = temp_db

# 履歴メモリ
if 'seen_eff' not in st.session_state: st.session_state.seen_eff = set()
if 'seen_adv' not in st.session_state: st.session_state.seen_adv = set()
if 'history_symptoms' not in st.session_state: st.session_state.history_symptoms = set()

# --- ⚙️ サイドバー（課金設定） ---
st.sidebar.header("👑 アプリの購入設定")
user_mode = st.sidebar.radio("バージョン", ["無料版（機能制限あり）", "有料版（全機能解放）"])
is_premium = (user_mode == "有料版（全機能解放）")

if st.sidebar.button("🔄 検索履歴をリセット"):
    st.session_state.seen_eff = set()
    st.session_state.seen_adv = set()
    st.session_state.history_symptoms = set()
    st.sidebar.success("クリアしました！")

# ⚖️ タイトルと免責事項
st.title("💊 お薬逆引きAI ＆ 専門病院ナビ")
with st.expander("⚠️ 【重要】ご利用前の免責事項", expanded=False):
    st.caption("本アプリは処方統計に基づくデモアプリであり医師の診断に代わるものではありません。実際の体調不良は必ず医療機関を受診してください。")

st.write("---")

# 👶 【最上部】大人・子供の選択ボタン
st.subheader("はじめに：お薬を飲む方の年齢を選んでください")
age_mode = st.radio(
    "年齢によって処方されるお薬の順番や安全な種類が全自動で切り替わります：",
    ["👨 大人（15歳以上）", "👶 子ども（15歳未満）"],
    horizontal=True
)
is_child = ("子ども（15歳未満）" in age_mode)

st.write("---")

# --- 📱 お薬の名前から直接検索窓 ---
st.subheader("🔎 お薬の名前から直接調べる")
search_drug_name = st.text_input("お薬名（商品名）を入力してください（例：ズツウマプロ、カロナイン など）")

if search_drug_name:
    st.write(f"「**{search_drug_name}**」の検索結果：")
    found_any = False
    for drug in st.session_state.app_db:
        if search_drug_name in drug["name"]:
            found_any = True
            st.success(f"📌 **{drug['name']}**")
            st.write(f"➔ **医薬品の分類** : 【{drug['type']}】")
            st.write(f"➔ **この用量の作用特徴** : {drug['category']}")
            st.write(f"➔ **認められた効能の例** : {', '.join(drug['efficacy'])}")
            st.write(f"➔ **注意すべき副作用** : {', '.join(drug['adverse'])}")
            if is_child and drug["target"] == "adult_only":
                st.error("⚠️ 【警告】このお薬は子ども（15歳未満）への安全性が確立されていないため、原則処方されません。")
            st.write("-" * 50)
    if not found_any:
        st.info("該当するお薬が見つかりませんでした。")
    st.write("---")

# =========================================================================
# 🩺 【UI大改善】キーボードを一切出さない、チェックボックス並列選択システム
# =========================================================================
st.subheader("🩺 当てはまる症状をすべて選んでください（複数選択可）")
st.caption("※タップするだけで自動でチェックが付き、お薬がその場で瞬時に仕分けられます。")

# スマホの縦幅を無駄にしないよう、3列のキレイなグリッド（並列）を作成
c1, col_box2, col_box3 = st.columns(3)

selected_symptoms = []

# 1つずつ独立したチェックボックスとして症状を配置（キーボードは1秒も立ち上がりません）
with c1:
    if st.checkbox("頭痛 (頭が痛い)"): selected_symptoms.append("頭痛")
    if st.checkbox("喉の痛み"): selected_symptoms.append("喉の痛み")
    if st.checkbox("腰痛 (腰が痛い)"): selected_symptoms.append("腰痛")
    if st.checkbox("高血圧"): selected_symptoms.append("高血圧")

with col_box2:
    if st.checkbox("発熱 (熱がある)"): selected_symptoms.append("発熱")
    if st.checkbox("胃痛 (お腹の上側)"): selected_symptoms.append("胃痛")
    if st.checkbox("関節痛 (ふしぶし)"): selected_symptoms.append("関節痛")

with col_box3:
    if st.checkbox("鼻炎 (鼻水やくしゃみ)"): selected_symptoms.append("鼻炎")
    if st.checkbox("腹痛 (お腹の下側)"): selected_symptoms.append("腹痛")
    if st.checkbox("歯痛 (歯が痛い)"): selected_symptoms.append("歯痛")
    if st.checkbox("咳 (せきが出る)"): selected_symptoms.append("咳")

# --- 🧠 選択された症状に応じた検索処理セクション ---
if selected_symptoms:
    st.write("---")
    for s in selected_symptoms: st.session_state.history_symptoms.add(s)
        
    matched_eff = []
    matched_adv = []
    
    for drug in st.session_state.app_db:
        if is_child and drug["target"] == "adult_only":
            continue
            
        if keyword_count := sum(1 for s in selected_symptoms if s in drug["efficacy"]):
            if drug["name"] not in st.session_state.seen_eff:
                matched_eff.append({"data": drug, "count": keyword_count})
        if keyword_count_adv := sum(1 for s in selected_symptoms if s in drug["adverse"]):
            if drug["name"] not in st.session_state.seen_adv:
                matched_adv.append({"data": drug, "count": keyword_count_adv})
                
    rank_key = "child_rank" if is_child else "adult_rank"
    matched_eff.sort(key=lambda x: (-x["count"], x["data"][rank_key]))
    matched_adv.sort(key=lambda x: (-x["count"], x["data"][rank_key]))
    
    eff_show = matched_eff[:3]
    shown_eff_names = [item["data"]["name"] for item in eff_show]
    filtered_adv = [item for item in matched_adv if item["data"]["name"] not in shown_eff_names]
    adv_show = filtered_adv[:3]
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔵 効率よく『同時に治せる』お薬")
        for item in eff_show:
            d = item["data"]
            current_rank = d['child_rank'] if is_child else d['adult_rank']
            st.info(f"**{d['name']}** (処方実績:{current_rank}位)\n\n📜 効能: {', '.join(d['efficacy'])}")
            if is_premium: 
                st.caption(f"💊 **【区分: {d['type']}】**")
                st.caption(f"💡 {d['category']}")
                
            clean_name = d["name"].replace("「", "").replace("」", "").split(" ")
            encoded_name = urllib.parse.quote(clean_name[0])
            amazon_url = f"https://amazon.co.jp{encoded_name}&tag=YOUR_ID-22"
            st.markdown(f"[🛒 Amazonで探す]({amazon_url})")

    with col2:
        st.subheader("🔴 『副作用で出やすい』お薬")
        for item in adv_show:
            d = item["data"]
            current_rank = d['child_rank'] if is_child else d['adult_rank']
            st.warning(f"**{d['name']}** (処方実績:{current_rank}位)\n\n⚠️ 副作用: {', '.join(d['adverse'])}")
            if is_premium: 
                st.caption(f"💊 **【区分: {d['type']}】**")
                st.caption(f"💡 {d['category']}")

    st.write("---")
    
    if not is_premium:
        st.error("🔒 **【機能制限】4位以降のより専門的なお薬は、有料版で全機能解放されます。**")
    else:
        st.success(f"🔓 **有料版：全機能解放中**")
        if st.button("⏭️ 次の3件のお薬をめくる（さらに専門的な薬を表示）", use_container_width=True):
            for item in eff_show: st.session_state.seen_eff.add(item["data"]["name"])
            for item in adv_show: st.session_state.seen_adv.add(item["data"]["name"])
            st.rerun()

# --- 🏥 病院検索セクション ---
st.write("---")
st.subheader("🗺️ あなたの症状に合わせた「最寄りの専門病院」ナビ")

recommended_departments = set()
if st.session_state.history_symptoms:
    for s in st.session_state.history_symptoms:
        if s in ["頭痛", "眠気"]: recommended_departments.add("脳神経外科" if not is_child else "小児科")
        if s in ["発熱", "喉の痛み", "咳"]: recommended_departments.add("内科" if not is_child else "小児科")
        if s in ["鼻炎", "くしゃみ"]: recommended_departments.add("耳鼻咽喉科")
        if s in ["胃痛", "腹痛"]: recommended_departments.add("消化器内科" if not is_child else "小児科")
        if s in ["腰痛", "関節痛"]: recommended_departments.add("整形外科")
        if s in ["歯痛"]: recommended_departments.add("歯科")
        if s in ["高血圧"]: recommended_departments.add("循環器内科")

dept_list = list(recommended_departments) if recommended_departments else ["内科"]
