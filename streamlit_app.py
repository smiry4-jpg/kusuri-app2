
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

# 💡 症状変更時の自動履歴クリア＆1位リスタート回路
if selected_symptoms != st.session_state.last_selected_symptoms:
    st.session_state.current_page = 0
    st.session_state.seen_eff = set()
    st.session_state.seen_adv = set()
    st.session_state.history_symptoms = set()
    st.session_state.page_history_stack = []
    st.session_state.last_selected_symptoms = selected_symptoms
    st.rerun()

if selected_symptoms:
    for s in selected_symptoms: st.session_state.history_symptoms.add(s)
        
    matched_eff = []
    matched_adv = []
    
    for drug in st.session_state.app_db:
        if is_child and drug["target"] == "adult_only":
            continue
            
        if keyword_count := sum(1 for s in selected_symptoms if s in drug["efficacy"]):
            matched_eff.append({"data": drug, "count": keyword_count})
        if keyword_count_adv := sum(1 for s in selected_symptoms if s in drug["adverse"]):
            matched_adv.append({"data": drug, "count": keyword_count_adv})
                
    matched_eff.sort(key=lambda x: (-x["count"], x["data"]["rank"]))
    matched_adv.sort(key=lambda x: (-x["count"], x["data"]["rank"]))
    
    start_idx = st.session_state.current_page * 3
    end_idx = start_idx + 3
    
    eff_show = matched_eff[start_idx:end_idx]
    shown_eff_names = [item["data"]["name"] for item in eff_show]
    filtered_adv = [item for item in matched_adv if item["data"]["name"] not in shown_eff_names]
    adv_show = filtered_adv[start_idx:end_idx]
    
    # 💻 結果出力
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔵 効率よく『同時に治せる』お薬")
        if eff_show:
            for item in eff_show:
                d = item["data"]
                st.info(f"**{d['name']}** (処方:{d['rank']}位)\n\n📜 効能: {', '.join(d['efficacy'])}")
                
                # 💡 【ログ消滅の修正】1行合体をすべて廃止し、正しい段落へ修正
                if is_premium:
                    st.caption(f"💊 【区分: {d['type']}】")
                    st.caption(f"💡 {d['category']}")
                    
                encoded_name = urllib.parse.quote(d["prefix"])
                amazon_url = f"https://amazon.co.jp{encoded_name}&tag=YOUR_ID-22"
                if is_premium:
                    st.markdown(f"<a href='{amazon_url}' target='_blank' style='color:#00c0f0; text-decoration:none;'>🛒 Amazonで類似市販薬を探す</a>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<a href='{amazon_url}' target='_blank' style='color:#ff4b4b; text-decoration:none;'>🛒 Amazonで類似市販薬を探す（広告）</a>", unsafe_allow_html=True)
        else:
            st.write("該当するお薬はこれ以上ありません。")

    with col2:
        st.subheader("🔴 『副作用で出やすい』お薬")
        if adv_show:
            for item in adv_show:
                d = item["data"]
                st.warning(f"**{d['name']}** (処方:{d['rank']}位)\n\n⚠️ 副作用: {', '.join(d['adverse'])}")
                if is_premium:
                    st.caption(f"💡 {d['category']}")
        else:
            st.write("該当するお薬はこれ以上ありません。")

    st.write("---")
    
    # 🎛️ ボタン制御セクション
    if not is_premium:
        st.error("🔒 **【機能制限】これより下位（4位以降）のお薬は、無料版では非表示になっています。**")
        
    if is_premium:
        # 💡 【ログ消滅の修正】ここも正しく改行して段落の中に文字出力を格納
        st.success(f"🔓 **有料版：全機能解放中** （現在 {start_idx + 1} 〜 {start_idx + len(eff_show)} 位付近を表示中）")
        
        is_next_disabled = (len(matched_eff) <= end_idx)
        if st.button("⏭️ 次の3件のお薬をめくる (次ページへ)", use_container_width=True, disabled=is_next_disabled, key="next_page_btn"):
            st.session_state.current_page += 1
            st.rerun()
            
        is_back_disabled = (st.session_state.current_page <= 0)
        if st.button("⏮️ 1つ前の検索結果に戻る (前ページへ)", use_container_width=True, disabled=is_back_disabled, key="back_page_btn"):
            st.session_state.current_page -= 1
            st.rerun()