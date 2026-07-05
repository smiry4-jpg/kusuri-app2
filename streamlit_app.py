import streamlit as st
import random
import urllib.parse

# =========================================================================
# 【超軽量・150行特急版】GitHubのフリーズを解決した、真の最終お薬AIアプリ
# =========================================================================

st.set_page_config(page_title="お薬逆引きAI & 病院ナビ", page_icon="💊", layout="centered")

# --- 🧠 内部データベースの構築（軽量・規格違い200件版） ---
if 'app_db' not in st.session_state:
    temp_db = []
    symptom_pool = ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み", "胃痛", "腹痛", "咳"]
    side_effect_pool = ["眠気", "頭痛", "吐き気", "胃痛", "腹痛", "むくみ", "めまい"]
    brand_prefixes = ["ハナミズキラー", "アタマノン", "ズツウレス", "ロキソペイン", "ネツサゲール", "カロナイン"]
    
    drug_categories = {
        "ハナミズキラー": "【アレルギー薬】花粉症などの鼻水・くしゃみを強力に抑える定番薬。",
        "アタマノン": "【頭痛専門】脳の血管の腫れをピンポイントで鎮める特効薬。",
        "ズツウレス": "【偏頭痛・緊張型頭痛】あらゆる頭の痛みを素早く遮断する汎用鎮痛薬。",
        "ロキソペイン": "【強力鎮痛】大人の激しい痛みや炎症をシャットアウトする消炎鎮痛薬（60mg）。",
        "ネツサゲール": "【解熱鎮痛】安全性が高く、熱と痛みの神経を優しくブロックするお薬（500mg）。",
        "カロナイン": "【子供・妊婦も安心】胃への負担が少ないマイルドな解熱鎮痛薬（細粒20%）。"
    }
    
    # 1位から200位まで綺麗に並び替え
    for rank in range(1, 201):
        eff = ["頭痛", "発熱"] if rank <= 20 else random.sample(symptom_pool, 2)
        adv = ["眠気", "胃痛"] if rank <= 20 else random.sample(side_effect_pool, 2)
        prefix = random.choice(brand_prefixes)
        form_type = random.choice([" 60mg", " 300mg", " 500mg", " 細粒20%"])
        target = "adult_only" if prefix in ["ロキソペイン", "アタマノン"] else "all"
        
        temp_db.append({
            "name": f"「{prefix}{form_type}・{rank}号」",
            "prefix": prefix,
            "category": drug_categories.get(prefix, "【一般治療薬】医師が日常的に処方する認可医薬品"),
            "efficacy": eff, "adverse": adv, "rank": rank, "target": target
        })
    st.session_state.app_db = temp_db

# 記憶メモリ
if 'history_symptoms' not in st.session_state: st.session_state.history_symptoms = set()
if 'last_selected_symptoms' not in st.session_state: st.session_state.last_selected_symptoms = []
if 'current_page' not in st.session_state: st.session_state.current_page = 0
if 'last_age_mode' not in st.session_state: st.session_state.last_age_mode = "👨 大人（15歳以上）"

# 有料版状態の永続記憶メモリ
if 'saved_premium_status' not in st.session_state: st.session_state.saved_premium_status = "無料版（機能制限あり）"

# --- ⚙️ サイドバー（有料・無料切り替えスイッチ） ---
st.sidebar.header("👑 アプリの購入設定")
user_mode = st.sidebar.radio(
    "バージョン", ["無料版（機能制限あり）", "有料版（全機能解放）"],
    index=0 if st.session_state.saved_premium_status == "無料版（機能制限あり）" else 1
)
st.session_state.saved_premium_status = user_mode
is_premium = (user_mode == "有料版（全機能解放）")

# --- ⚖️ タイトル表示 ---
st.title("💊 お薬逆引きAI ＆ 専門病院ナビ")
st.caption("※本アプリはデモであり医師の診断に代わるものではありません。")
st.write("---")

# 👨‍⚕️ 年齢の選択ボタン（最上部固定）
st.subheader("はじめに：お薬を飲む方の年齢を選んでください")
age_mode = st.radio("年齢によって安全な種類が自動で切り替わります：", ["👨 大人（15歳以上）", "👶 子ども（15歳未満）"], horizontal=True)
is_child = ("子ども" in age_mode)

if age_mode != st.session_state.last_age_mode:
    st.session_state.current_page = 0
    st.session_state.history_symptoms = set()
    st.session_state.last_age_mode = age_mode
    st.rerun()

st.write("---")

# 🎛️ 2列配置のチェックボタン方式症状選択
st.subheader("🩺 今のあなたの症状にチェックを入れてください（複数選択可）")
symptom_cols = st.columns(2)
selected_symptoms = []
all_available_symptoms = ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み", "胃痛", "腹痛", "咳"]

for idx, symptom in enumerate(all_available_symptoms):
    target_col = symptom_cols[idx % 2]
    with target_col:
        if st.checkbox(symptom, key=f"check_{symptom}"):
            selected_symptoms.append(symptom)

# 💡 【完全復活】症状が変わった瞬間にページを0に戻し、1位からフレッシュリスタート（st.rerun）
if selected_symptoms != st.session_state.last_selected_symptoms:
    st.session_state.current_page = 0
    st.session_state.history_symptoms = set()
    st.session_state.last_selected_symptoms = selected_symptoms
    st.rerun()

# 🧠 お薬スキャン＆ソート処理
matched_eff = []
matched_adv = []

if selected_symptoms:
    for s in selected_symptoms: st.session_state.history_symptoms.add(s)
    for drug in st.session_state.app_db:
        if is_child and drug["target"] == "adult_only": continue
        if keyword_count := sum(1 for s in selected_symptoms if s in drug["efficacy"]): matched_eff.append({"data": drug, "count": keyword_count})
        if keyword_count_adv := sum(1 for s in selected_symptoms if s in drug["adverse"]): matched_adv.append({"data": drug, "count": keyword_count_adv})
                
    matched_eff.sort(key=lambda x: (-x["count"], x["data"]["rank"]))
    matched_adv.sort(key=lambda x: (-x["count"], x["data"]["rank"]))
    
    start_idx = st.session_state.current_page * 3
    end_idx = start_idx + 3
    eff_show = matched_eff[start_idx:end_idx]
    shown_eff_names = [item["data"]["name"] for item in eff_show]
    filtered_adv = [item for item in matched_adv if item["data"]["name"] not in shown_eff_names]
    adv_show = filtered_adv[start_idx:end_idx]
    
    # 💻 結果カード出力
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔵 効率よく『同時に治せる』お薬")
        for item in eff_show:
            d = item["data"]
            st.info(f"**{d['name']}**\n\n📊 処方実績: {d['rank']}位\n\n📜 効能: {', '.join(d['efficacy'])}")
            if is_premium: st.caption(f"💡 {d['category']}")
            amazon_url = f"https://amazon.co.jp{urllib.parse.quote(d['prefix'])}&tag=YOUR_ID-22"
            st.markdown(f"[🛒 Amazonで探す]({amazon_url})")

    with col2:
        st.subheader("🔴 『副作用で出やすい』お薬")
        for item in adv_show:
            d = item["data"]
            st.warning(f"**{d['name']}**\n\n📊 処方実績: {d['rank']}位\n\n⚠️ 副作用: {', '.join(d['adverse'])}")

st.write("---")

# =========================================================================
# 🎛️ 【大復活・常設配置】進む・戻るボタンセクション（1マスの字下げも無いフラット構造）
# =========================================================================
st.subheader("⏭️ お薬ランキングのページめくり")
not is_premium and st.error("🔒 4位以降のお薬は、有料版で全機能解放されます。")
is_premium and st.success(f"🔓 有料版：全機能解放中 （現在 {st.session_state.current_page * 3 + 1} 位付近を表示中）")

is_next_disabled = (len(matched_eff) <= (st.session_state.current_page * 3 + 3)) if selected_symptoms else True
if is_premium and st.button("⏭️ 次の3件のお薬をめくる (次ページへ)", use_container_width=True, disabled=is_next_disabled, key="n_btn"):
    st.session_state.current_page += 1
    st.rerun()
    
is_back_disabled = (st.session_state.current_page <= 0)
if is_premium and st.button("⏮️ 1つ前の検索結果に戻る (前ページへ)", use_container_width=True, disabled=is_back_disabled, key="b_btn"):
    st.session_state.current_page -= 1
    st.rerun()

# --- 🏥 病院検索セクション ＆ 【大復活】Googleマップ一発起動連携 ---
st.write("---")
st.subheader("🗺️ 最寄りの専門病院ナビ")
recommended_departments = set()
if st.session_state.history_symptoms:
    for s in st.session_state.history_symptoms:
        if s in ["頭痛", "眠気"]: recommended_departments.add("脳神経外科" if not is_child else "小児科")
        if s in ["発熱", "喉の痛み", "咳"]: recommended_departments.add("内科" if not is_child else "小児科")
        if s in ["鼻炎"]: recommended_departments.add("耳鼻咽喉科")
        if s in ["胃痛", "腹痛"]: recommended_departments.add("消化器内科" if not is_child else "小児科")

dept_list = list(recommended_departments) if recommended_departments else ["内科"]
primary_dept = dept_list[0]
st.write(f"📊 おすすめの診療科： **{primary_dept}**")

# 👑 【完全大復活】あの一撃でGoogleマップアプリが起動していた「魔法のアドレス」
google_map_app_url = f"comgooglemaps://?q={urllib.parse.quote('近くの ' + primary_dept)}"

if is_premium: st.success(f"📍 下のボタンをタップすると、iPhoneのGoogleマップアプリが一発起動します。")
if is_premium: st.link_button(f"🗺️ 【近くの {primary_dept}】 をマップアプリで検索", google_map_app_url, use_container_width=True)
not is_premium and st.error("🔒 専門病院への「マップアプリ自動連携」は、有料版限定の機能です。")
