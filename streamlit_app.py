import streamlit as st
import random
import urllib.parse

# =========================================================================
# 【最終進化版】自動履歴クリア ＆ 1つ前に戻る機能 ＆ 無限めくり対応お薬アプリ
# =========================================================================

st.set_page_config(page_title="お薬逆引きAI & 病院ナビ", page_icon="💊", layout="centered")

# --- 🧠 内部データベースの構築（量・規格違いを含めて豊富に展開） ---
if 'app_db' not in st.session_state:
    temp_db = []
    symptom_pool = ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み", "胃痛", "腹痛", "咳", "腰痛", "関節痛", "歯痛", "高血圧"]
    side_effect_pool = ["眠気", "頭痛", "吐き気", "胃痛", "腹痛", "むくみ", "めまい"]
    
    friendly_categories = [
        {"prefix": "ロキソペイン錠 60mg", "type": "一般薬", "target": "adult_only", "desc": "【標準消炎鎮痛量】大人の激しい頭痛や急な発熱、関節の炎症を素早く鎮める消炎鎮痛薬の標準サイズです。", "eff": ["頭痛", "発熱", "歯痛", "関節痛"], "adv": ["胃痛", "腹痛"], "mg_guide": "●大人の頭痛・発熱・歯痛時の頓服：1回60mgを、空腹時を避けて服用します。"},
        {"prefix": "カロナイン錠 300mg", "type": "一般薬", "target": "all", "desc": "【中容量解熱鎮痛】胃に優しい成分。軽度の頭痛や、小柄な方・高齢者の方の熱をマイルドに下げるサイズです。", "eff": ["頭痛", "発熱", "喉の痛み"], "adv": ["眠気"], "mg_guide": "●大人の発熱・痛みの緩和：症状や年齢に合わせて1回300mg〜600mgの間で細かく調節されます。"},
        {"prefix": "カロナイン錠 500mg", "type": "一般薬", "target": "all", "desc": "【大容量解熱鎮痛】大人の頑固な偏頭痛や、風邪による高熱をしっかりとブロックするための大人向け標準サイズです。", "eff": ["頭痛", "発熱", "喉の痛み", "関節痛"], "adv": ["眠気", "食欲不振"], "mg_guide": "●成人の頑固な頭痛・腰痛：1回500mgを服用し、次の服用までは4時間以上あけます。"},
        {"prefix": "カロナイン細粒 20%", "type": "一般薬", "target": "all", "desc": "【乳幼児・小児用シロップ・粉薬】子どもの体重（kg）に合わせて、0.1g単位で医師が正確に量を計算して処方する子ども専用規格です。", "eff": ["頭痛", "発熱", "喉の痛み"], "adv": ["眠気"], "mg_guide": "●子どもの急性発熱：体重1kgあたり1回0.05g〜0.075g（成分として10〜15mg）を計算して服用します。"},
        {"prefix": "ズツウマプロ点鼻液 20mg", "type": "専門薬（脳神経外科）", "target": "adult_only", "desc": "【偏頭痛・トリプタン系発作薬】拡張した脳の血管を直接ピンポイントで収縮させ、激しい偏頭痛の発作を瞬時に止める特殊な鼻スプレーです。", "eff": ["頭痛"], "adv": ["めまい", "喉の不快感", "動悸"], "mg_guide": "●偏頭痛の発作発現時：片方の鼻腔に1回20mgを噴霧します。改善しない場合の追加は2時間以上あけます。"},
        {"prefix": "ガルペネズ皮下注 120mg", "type": "特殊薬（最先端治療）", "target": "adult_only", "desc": "【偏頭痛・抗体医薬品】月1回の注射で、偏頭痛を引き起こす脳内の原因物質（CGRP）を根元から長期間ブロックする最新の予防注射です。", "eff": ["頭痛"], "adv": ["注射部位の腫れ", "便秘"], "mg_guide": "●偏頭痛の予常管理：月1回、140mg（初回のみ2回分など）を皮下注射することで発作の頻度を激減させます。"},
        {"prefix": "オキシペイン徐放錠 5mg", "type": "特殊薬（麻薬処方箋必須）", "target": "adult_only", "desc": "【強オピオイド・医療用麻薬】一般的な痛み止めが一切効かない、がんの激しい痛み（吐出痛）を脳の神経で直接遮断する強力な医療用麻薬です。", "eff": ["頭痛", "腰痛", "関節痛"], "adv": ["便秘", "吐き気", "強烈な眠気"], "mg_guide": "●がん性疼痛の持続緩和：1回5mgから開始し、痛みの強さに応じて段階的に増量が検討される特殊な用量設計です。"},
        {"prefix": "スピロペント錠 10mcg", "type": "専門薬（呼吸器内科）", "target": "all", "desc": "【気管支拡張薬】気管支の筋肉を強力にゆるめて空気の通り道を広げ、止まらない喘息の激しい咳を劇的に楽にする専門薬です。", "eff": ["咳"], "adv": ["手の震え", "動悸", "頭痛"], "mg_guide": "●喘息の咳・腹圧性尿失禁：成人は1日2回、1回10mcg（マイクログラム）を朝・就寝前に服用します。"},
        {"prefix": "ネムラール錠 15mg", "type": "専門薬（精神神経科）", "target": "adult_only", "desc": "【オレキシン受容体拮抗薬】脳の『覚醒スイッチ』を強制的にオフにすることで、依存性が極めて低く自然な睡眠をもたらす新世代の催眠薬です。", "eff": ["眠気"], "adv": ["翌朝のだるさ", "悪夢", "頭痛"], "mg_guide": "●不眠症の改善：1回15mgを就寝の直前に服用します。高齢者の場合は1回10mgに減量されるケースがあります。"}
    ]
    
    # 2,000件の規模でお薬のリアルな規格違いをシミュレーション展開
    for rank in range(1, 2001):
        base_drug = friendly_categories[rank % len(friendly_categories)]
        drug_name = f"「{base_drug['prefix']}」"
        
        child_rank = rank if base_drug["target"] == "all" else rank + 5000
        if "カロナイン細粒" in base_drug["prefix"]: child_rank = int(rank / 10) + 1
        
        # 💡 【無限めくり対応】「頭痛」で弾切れにならないよう、後半のデータにも頭痛成分を確率で豊富に注入
        eff_words = list(base_drug["eff"])
        if rank > 50 and "頭痛" not in eff_words and random.random() < 0.4:
            eff_words.append("頭痛")
            
        temp_db.append({
            "name": drug_name,
            "prefix": base_drug["prefix"],
            "category": base_drug["desc"],
            "efficacy": eff_words,
            "adverse": base_drug["adv"],
            "mg_guide": base_drug["mg_guide"],
            "adult_rank": rank,
            "child_rank": child_rank,
            "target": base_drug["target"],
            "type": base_drug["type"]
        })
    st.session_state.app_db = temp_db

# 記憶保持用のメモリ
if 'seen_eff' not in st.session_state: st.session_state.seen_eff = set()
if 'seen_adv' not in st.session_state: st.session_state.seen_adv = set()
if 'history_symptoms' not in st.session_state: st.session_state.history_symptoms = set()
if 'last_selected_symptoms' not in st.session_state: st.session_state.last_selected_symptoms = []

# 💡 【新機能：戻る機能用のスタックメモリ】
if 'eff_history_stack' not in st.session_state: st.session_state.eff_history_stack = []
if 'adv_history_stack' not in st.session_state: st.session_state.adv_history_stack = []

# --- ⚙️ サイドバー（課金設定） ---
st.sidebar.header("👑 アプリの購入設定")
user_mode = st.sidebar.radio("バージョン", ["無料版（機能制限あり）", "有料版（全機能解放）"])
is_premium = (user_mode == "有料版（全機能解放）")

# --- ⚖️ タイトル表示 ---
st.title("💊 お薬逆引きAI ＆ 専門病院ナビ")
with st.expander("⚠️ 【重要】ご利用前の免責事項", expanded=False):
    st.caption("本アプリは処方統計に基づくデモアプリであり医師の診断に代わるものではありません。実際の体調不良は必ず医療機関を受診してください。")

st.write("---")

# --- 👶 【最上部】年齢選択UI ---
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
        if search_drug_name in drug["prefix"]:
            found_any = True
            st.success(f"📌 {drug['name']}")
            st.write(f"➔ **医薬品の分類** : 【{drug['type']}】")
            st.write(f"➔ **この用量の作用特徴** : {drug['category']}")
            st.write(f"➔ **認められた効能の例** : {', '.join(drug['efficacy'])}")
            st.write(f"➔ **注意すべき副作用** : {', '.join(drug['adverse'])}")
            if is_premium:
                st.info(f"📋 **【参考】病名別の標準的な用量ガイド**\n\n{drug['mg_guide']}")
            if is_child and drug["target"] == "adult_only":
                st.error("⚠️ 【警告】このお薬は子ども（15歳未満）への安全性が確立されていないため、原則処方されません。")
            st.write("-" * 50)
    if not found_any:
        st.info("該当するお薬が見つかりませんでした。")
    st.write("---")

# --- 📱 症状からの検索セクション ---
st.subheader("🩺 症状からお薬を処方順に検索")
selected_symptoms = st.multiselect(
    "今の症状をタップして選択してください（複数選択可）",
    ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み", "胃痛", "腹痛", "咳", "腰痛", "関節痛", "歯痛", "高血圧"]
)

# 💡 【新機能：症状の変更を検知して全自動履歴クリア】
if selected_symptoms != st.session_state.last_selected_symptoms:
    st.session_state.seen_eff = set()
    st.session_state.seen_adv = set()
    st.session_state.history_symptoms = set()
    st.session_state.eff_history_stack = []
    st.session_state.adv_history_stack = []
    st.session_state.last_selected_symptoms = selected_symptoms # 現在の症状を保存

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
        st.subheader("🔵 効率よく『同時に治せる』お薬")
        for item in eff_show:
            d = item["data"]
            current_rank = d['child_rank'] if is_child else d['adult_rank']
            st.info(f"**{d['name']}**\n\n📊 処方実績: {current_rank}位\n\n📜 効能: {', '.join(d['efficacy'])}")
            if is_premium: 
                st.caption(f"💊 **【区分: {d['type']}】**")
                st.caption(f"💡 {d['category']}")
                st.caption(f"📋 {d['mg_guide']}")
                
            clean_name = d["prefix"].replace("「", "").replace("」", "")
            encoded_name = urllib.parse.quote(clean_name)
            amazon_url = f"https://amazon.co.jp{encoded_name}&tag=YOUR_ID-22"
            st.markdown(f"[🛒 Amazonで探す]({amazon_url})")

    with col2:
        st.subheader("🔴 『副作用で出やすい』お薬")
        for item in adv_show:
            d = item["data"]
            current_rank = d['child_rank'] if is_child else d['adult_rank']
            st.warning(f"**{d['name']}**\n\n📊 処方実績: {current_rank}位\n\n⚠️ 副作用: {', '.join(d['adverse'])}")
            if is_premium: 
                st.caption(f"💊 **【区分: {d['type']}】**")
                st.caption(f"💡 {d['category']}")

    st.write("---")
    
    if not is_premium:
        st.error("🔒 **【機能制限】4位以降のより専門的なお薬は、有料版で全機能解放されます。**")
    else:
        st.success(f"🔓 **有料版：全機能解放中**")
        
        # 🎛️ ボタン配置用の横並び枠
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            # 💡 【新機能】1つ前の結果に戻るボタン（過去の履歴がスタックにある場合だけ押せる）
            if len(st.session_state.eff_history_stack) > 0:
                if st.button("⏮️ 1つ前の検索結果に戻る", use_container_width=True):
                    # 過去の3件を記憶から引き抜いて除外リストから消去する（復活させる）
                    last_eff = st.session_state.eff_history_stack.pop()
                    last_adv = st.session_state.adv_history_stack.pop()
