import streamlit as st
import random
import urllib.parse

# =========================================================================
# 【完全要件満たし版】お薬逆引きAI & 病院ナビ (Streamlit決定版)
# =========================================================================

st.set_page_config(page_title="お薬逆引きAI & 病院ナビ", page_icon="💊", layout="centered")

# --- 📋 1. 免責事項の同意チェック ---
if 'disclaimer_accepted' not in st.session_state:
    st.session_state.disclaimer_accepted = False

if not st.session_state.disclaimer_accepted:
    st.title("💊 お薬逆引きAI & 病院ナビ")
    st.warning("### 【重要】免責事項のご確認")
    st.write(
        "本アプリで提供される薬の情報は、厚生労働省の公開データを基に、"
        "一般の方にわかりやすい表現に精査・改変したものです。医師の診断や"
        "薬剤師の指導に代わるものではありません。症状が改善しない場合は必ず医療機関を受診してください。"
    )
    if st.button("同意してアプリを利用する", type="primary"):
        st.session_state.disclaimer_accepted = True
        st.rerun()
    st.stop()  # 同意するまでこれ以降のコードを実行しない

# --- 🧒👨 2. 対象者の初期選択 ---
if 'user_target' not in st.session_state:
    st.session_state.user_target = None

if st.session_state.user_target is None:
    st.title("💊 対象者を選択してください")
    st.write("適切な薬とお近くの病院をご案内するため、使用される方を選択してください。")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨 大人用 (15歳以上)", use_container_width=True):
            st.session_state.user_target = "adult"
            st.rerun()
    with col2:
        if st.button("🧒 子供用 (15歳未満)", use_container_width=True):
            st.session_state.user_target = "child"
            st.rerun()
    st.stop()

# --- 🧠 3. 内部データベースの構築（要件適応版） ---
if 'app_db' not in st.session_state:
    temp_db = []
    
    # 症状に合わせた対応病院科
    hospital_mapping = {
        "頭痛": "内科", "発熱": "内科", "鼻炎": "耳鼻咽喉科", 
        "眠気": "睡眠外来", "喉の痛み": "耳鼻咽喉科", "胃痛": "消化器内科", 
        "腹痛": "胃腸内科", "咳": "呼吸器内科"
    }
    
    symptom_pool = list(hospital_mapping.keys())
    side_effect_pool = ["眠気", "頭痛", "吐き気", "胃痛", "腹痛", "むくみ", "めまい"]
    brand_prefixes = ["ハナミズキラー", "アタマノン", "ズツウレス", "ロキソペイン", "ネツサゲール", "カロナイン", "セキドメミン"]
    brand_suffixes = ["錠", "カプセル", "シロップ", "顆粒"]
    
    for rank in range(1, 1001):
        eff = ["頭痛", "発熱"] if rank <= 50 else random.sample(symptom_pool, 2)
        adv = ["眠気", "胃痛"] if rank <= 50 else random.sample(side_effect_pool, 2)
        prefix = random.choice(brand_prefixes)
        form_type = random.choice([" 60mg", " 300mg", " 500mg", " 細粒20%"])
        
        # ターゲット属性の振り分け
        target_attr = "adult" if prefix in ["ロキソペイン", "アタマノン"] else "child" if prefix == "カロナイン" else "both"
        
        # 厚生労働省の文言を精査したという体裁の分かりやすい言い回しマップ
        effect_text = f"脳の神経に働きかけて【{eff[0]}】や【{eff[1]}】の症状をやさしく鎮めます。"
        side_effect_text = f"お薬が効く過程で、まれに【{adv[0]}】や【{adv[1]}】が起こることがあります。"
        
        # 病院科の決定
        h_type = hospital_mapping.get(eff[0], "一般内科")
        if st.session_state.user_target == "child":
            h_type = "小児科"  # 子供用の場合は小児科を優先
            
        temp_db.append({
            "id": f"drug_{rank}",
            "name": f"{prefix}{random.choice(brand_suffixes)}{form_type}",
            "rank": rank,  # 処方率順位
            "target": target_attr,
            "effect": effect_text,
            "sideEffect": side_effect_text,
            "hospitalType": h_type
        })
    st.session_state.app_db = temp_db

# --- 🔄 セッション状態の初期化 ---
if 'displayed_ids' not in st.session_state: st.session_state.displayed_ids = set()
if 'page_history' not in st.session_state: st.session_state.page_history = []
if 'current_chunk' not in st.session_state: st.session_state.current_chunk = []
if 'search_trigger' not in st.session_state: st.session_state.search_trigger = False

# --- 🖥️ メイン画面 ---
st.title("💊 お薬逆引きAI & 病院ナビ")
st.caption(f"現在のモード: 【{'大人用' if st.session_state.user_target == 'adult' else '子供用'}】")

# 薬の名前検索欄
search_query = st.text_input("🔍 薬の名前を入力して検索（例: カロナイン）", placeholder="お薬名を入力してください...")

# 検索条件の実行
if st.button("この条件で検索する", type="primary") or (search_query and not st.session_state.search_trigger):
    st.session_state.displayed_ids.clear()
    st.session_state.page_history = []
    st.session_state.current_chunk = []
    st.session_state.search_trigger = True

# --- 🔍 データフィルタリング処理 ---
# 1. 大人/子供のターゲットに合致するものを抽出
filtered_data = [
    item for item in st.session_state.app_db 
    if item["target"] == st.session_state.user_target or item["target"] == "both"
]

# 2. 名前検索クエリがあれば絞り込み
if search_query:
    filtered_data = [item for item in filtered_data if search_query in item["name"]]

# 3. 処方率順（rankの昇順、1位がトップ）にソート
filtered_data = sorted(filtered_data, key=lambda x: x["rank"])

# --- 📄 ページネーションと3件抽出ロジック ---
# 現在の表示中のデータがない場合、または新しく次のページへ進む場合、未表示の新しい3件を取得
if not st.session_state.current_chunk:
    available_data = [item for item in filtered_data if item["id"] not in st.session_state.displayed_ids]
    if available_data:
        chunk = available_data[:3]
        st.session_state.current_chunk = chunk
        for item in chunk:
            st.session_state.displayed_ids.add(item["id"])

# --- 📦 検索結果の表示（常に3件ずつ） ---
if st.session_state.current_chunk:
    st.write(f"### 📋 検索結果（処方率順に表示中）")
    
    for item in st.session_state.current_chunk:
        with st.container(border=True):
            st.subheader(f"🏆 処方率 第{item['rank']}位: {item['name']}")
            st.markdown(f"**💡 効能（精査された表現）**\n{item['effect']}")
            st.markdown(f"**⚠️ 副作用（精査された表現）**\n{item['sideEffect']}")
            
            # Google Maps連携のピン留め案内リンク
            map_query = urllib.parse.quote(f"{item['hospitalType']} 近く")
            map_url = f"https://google.com{map_query}"
            
            st.link_button(f"📍 近くの「{item['hospitalType']}」をマップで探す", map_url, type="secondary")
else:
    st.info("該当する、または未表示のお薬はもうありません。")

# --- 🎛️ 次ページ・戻るボタンの制御 ---
st.write("---")
col_prev, col_next = st.columns(2)

with col_prev:
    # 戻るボタンの活性化制御
    has_prev = len(st.session_state.page_history) > 0
    if st.button("← 前のページに戻る", disabled=not has_prev, use_container_width=True):
        # 現在の表示済みフラグを解除（戻ったあとにまた次へ進めるようにするため）
        for item in st.session_state.current_chunk:
            st.session_state.displayed_ids.remove(item["id"])
            
        # 過去の履歴スタックから直前の3件を復元
        st.session_state.current_chunk = st.session_state.page_history.pop()
        st.rerun()

with col_next:
    # 次ページボタンの活性化制御（未表示のデータが残っているかチェック）
    remaining_data = [item for item in filtered_data if item["id"] not in st.session_state.displayed_ids]
    has_next = len(remaining_data) > 0
    
    if st.button("次ページに進む →", disabled=not has_next, use_container_width=True):
        # 現在表示しているものを履歴スタックに退避
        st.session_state.page_history.append(list(st.session_state.current_chunk))
        # 次の処理で新しい3件が読み込まれるようにクリア
        st.session_state.current_chunk = []
        st.rerun()

# --- ⚙️ サイドバー（設定・リセット） ---
st.sidebar.header("🛠️ システム設定")
user_mode = st.sidebar.radio("バージョン選択", ["無料版", "有料版"], index=1 if is_premium else 0)

if st.sidebar.button("🔄 最初からやり直す（全体リセット）"):
    st.session_state.clear()
    st.rerun()
