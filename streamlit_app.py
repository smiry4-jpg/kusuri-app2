import streamlit as st
import urllib.parse

# =========================================================================
# 【有料無料切り替えバグ完全修正版】お薬逆引きAI & 病院ナビ (追加修正版)
# =========================================================================

st.set_page_config(page_title="お薬逆引きAI & 病院ナビ", page_icon="💊", layout="wide")

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
    st.stop()

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

is_child = (st.session_state.user_target == "child")

# --- ⚙️ 3. 【最優先修正】サイドバーの有料・無料切り替え判定 ---
# データベース構築より前に判定を置くことで、すべての表示に即時反映させます
st.sidebar.header("🛠️ システム設定")

if 'saved_premium_status' not in st.session_state:
    st.session_state.saved_premium_status = "有料版（全機能解放）"

# ラジオボタンの選択肢を現在のセッション状態から初期化
current_index = 0 if st.session_state.saved_premium_status == "無料版" else 1
user_mode = st.sidebar.radio("バージョン選択", ["無料版", "有料版（全機能解放）"], index=current_index)

# 選択が切り替わったらセッションを更新して即座に再描画（リロード）
if user_mode != st.session_state.saved_premium_status:
    st.session_state.saved_premium_status = user_mode
    st.rerun()

is_premium = (st.session_state.saved_premium_status == "有料版（全機能解放）")


# --- 🧠 4. 【mg・剤形 厳密細分化版】本物のマスターデータベース ---
if 'app_db' not in st.session_state:
    st.session_state.app_db = [
        # --- 大人用：カロナール（mg数・使用条件で分離） ---
        {
            "id": "M001-200", 
            "name": "カロナール錠 200mg（成分: アセトアミノフェン）",
            "rank": 1,
            "target": "adult_only",
            "efficacy": ["頭痛", "発熱"],
            "adverse": ["胃痛"],
            "effect_detail": "比較的軽度な頭痛や、風邪の初期症状における発熱を優しく鎮めます。1回あたりの成分量が抑えめな規格です。",
            "adverse_detail": "胃への影響は極めて穏やかですが、体質により軽度の胃痛を覚えることがあります。長期間の連続服用は避けてください。",
            "hospitalType": "内科",
            "category": "【解熱鎮痛薬】マイルドに効く200mg規格の錠剤です。"
        },
        {
            "id": "M001-300", 
            "name": "カロナール錠 300mg（成分: アセトアミノフェン）",
            "rank": 2,
            "target": "adult_only",
            "efficacy": ["頭痛", "発熱", "喉の痛み"],
            "adverse": ["胃痛", "吐き気"],
            "effect_detail": "大人の標準的な頭痛、および風邪に伴う激しい熱や喉の痛みを効果的に和らげるために広く処方される強さです。",
            "adverse_detail": "胃粘膜への刺激は少ないですが、敏感な方は一時的な胃痛や軽い吐き気を感じることがあります。",
            "hospitalType": "内科",
            "category": "【解熱鎮痛薬】大人の風邪症状に最も頻繁に選ばれる300mg規格です。"
        },
        {
            "id": "M001-500", 
            "name": "カロナール錠 500mg（成分: アセトアミノフェン）",
            "rank": 3,
            "target": "adult_only",
            "efficacy": ["頭痛", "喉の痛み"],
            "adverse": ["吐き気"],
            "effect_detail": "1錠中の成分量が多いため、通常の熱・痛み止めでは緩和しにくい、激しい偏頭痛や、のどの酷い炎症による痛みをしっかり遮断します。",
            "adverse_detail": "高用量のため、一度に飲むと胃のムカムカ感や吐き気が出やすくなります。また肝臓への影響を防ぐため、1日の上限量を厳守する必要があります。",
            "hospitalType": "内科",
            "category": "【解熱鎮痛薬】強い痛みに対してピンポイントで処方される高用量500mg規格です。"
        },
        # --- 大人用：その他のお薬 ---
        {
            "id": "M002-60", 
            "name": "ロキソニン錠 60mg（成分: ロキソプロフェンナトリウム）",
            "rank": 4,
            "target": "adult_only",
            "efficacy": ["頭痛", "発熱", "喉の痛み"],
            "adverse": ["胃痛", "腹痛"],
            "effect_detail": "炎症を引き起こす体内物質を強力に抑え込み、激しい頭痛、喉の腫れ、高熱を非常に素早く鎮めます。",
            "adverse_detail": "強い効果の反面、胃の粘膜を保護する働きも弱めてしまうため、高確率で胃痛や腹痛、胃もたれを招きます。必ず胃を守るために空腹時を避けてください。",
            "hospitalType": "内科",
            "category": "【消炎解熱鎮痛薬】非常にシャープに効きますが、胃障害のリスクが高いため注意が必要なお薬です。"
        },
        {
            "id": "M003-60", 
            "name": "アレグラ錠 60mg（成分: フェキソフェナジン塩酸塩）",
            "rank": 5,
            "target": "adult_only",
            "efficacy": ["鼻炎"],
            "adverse": ["眠気"],
            "effect_detail": "花粉やハウスダストが原因で起こるアレルギー性のしつこい鼻水、連続するくしゃみを根元からブロックします。",
            "adverse_detail": "脳に薬の成分が移行しにくい特殊な設計のため、アレルギー薬特有の眠気が出にくいですが、人によっては軽微な眠気を覚えることがあります。",
            "hospitalType": "耳鼻咽喉科",
            "category": "【抗ヒスタミン薬】仕事や運転など、日常の活動に支障をきたしにくい安全性の高い鼻炎薬です。"
        },
        {
            "id": "M004-15", 
            "name": "メジコン錠 15mg（成分: デキストロメトルファン臭化水素酸塩）",
            "rank": 6,
            "target": "adult_only",
            "efficacy": ["咳"],
            "adverse": ["眠気", "吐き気"],
            "effect_detail": "脳内の咳コントロールセンター（咳中枢）に直接働きかけ、気管支の刺激によって止まらなくなった激しい咳を力強く鎮めます。",
            "adverse_detail": "神経に作用するため、人によっては軽い眠気やめまい、あるいは胃の不快感（吐き気）を伴うことがあります。",
            "hospitalType": "呼吸器内科",
            "category": "【非麻薬性鎮咳薬】依存性の心配がなく、一般的な風邪のしつこい咳に広く使われる錠剤です。"
        },
        {
            "id": "M005-250", 
            "name": "ムコダイン錠 250mg（成分: カルボシステイン）",
            "rank": 7,
            "target": "adult_only",
            "efficacy": ["鼻炎"],
            "adverse": ["胃痛"],
            "effect_detail": "鼻の奥につまったドロドロした粘り気のある鼻水をサラサラに変え、体外へ排出しやすくして副鼻腔の不快感を改善します。",
            "adverse_detail": "きわめて安全ですが、胃の弱い方では稀に軽い胃の不快感や胃痛を覚えることがあります。",
            "hospitalType": "耳鼻咽喉科",
            "category": "【気道粘液調整薬】鼻づまりや軽度の鼻炎症状に対して処方される低用量250mg規格です。"
        },
        {
            "id": "M005-500", 
            "name": "ムコダイン錠 500mg（成分: カルボシステイン）",
            "rank": 8,
            "target": "adult_only",
            "efficacy": ["咳", "喉の痛み"],
            "adverse": ["腹痛"],
            "effect_detail": "喉や気管支にべったりと張り付いて離れないしつこい痰（たん）を分解して流動化し、咳と一緒にスムーズに吐き出せるようにします。",
            "adverse_detail": "成分量が多い規格のため、腸内環境にわずかに影響し、稀に軽い腹痛や軟便を引き起こすことがあります。",
            "hospitalType": "呼吸器内科",
            "category": "【気道粘液調整薬】気管支炎など、痰が絡んで喉が痛む咳に処方される標準的な500mg規格です。"
        },
        # --- 子供用：細粒・ドライシロップ・シロップ ---
        {
            "id": "C001-20", 
            "name": "小児用カロナール細粒 20%（成分: アセトアミノフェン）",
            "rank": 1,
            "target": "child_only",
            "efficacy": ["頭痛", "発熱", "喉の痛み"],
            "adverse": ["胃痛", "吐き気"],
            "effect_detail": "乳幼児から学童期まで広く使われるお薬です。お子さまの急な高熱や、中耳炎などによる激しい痛みを脳の神経から優しく緩和します。",
            "adverse_detail": "安全性が非常に高いお薬ですが、お子さまの【体重】に合わせて1回量を1ミリグラム単位で正確に小児科医が計算します。量を間違えると肝臓に重い負担がかかります。",
            "hospitalType": "小児科",
            "category": "【小児用解熱鎮痛薬】粉タイプで量を細かく調節できる、子ども用熱・痛み止めの第一選択薬です。"
        },
        {
            "id": "C001-SYR", 
            "name": "カロナールシロップ 2%（成分: アセトアミノフェン）",
            "rank": 2,
            "target": "child_only",
            "efficacy": ["発熱"],
            "adverse": ["吐き気"],
            "effect_detail": "粉薬をまだ上手に飲み込むことができない、ごく小さなお子さまや赤ちゃん（乳幼児）の発熱を優しく下げるための液体のお薬です。",
            "adverse_detail": "甘い味がついていて飲みやすいですが、嫌がって一度に大量に誤飲すると危険です。服用後に吐き気などの副反応が出ないか様子を見てあげてください。",
            "hospitalType": "小児科",
            "category": "【小児用解熱鎮痛液体薬】赤ちゃんでも安全に服用できるように作られたシロップ剤です。"
        },
        {
            "id": "C002-DS", 
            "name": "オノンドライシロップ 10%（成分: プランルカスト）",
            "rank": 3,
            "target": "child_only",
            "efficacy": ["鼻炎", "咳"],
            "adverse": ["眠気", "腹痛"],
            "effect_detail": "お子さまのアレルギー性のしつこい鼻づまりや、気管支が狭くなってゼーゼーと苦しそうな咳（喘息発作）が起きるのを根底から防ぎます。",
            "adverse_detail": "服用後に軽い眠気や腹痛が起きることがあります。また、一時的にお子さまの機嫌が悪くなったり（易刺激性）する副作用が報告されています。",
            "hospitalType": "小児科",
            "category": "【抗ロイコトリエン薬】アレルギーによる気道や鼻の炎症を長期的におさえる定番の子供用お薬です。"
        },
        {
            "id": "C003-10", 
            "name": "アスベリン散 10%（成分: チペピジンヒバイン酸塩）",
            "rank": 4,
            "target": "child_only",
            "efficacy": ["咳"],
            "adverse": ["眠気"],
            "effect_detail": "お子さまの止まらないコンコンという乾いた咳を脳から鎮め、同時にのどに絡む粘り気のある痰をサラサラにして出しやすくします。",
            "adverse_detail": "軽い眠気を誘発することがあります。また、お薬が体内で分解されて排出される際、一時的に【尿が赤っぽくなる】特徴がありますが、無害ですので驚かなくて大丈夫です。",
            "hospitalType": "小児科",
            "category": "【小児用鎮咳去痰薬】咳を止め、痰を切りやすくする子供向けの代表的な粉末の咳止めです。"
        }
    ]

# --- 🔄 セッション状態の初期化 ---
if 'current_page' not in st.session_state: st.session_state.current_page = 0
if 'last_selected_symptoms' not in st.session_state: st.session_state.last_selected_symptoms = []
if 'last_search_query' not in st.session_state: st.session_state.last_search_query = ""

# --- 🖥️ メイン画面の表示エリア ---
st.title("💊 お薬逆引きAI & 病院ナビ")
st.caption(f"現在の対象モード: 【{'子供用 (15歳未満)' if is_child else '大人用 (15歳以上)'}】")

# 🔍 薬の名前入力検索欄
search_query = st.text_input("🔍 薬の名前を入力して検索（例: カロナール錠 500mg）", placeholder="お薬名や規格(mg)を入力すると、その薬を直接絞り込んで表示します")

# 🎛️ 2列配置のチェックボックス方式症状選択
st.subheader("🩺 今のあなたの症状にチェックを入れてください（複数選択可）")
symptom_cols = st.columns(2)
selected_symptoms = []
all_available_symptoms = ["頭痛", "発熱", "鼻炎", "眠気", "喉の痛み", "胃痛", "腹痛", "咳"]

for idx, symptom in enumerate(all_available_symptoms):
    target_col = symptom_cols[idx % 2]
    with target_col:
        if st.checkbox(symptom, key=f"check_{symptom}"):
            selected_symptoms.append(symptom)

# 💡 症状または検索ワード変更時の自動履歴クリア＆1位リスタート回路
if selected_symptoms != st.session_state.last_selected_symptoms or search_query != st.session_state.last_search_query:
    st.session_state.current_page = 0
    st.session_state.last_selected_symptoms = selected_symptoms
    st.session_state.last_search_query = search_query
    st.rerun()

