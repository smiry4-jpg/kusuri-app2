import streamlit as st
import random
import urllib.parse

# =========================================================================
# 【お薬情報検索システム】「量(mg)」による効能と疾患別の情報提供デモ
# =========================================================================

st.set_page_config(page_title="お薬逆引きAI & 病院ナビ", page_icon="💊", layout="centered")

# --- 🧠 内部データベース（mg別の情報をシミュレーション） ---
if 'app_db' not in st.session_state:
    temp_db = []
    
    # 💡 【今回の核心】同じ成分名でも「mg（量）」によって期待される作用・解説が異なるデータ
    friendly_categories = [
        {
            "prefix": "アスピロン錠 100mg", 
            "desc": "【血液サラサラ作用】血管内の血の塊を防ぐ目的で、長期的な予防に用いられることが多いお薬です（※この用量では解熱・鎮痛作用は限定的です）。", 
            "eff": ["高血圧", "脳梗塞・心筋梗塞予防"], "adv": ["胃痛", "吐き気"], "target": "adult_only",
            "mg_guide": "●血管内血栓の予防：医師の判断に基づき、1日1回100mgで処方されるケースがあります。"
        },
        {
            "prefix": "アスピロン錠 500mg", 
            "desc": "【解熱鎮痛作用】熱や痛みを引き起こす物質の生成を抑え、主に頭痛や発熱の際に頓服として使用されるお薬です。", 
            "eff": ["頭痛", "発熱", "歯痛"], "adv": ["胃痛", "腹痛", "吐き気"], "target": "adult_only",
            "mg_guide": "●頭痛・発熱時の頓服：1回500mgを、空腹時を避けて服用するケースがあります。"
        },
        {
            "prefix": "セレコペイン錠 100mg", 
            "desc": "【持続型：消炎鎮痛】関節の腫れや長引く痛みの原因を抑え、炎症をじわじわと楽にするお薬です。", 
            "eff": ["関節痛", "腰痛"], "adv": ["胃痛", "むくみ"], "target": "adult_only",
            "mg_guide": "●変形性関節症・関節リウマチ：1回100mgを1日2回（朝・夕）処方されるケースがあります。"
        },
        {
            "prefix": "セレコペイン錠 200mg", 
            "desc": "【速効型：消炎鎮痛】急な炎症や強い痛みをピンポイントで抑えるお薬です。", 
            "eff": ["頭痛", "歯痛", "生理痛"], "adv": ["胃痛", "腹痛"], "target": "adult_only",
            "mg_guide": "●急性な痛みの緩和：最初の1回目、2回目以降で用量が調整されるケースがあります。"
        },
        {
            "prefix": "カロナイン錠 200mg", 
            "desc": "【小容量：解熱鎮痛成分】胃への負担が比較的少なく、子どもの発熱や小柄な方向けの小容量サイズです。", 
            "eff": ["頭痛", "発熱", "喉の痛み"], "adv": ["眠気"], "target": "all",
            "mg_guide": "●子どもの発熱・頭痛：年齢や体重（例:10-15mg/kg）に基づき計算して服用するケースがあります。"
        },
        {
            "prefix": "カロナイン錠 500mg", 
            "desc": "【標準量：解熱鎮痛成分】大人の頑固な頭痛や、風邪による発熱を抑えるための、標準的な大人向け用量サイズです。", 
            "eff": ["頭痛", "発熱", "喉の痛み", "関節痛"], "adv": ["眠気", "食欲不振"], "target": "all",
            "mg_guide": "●大人の頭痛・関節痛：1回500mg以上を服用するケースがあります。"
        },
        {
            "prefix": "ハナミズキラーカプセル", "desc": "【抗ヒスタミン作用】花粉症などによる鼻水やくしゃみをブロックするお薬", "eff": ["鼻炎", "くしゃみ"], "adv": ["眠気", "頭痛"], "target": "all", "mg_guide": "●アレルギー性鼻炎：1回1カプセルを1日2回（朝・就寝前）処方されるケースがあります。"
        },
        {
            "prefix": "セキドメミン液", "desc": "【咳中枢抑制】咳の過剰な興奮を鎮める、咳止め用の内服薬", "eff": ["咳", "喉の痛み"], "adv": ["眠気", "便秘"], "target": "all", "mg_guide": "●激しい咳の鎮静：1回5mLを1日3回、症状がひどい時のみ服用するケースがあります。"
        }
    ]
    
    for rank in range(1, 2001):
        base_drug = friendly_categories[rank % len(friendly_categories)]
        drug_name = f"{base_drug['prefix']} (コード: JP-{10000 + rank})"
        
        child_rank = rank if base_drug["target"] == "all" else rank + 5000
        if "カロナイン錠 200mg" in base_drug["prefix"]: child_rank = int(rank / 10) + 1
        
        temp_db.append({
            "name": drug_name,
            "prefix": base_drug["prefix"],
            "category": base_drug["desc"],
            "efficacy": base_drug["eff"],
            "adverse": base_drug["adv"],
            "mg_guide": base_drug["mg_guide"],
            "adult_rank": rank,
            "child_rank": child_rank,
            "target": base_drug["target"]
        })
    st.session_state.app_db = temp_db

# メモリ保持
if 'seen_eff' not in st.session_state: st.session_state.seen_eff = set()
if 'seen_adv' not in st.session_state: st.session_state.seen_adv = set()
if 'history_symptoms' not in st.session_state: st.session_state.history_symptoms = set()

# --- ⚙️ サイドバー設定 ---
st.sidebar.header("👑 アプリの設定")
user_mode = st.sidebar.radio("バージョン", ["無料版（機能制限あり）", "有料版（全機能解放）"])
is_premium = (user_mode == "有料版（全機能解放）")

st.sidebar.header("👶 対象者の年齢")
age_mode = st.sidebar.radio("年齢区分を選んでください", ["大人（15歳以上）", "子ども（15歳未満）"])
is_child = (age_mode == "子ども（15歳未満）")

if st.sidebar.button("🔄 履歴をリセット"):
    st.session_state.seen_eff = set()
    st.session_state.seen_adv = set()
    st.session_state.history_symptoms = set()
    st.sidebar.success("履歴をクリアしました！")

st.title("💊 お薬逆引きAI ＆ 専門病院ナビ")
st.write("---")

# =========================================================================
# 🔍 【機能拡張】量(mg)別の「病名別情報」を出力する検索システム
# =========================================================================
st.subheader("🔎 お薬の成分名から「量（mg）と期待される作用の違い」を調べる")
search_drug_name = st.text_input("お薬名（商品名）を入力してください（例：アスピロン、セレコペイン、カロナイン など）")

if search_drug_name:
    st.write(f"「**{search_drug_name}**」のミリ数（容量）別の違いを判定しました：")
    found_any = False
    for drug in st.session_state.app_db:
        if search_drug_name in drug["name"]:
            found_any = True
            st.success(f"📌 **{drug['name']}**")
            st.write(f"➔ **この用量の作用特徴** : {drug['category']}")
            st.write(f"➔ **認められた効能の例** : {', '.join(drug['efficacy'])}")
            
            # 💡 【情報ガイド】
            if is_premium:
                st.info(f"📋 **【参考】病名別の一般的な用法・用量情報**\n\n{drug['mg_guide']}")
            else:
                st.error("🔒 **【機能制限】『病名ごとの標準的な用量ガイド』は有料版でご覧いただけます。**")
                
            st.write("-" * 50)
    if not found_any:
        st.info("該当するお薬が見つかりませんでした。デモ用表現（アスピロン、セレコペイン等）でお試しください。")
    st.write("---")

# --- 📱 メイン画面：症状からの検索 ---
st.subheader("🩺 症状からお薬を検索")
selected_symptoms = st.multiselect(
    "今の症状をタップして選択してください（複数選択可）",
    ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み", "胃痛", "腹痛", "咳", "腰痛", "関節痛", "歯痛", "高血圧"]
)

if selected_symptoms:
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
        st.subheader("🔵 期待される作用の例")
        for item in eff_show:
            d = item["data"]
            current_rank = d['child_rank'] if is_child else d['adult_rank']
            st.info(f"**{d['name']}**\n\n📜 作用: {', '.join(d['efficacy'])}")
            if is_premium: 
                st.caption(f"💡 {d['category']}")
                st.caption(f"📋 {d['mg_guide']}")
                
            encoded_name = urllib.parse.quote(d["name"].replace("「", "").replace("」", ""))
            amazon_url = f"https://amazon.co.jp{encoded_name}&tag=YOUR_ID-22"
            st.markdown(f"[🛒 Amazonで検索]({amazon_url})")

    with col2:
        st.subheader("🔴 報告されている副作用の例")
        for item in adv_show:
            d = item["data"]
            current_rank = d['child_rank'] if is_child else d['adult_rank']
            st.warning(f"**{d['name']}**\n\n⚠️ 副作用: {', '.join(d['adverse'])}")
            if is_premium: st.caption(f"💡 {d['category']}")

    st.write("---")
    
    if not is_premium:
        st.error("🔒 **【機能制限】3件以降の検索結果は、有料版で表示されます。**")
    else:
        st.success(f"🔓 **有料版：全機能解放中**")
        if st.button("⏭️ 次の検索結果を表示", use_container_width=True):
            for item in eff_show: st.session_state.seen_eff.add(item["data"]["name"])
            for item in adv_show: st.session_state.seen_adv.add(item["data"]["name"])
            st.rerun()

# --- 🏥 病院検索セクション ---
st.write("---")
st.subheader("🗺️ 専門病院検索")

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
dept_text = "、".join(dept_list)

if st.session_state.history_symptoms:
    st.write(f"📊 分析されたおすすめの診療科： **{dept_text}**")
else:
    st.write("👉 症状未選択の場合は、一般的な **内科** を案内します。")

primary_dept = dept_list[0] if dept_list else "内科"
encoded_search_word = urllib.parse.quote(f"近くの {primary_dept}")
google_map_app_url = f"comgooglemaps://?q={encoded_search_word}"

if is_premium:
    st.success(f"📍 有料版機能：ボタンタップでマップアプリが起動します。")
    st.link_button(f"🗺️ 【近くの {primary_dept}】 を検索", google_map_app_url, use_container_width=True)
else:
    st.error("🔒 **【機能制限】専門病院マップ連携は、有料版限定です。**")
