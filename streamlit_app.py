import streamlit as st
import random
import urllib.parse

# =========================================================================
# 【完全完成版】「次へめくるボタン」搭載 ＆ マップアプリ全自動連携アプリ
# =========================================================================

st.set_page_config(page_title="お薬逆引きAI & 病院ナビ", page_icon="💊", layout="centered")

# --- 🧠 内部データベースの構築 ---
if 'app_db' not in st.session_state:
    temp_db = []
    symptom_pool = ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み", "胃痛", "腹痛", "咳"]
    side_effect_pool = ["眠気", "頭痛", "吐き気", "胃痛", "腹痛", "むくみ", "めまい"]
    brand_prefixes = ["ハナミズキラー", "アタマノン", "ズツウレス", "ロキソペイン", "ネツサゲール", "カロナイン"]
    brand_suffixes = ["錠", "カプセル", "シロップ", "顆粒"]
    
    drug_categories = {
        "ハナミズキラー": "【アレルギー薬】花粉症などの鼻水・くしゃみを強力に抑える現代の定番薬",
        "ネムラール": "【催眠鎮静剤】興奮した脳の神経を落ち着かせて、深い眠りをサポートする薬",
        "アタマノン": "【頭痛専門】脳の血管の腫れをピンポイントで鎮める特効薬",
        "ズツウレス": "【偏頭痛・緊張型頭痛】あらゆる頭の痛みを素早く遮断する汎用鎮痛薬",
        "ロキソペイン": "【強力鎮痛】大人の激しい痛みや炎症をシャットアウトする消炎鎮痛薬",
        "ネツサゲール": "【解熱鎮痛】安全性が高く、熱と痛みの神経を優しくブロックするお薬",
        "カロナイン": "【子供・妊婦も安心】胃への負担が極めて少ないマイルドな解熱鎮痛薬",
        "セキドメミン": "【咳止め】脳の咳スイッチを鎮めて、止まらない激しい咳を楽にする薬"
    }
    
    # 1位から完璧な連番でお薬を格付け
    for rank in range(1, 1001):
        if rank <= 200:
            eff = ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み"]
            adv = ["眠気", "頭痛", "胃痛", "吐き気"]
        else:
            eff = random.sample(symptom_pool, 2)
            adv = random.sample(side_effect_pool, 2)
        prefix = random.choice(brand_prefixes)
        temp_db.append({
            "name": f"「{prefix}{random.choice(brand_suffixes)}」",
            "prefix": prefix,
            "category": drug_categories.get(prefix, "【一般治療薬】医師が日常的に処方する認可医薬品"),
            "efficacy": eff, "adverse": adv, "rank": rank
        })
    st.session_state.app_db = temp_db

# 履歴メモリ
if 'seen_eff' not in st.session_state: st.session_state.seen_eff = set()
if 'seen_adv' not in st.session_state: st.session_state.seen_adv = set()
if 'history_symptoms' not in st.session_state: st.session_state.history_symptoms = set()

# --- ⚙️ ユーザー課金設定のサイドバー ---
st.sidebar.header("👑 アプリの購入設定（収益化モデル）")
user_mode = st.sidebar.radio(
    "アプリのバージョンを選択",
    ["無料版（機能制限あり）", "有料版を購入（480円・全機能解放）"]
)
is_premium = (user_mode == "有料版を購入（480円・全機能解放）")

# 🔄 履歴リセットボタン（最初からやり直す）
if st.sidebar.button("🔄 検索履歴を完全にリセット"):
    st.session_state.seen_eff = set()
    st.session_state.seen_adv = set()
    st.session_state.history_symptoms = set()
    st.sidebar.success("履歴をクリアしました！1位から再表示されます。")

# ⚖️ 免責事項の表示
st.title("💊 お薬逆引きAI ＆ 専門病院ナビ")
with st.expander("⚠️ 【重要】ご利用前の免責事項", expanded=True):
    st.caption("本アプリは処方統計に基づくデモアプリであり医師の診断に代わるものではありません。実際の体調不良は必ず医療機関を受診してください。")

# 📱 症状の選択
selected_symptoms = st.multiselect(
    "今のあなたの症状をタップして選択してください（複数選択可）",
    ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み", "胃痛", "腹痛", "咳"]
)

if selected_symptoms:
    for s in selected_symptoms: st.session_state.history_symptoms.add(s)
        
    matched_eff = []
    matched_adv = []
    
    # データベースのスキャン（過去に見たものは自動で除外されるフィルター）
    for drug in st.session_state.app_db:
        if keyword_count := sum(1 for s in selected_symptoms if s in drug["efficacy"]):
            if drug["name"] not in st.session_state.seen_eff:
                matched_eff.append({"data": drug, "count": keyword_count})
        if keyword_count_adv := sum(1 for s in selected_symptoms if s in drug["adverse"]):
            if drug["name"] not in st.session_state.seen_adv:
                matched_adv.append({"data": drug, "count": keyword_count_adv})
                
    matched_eff.sort(key=lambda x: (-x["count"], x["data"]["rank"]))
    matched_adv.sort(key=lambda x: (-x["count"], x["data"]["rank"]))
    
    # 今回表示する3件を切り出し
    eff_show = matched_eff[:3]
    shown_eff_names = [item["data"]["name"] for item in eff_show]
    filtered_adv = [item for item in matched_adv if item["data"]["name"] not in shown_eff_names]
    adv_show = filtered_adv[:3]
    
    # 💡 【重要】「次へボタン」が押されたタイミングで履歴に保存されるようにするため、ここではまだ仮保存（表示のみ）にします
    
    # 画面出力
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔵 効率よく『同時に治せる』お薬")
        for item in eff_show:
            d = item["data"]
            st.info(f"**{d['name']}** (処方:{d['rank']}位)\n\n📜 効能: {', '.join(d['efficacy'])}")
            if is_premium: st.caption(f"💡 {d['category']}")
                
            encoded_name = urllib.parse.quote(d["name"].replace("「", "").replace("」", ""))
            amazon_url = f"https://amazon.co.jp{encoded_name}&tag=YOUR_ID-22"
            if is_premium:
                st.markdown(f"<a href='{amazon_url}' target='_blank' style='color:#00c0f0; text-decoration:none;'>🛒 Amazonで類似市販薬を探す</a>", unsafe_allow_html=True)
            else:
                st.markdown(f"<a href='{amazon_url}' target='_blank' style='color:#ff4b4b; text-decoration:none;'>🛒 Amazonで類似市販薬を探す（広告）</a>", unsafe_allow_html=True)

    with col2:
        st.subheader("🔴 『副作用で出やすい』お薬")
        for item in adv_show:
            d = item["data"]
            st.warning(f"**{d['name']}** (処方:{d['rank']}位)\n\n⚠️ 副作用: {', '.join(d['adverse'])}")
            if is_premium: st.caption(f"💡 {d['category']}")

    st.write("---")
    
    # =========================================================================
    # 🎛️ 【仕掛け】2回目以降の検索（続きをめくる）を実現する「次へボタン」アルゴリズム
    # =========================================================================
    if not is_premium:
        # 🆓 無料版：続きをめくろうとするとロック画面を表示
        st.error("🔒 **【機能制限】これより下位（4位以降）のお薬は、無料版では非表示になっています。**")
        st.caption("サイドバーから【有料版（480円）】を購入すると、制限が解除され、下の『次のお薬をめくる』ボタンが出現して無限に閲覧できるようになります。")
    else:
        # 👑 有料版：次のお薬へ進むための本物のボタンを配置！
        st.success(f"🔓 **有料版：全機能解放中**（現在までに累計 効能:{len(st.session_state.seen_eff)}件 / 副作用:{len(st.session_state.seen_adv)}件 を除外済）")
        
        # ボタンが押されたら、今見ているお薬を「除外履歴」に正式に登録して、画面を再起動（リロード）させる
        if st.button("⏭️ 次の3件のお薬をめくる（4位以降を表示）", use_container_width=True):
            for item in eff_show: st.session_state.seen_eff.add(item["data"]["name"])
            for item in adv_show: st.session_state.seen_adv.add(item["data"]["name"])
            st.rerun() # 👈 これにより、今見たお薬が完全に引き算され、次の3件が押し出されます！

# --- 🏥 病院検索セクション ---
st.write("---")
st.subheader("🗺️ あなたの症状に合わせた「最寄りの専門病院」ナビ")

recommended_departments = set()
if st.session_state.history_symptoms:
    for s in st.session_state.history_symptoms:
        if s in ["頭痛", "眠気"]: recommended_departments.add("脳神経外科")
        if s in ["発熱", "喉の痛み", "咳"]: recommended_departments.add("内科")
        if s in ["鼻炎"]: recommended_departments.add("耳鼻咽喉科")
        if s in ["胃痛", "腹痛"]: recommended_departments.add("消化器内科")

dept_list = list(recommended_departments) if recommended_departments else ["内科"]
dept_text = "、".join(dept_list)

if st.session_state.history_symptoms:
    st.write(f"📊 過去の検索履歴を分析しました。おすすめの診療科： **{dept_text}**")
else:
    st.write("👉 症状未選択の場合は、一般的な **内科** を案内します。")

primary_dept = dept_list if dept_list else "内科"
encoded_search_word = urllib.parse.quote(f"近くの {primary_dept}")
google_map_app_url = f"comgooglemaps://?q={encoded_search_word}"

if is_premium:
    st.success(f"📍 有料版限定機能：下のボタンをタップすると、iPhoneのGoogleマップアプリが【自動で文字が入力された状態】で一発起動します。")
    st.link_button(f"🗺️ 【近くの {primary_dept}】 をマップアプリで検索", google_map_app_url, use_container_width=True)
else:
    st.error("🔒 **【機能制限】専門病院への「マップアプリ自動連携」は、有料版限定の機能です。**")
