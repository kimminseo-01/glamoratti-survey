import streamlit as st
import base64
import random  
import streamlit.components.v1 as components
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. 초기 설정 및 세션 상태 관리 ---
if 'page' not in st.session_state:
    st.session_state.page = 'intro'
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'all_responses' not in st.session_state:
    st.session_state.all_responses = {}

if 'p1_idx' not in st.session_state:
    st.session_state.p1_idx = 0
if 'p2_idx' not in st.session_state:
    st.session_state.p2_idx = 0

# 🌟 고유 ID (이어하기 번호) - 세션 내 1회만 생성
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(random.randint(100000, 999999))

# 🌟 [순서 고정] 참가자 번호를 시드로 사용하여 항상 동일한 랜덤 순서 생성
rng = random.Random(int(st.session_state.user_id))

# 🌟 A/B 테스트 (시드 기반 고정)
if 'survey_type' not in st.session_state:
    st.session_state.survey_type = rng.choice(['A', 'B']) 

if 'p1_order' not in st.session_state:
    if st.session_state.survey_type == 'A':
        p1_list = [f"S{i}.png" for i in range(1, 13)] 
    else:
        p1_list = [f"S{i}.png" for i in range(13, 25)] 
    rng.shuffle(p1_list) # 🌟 시드 기반 셔플
    st.session_state.p1_order = p1_list

if 'p2_order' not in st.session_state:
    if st.session_state.survey_type == 'A':
        p2_list = [f"pair{i}.png" for i in range(1, 7)] 
    else:
        p2_list = [f"pair{i}.png" for i in range(7, 13)] 
    rng.shuffle(p2_list) # 🌟 시드 기반 셔플
    st.session_state.p2_order = p2_list

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return None

# --- 🌟 실시간 시트 저장 (미리 써둔 헤더 완벽 보존 버전) ---
def save_progress_to_sheet():
    try:
        # 스트림릿 캐시를 비워야 최신 데이터를 쓰고 읽을 수 있습니다.
        st.cache_data.clear()
        conn = st.connection("gsheets", type=GSheetsConnection)
        target_sheet_name = f"{st.session_state.survey_type}형"
        
        # 1. 기존 데이터 읽기 (ttl=0으로 캐시 없이 읽기)
        try:
            existing_data = conn.read(worksheet=target_sheet_name, ttl=0)
            if existing_data is None:
                return # 시트를 못 읽어오면 안전을 위해 중단
            existing_data = existing_data.copy()
        except Exception:
            return # 통신 오류 시 중단

        # 2. 현재 응답 데이터 정리
        current_data = {
            "ID": str(st.session_state.user_id),
            "설문유형": st.session_state.survey_type,
            "현재페이지": st.session_state.page,
            "p1_idx": st.session_state.p1_idx,
            "p2_idx": st.session_state.p2_idx,
            **st.session_state.user_data,
            **st.session_state.all_responses
        }
        
        new_row = pd.DataFrame([current_data])
        
        # 3. 중복 확인 및 업데이트/추가 로직
        if "ID" in existing_data.columns:
            # ID 컬럼의 소수점(.0) 제거 후 문자열 비교
            existing_data['ID_match'] = existing_data['ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            target_id = str(st.session_state.user_id).strip()
            
            if target_id in existing_data['ID_match'].values:
                # 🌟 기존 참가자: 해당 행을 찾아 내용만 교체 (덮어쓰기)
                idx = existing_data[existing_data['ID_match'] == target_id].index[-1]
                for col in new_row.columns:
                    if col not in existing_data.columns:
                        existing_data[col] = ""
                    existing_data.at[idx, col] = new_row.iloc[0][col]
                updated_df = existing_data.drop(columns=['ID_match'])
            else:
                # 🌟 새 참가자: 기존의 184개 컬럼 순서를 강제로 유지하면서 Append
                original_cols = existing_data.drop(columns=['ID_match']).columns.tolist()
                updated_df = pd.concat([existing_data.drop(columns=['ID_match']), new_row], ignore_index=True)
                
                # 혹시나 순서가 섞이지 않도록 원래 헤더 순서대로 재정렬
                all_cols = original_cols + [c for c in updated_df.columns if c not in original_cols]
                updated_df = updated_df[all_cols]
        else:
            # 시트가 완전히 비어있거나 ID 컬럼이 없는 경우
            updated_df = new_row
            
        # 4. 최종 시트 업데이트 (NaN 제거)
        updated_df = updated_df.fillna("")
        conn.update(worksheet=target_sheet_name, data=updated_df)
        
    except Exception as e:
        pass # 에러로 설문이 멈추지 않게 처리

# --- 새로고침 방지 ---
def prevent_refresh_script():
    components.html("""
    <script>
    window.parent.addEventListener("beforeunload", function (e) {
        e.preventDefault();
        e.returnValue = '';
    });
    </script>
    """, height=0)

# --- 자동 스크롤 기능 ---
def auto_scroll_top_script(key=""):
    return f"""
    <div id="scroll_trigger_{key}"></div>
    <script>
    function scrollParent() {{
        window.parent.scrollTo(0, 0);
        const selectors = ['.main', '[data-testid="stAppViewContainer"]', '[data-testid="stMain"]', 'section.main'];
        selectors.forEach(selector => {{
            const el = window.parent.document.querySelector(selector);
            if (el) {{
                el.scrollTop = 0;
                if (el.scrollTo) {{
                    el.scrollTo({{ top: 0, behavior: 'instant' }});
                }}
            }}
        }});
        window.parent.document.documentElement.scrollTop = 0;
        window.parent.document.body.scrollTop = 0;
    }}
    setTimeout(scrollParent, 50);
    setTimeout(scrollParent, 150);
    setTimeout(scrollParent, 300);
    </script>
    """

def apply_common_css():
    st.markdown("""
        <style>
        header {visibility: hidden;}
        .sticky-image { position: fixed; top: 0; left: 0; width: 100%; background-color: white; z-index: 1000; padding: 8px 0; border-bottom: 2px solid #ddd; text-align: center; }
        .sticky-image img { max-height: 1200px; width: auto; max-width: 100%; object-fit: contain; }
        .spacer { margin-top: 300px; }
        .section-header { background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-top: 20px; }
        div[data-testid="stButton"] button { height: 40px; }
        .stSlider [data-baseweb="slider"] > div > div { background: #D9D9D9 !important; }
        .stSlider [data-baseweb="slider"] > div > div > div { background: #D9D9D9 !important; }
        .stSlider [role="slider"] { background-color: white !important; border: 2px solid #999 !important; box-shadow: none !important; }
        .stSlider div[data-baseweb="slider"] + div { display: none; }
        </style>
    """, unsafe_allow_html=True)


# --- 2. [1페이지] 인트로 및 이어하기 로직 ---
if st.session_state.page == 'intro':
    st.title("1980년대 패션의 재해석 수준에 따른 Glamoratti 아우터의 감성 인지 조사")
    st.write("---")
    
    # 🌟 [새로 추가된 상세 안내문]
    st.markdown("""
    **안녕하세요. 본 설문조사에 참여해 주셔서 진심으로 감사드립니다.**
    
    본 설문은 2026년 주요 패션 트렌드인 'Glamoratti(글래모라티)'에 대한 소비자의 감성적 반응과 수용 의도를 조사하기 위해 설계되었습니다.

     ### 본 연구의 목적
    본 연구는 이러한 Glamoratti 트렌드 여성 아우터(재킷, 코트, 퍼 아우터 등)를 대상으로, 1980년대 패션 요소가 어느 정도 수준으로 재해석되었는지에 따라 소비자가 느끼는 감성적 인상과 수용 의도(착용, 구매, 추천 의도)가 어떻게 달라지는지를 탐구합니다.
    
    설문에서는 1980년대 원형 아우터 이미지와 이를 현대적으로 재해석한 아우터 이미지를 함께 보여드린 후, 현대 아우터에 대해 느끼시는 감성적 인상과 수용 의도를 여쭈어볼 것입니다.
    
    ### Glamoratti(글래모라티)란?
    패션 트렌드는 직선적으로 진행되지 않고, 과거의 스타일이 일정한 주기를 두고 다시 부상하는 순환적 특성을 지니고 있습니다. 2026년, 그 순환의 흐름 속에서 주목받고 있는 트렌드가 바로 Glamoratti입니다.
    
    Glamoratti는 1980년대 파워 드레싱(Power Dressing)의 핵심 미학을 현대적으로 재해석한 트렌드로, 글로벌 트렌드 플랫폼 Pinterest가 연례 보고서 'Pinterest Predicts 2026'을 통해 올해의 대표 신흥 트렌드로 선정하였습니다. 이 트렌드는 수 시즌에 걸친 미니멀리즘 기조에 대한 반동으로서, 보다 대담하고 존재감 있는 스타일의 귀환을 의미합니다.
    
    **Glamoratti의 주요 특징은 다음과 같습니다.**
    - **조각적인 숄더 라인:** 1980년대를 상징하는 강조된 어깨 구조의 현대적 변형
    - **구조적 테일러링:** 공간을 점유하는 파워풀한 수트와 재킷
    - **드라마틱한 디테일:** 퍼널 넥라인, 볼륨감 있는 소매 등 극적인 조형 요소
    - **강렬한 소재와 컬러:** 메탈릭 소재, 골드 액세서리, 과감한 색채 활용
    
    즉, Glamoratti는 1980년대 여성들이 전문직 사회 진출 과정에서 권위와 자신감을 표현하기 위해 활용했던 패션 언어를, 2026년의 감각으로 다시 불러낸 트렌드입니다.
    
    ### 설문 참여 안내
    - **소요 시간:** 약 15~20분
    - **참여 대상:** 한국 거주 여성
    - **설문 구성:** 인구통계 정보 → 자극물별 감성 평가 → 자극물별 수용 의도 및 재해석 정도 인식 확인
    
    본 설문에는 정답이 없으며, 이미지를 보시고 직관적으로 느끼시는 그대로 응답해 주시면 됩니다. 수집된 모든 응답은 익명으로 처리되며, 연구 목적 이외에는 일절 사용되지 않습니다. 설문 참여는 자발적이며, 원하실 경우 언제든지 참여를 중단하실 수 있습니다.
    
    여러분의 소중한 응답은 패션 트렌드의 순환적 재해석에 대한 소비자 반응을 이해하는 데 매우 귀중한 자료가 될 것입니다. 다시 한번 참여에 감사드리며, 궁금한 사항이 있으시면 아래 연락처로 문의해 주시기 바랍니다.
    
    - **연구팀:** 김민서, 전지영, 허지원, 허주원, Paulina Tjandrawibawa
    - **연락처:** huzzi@yonsei.ac.kr
    - **소속:** 연세대학교 통합디자인학과, 의류환경학과
    """)
    
    st.info(f"""
    🔑 **귀하의 고유 참가자 번호는 [{st.session_state.user_id}] 입니다.**
    (중간에 설문이 중단되더라도, 해당 번호로 이어서 진행하실 수 있으니 복사해 두시길 권장합니다.)
    """)
    
    st.warning("⚠️ 중간에 브라우저를 새로고침하면 설문이 중단되니 주의해 주세요.")
    st.warning("⚠️ 모든 문항에 대한 응답을 완료하였을 경우, 제출 버튼 클릭 후 제출 완료 문구가 표시될 때까지 기다려주세요.")
    
    st.write("---")
    
    # 🌟 [참여 동의 로직 추가]
    consent = st.radio(
        "본 설문조사에 자발적으로 참여하는 것에 동의하십니까?", 
        ["예, 동의합니다 (설문 시작)", "아니요, 동의하지 않습니다 (설문 종료)"], 
        index=0
    )
    
    if consent == "아니요, 동의하지 않습니다 (설문 종료)":
        st.error("설문 참여에 동의하지 않으셨습니다. 창을 닫아 설문을 종료해 주시기 바랍니다. 감사합니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        # 동의했을 때만 버튼 활성화
        if consent == "예, 동의합니다 (설문 시작)":
            if st.button("처음부터 시작하기", use_container_width=True):
                st.session_state.page = 'demographics'
                st.rerun()
        else:
            st.button("처음부터 시작하기", use_container_width=True, disabled=True)
            
    with col2:
        with st.expander("이전에 하던 설문 이어하기"):
            resume_id = st.text_input("고유 참가자 번호 6자리를 입력하세요").strip()
            
            if st.button("불러오기"):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    match = pd.DataFrame()
                    found_type = ""
                    
                    for s_type in ["A형", "B형"]:
                        try:
                            existing_data = conn.read(worksheet=s_type, ttl=0)
                            if not existing_data.empty and "ID" in existing_data.columns:
                                existing_data['ID_clean'] = existing_data['ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                                temp_match = existing_data[existing_data['ID_clean'] == resume_id]
                                if not temp_match.empty:
                                    match = temp_match
                                    found_type = s_type
                                    break
                        except Exception:
                            continue
                    
                    if not match.empty:
                        user_record = match.iloc[-1].to_dict()
                        st.session_state.user_id = str(user_record.get('ID')).replace('.0', '').strip()
                        st.session_state.survey_type = user_record.get('설문유형')
                        st.session_state.page = user_record.get('현재페이지')
                        st.session_state.p1_idx = int(user_record.get('p1_idx', 0))
                        st.session_state.p2_idx = int(user_record.get('p2_idx', 0))
                        
                        # 🌟 이어하기 시 랜덤 시드 동기화 (이미지 순서 복원)
                        resumed_rng = random.Random(int(st.session_state.user_id))
                        _ = resumed_rng.choice(['A', 'B']) # 1회 차감
                        
                        if st.session_state.survey_type == 'A':
                            resumed_p1 = [f"S{i}.png" for i in range(1, 13)]
                            resumed_p2 = [f"pair{i}.png" for i in range(1, 7)]
                        else:
                            resumed_p1 = [f"S{i}.png" for i in range(13, 25)]
                            resumed_p2 = [f"pair{i}.png" for i in range(7, 13)]
                        
                        resumed_rng.shuffle(resumed_p1)
                        resumed_rng.shuffle(resumed_p2)
                        st.session_state.p1_order = resumed_p1
                        st.session_state.p2_order = resumed_p2

                        exclude_keys = ['ID', '설문유형', '현재페이지', 'p1_idx', 'p2_idx', 'ID_clean']
                        for k, v in user_record.items():
                            if k not in exclude_keys and pd.notna(v):
                                if k in ["성별", "연령", "학력", "분야", "의류지출"]:
                                    st.session_state.user_data[k] = v
                                else:
                                    st.session_state.all_responses[k] = v
                                    # 슬라이더 값 복원
                                    try: st.session_state[k] = int(float(v))
                                    except: st.session_state[k] = v

                        st.success(f"데이터를 성공적으로 불러왔습니다! ({found_type})")
                        import time; time.sleep(1)
                        st.rerun()
                    else:
                        st.error("해당 번호의 기록을 찾을 수 없습니다.")
                except Exception as e:
                    st.error("불러오는 중 오류가 발생했습니다.")

# --- 3. [2페이지] 인구통계학적 설문 ---
elif st.session_state.page == 'demographics':
    prevent_refresh_script()
    components.html(auto_scroll_top_script("demographics"), height=0)
    st.title("인구통계학적 정보")
    st.write("---")
    gender = st.radio("귀하의 성별은 여성입니까? *", ["예", "아니오"], index=None)
    age = st.radio("귀하의 연령은 어떻게 되십니까? (만 나이 기준) *", ["만 19세 ~ 만 29 세", "만 30 세 ~ 만 39 세", "만 40 세 ~ 만 49 세", "만 50 세 ~ 만 59 세", "만 60 이상"], index=None)
    edu = st.radio("귀하의 최종 학력은 무엇입니까? *", ["고등학교 졸업", "대학교 재학", "대학교 졸업", "대학원 재학", "대학원 졸업"], index=None)
    major = st.radio("귀하의 현재 직종 혹은 전공 계열은 무엇입니까? *", ["예술·디자인 계열 (패션, 의류, 시각디자인 등)", "그 외"], index=None)
    spending = st.radio("귀하의 평소 월 평균 의류 지출액은 어느 정도입니까? *", ["5만 원 미만", "5만 원 이상 ~ 10만 원 미만", "10만 원 이상 ~ 20만 원 미만", "20만 원 이상 ~ 30만 원 미만", "30만 원 이상 ~ 50만 원 미만", "50만 원 이상"], index=None)

    if st.button("다음 단계로"):
        if not (gender and age and edu and major and spending):
            st.error("모든 문항에 응답해 주세요.")
        else:
            st.session_state.user_data.update({"성별": gender, "연령": age, "학력": edu, "분야": major, "의류지출": spending})
            st.session_state.page = 'part1_intro'
            with st.spinner("저장 중..."): save_progress_to_sheet()
            st.rerun()

# --- [파트 1 중간 안내] ---
elif st.session_state.page == 'part1_intro':
    prevent_refresh_script()
    components.html(auto_scroll_top_script("part1_intro"), height=0)
    st.title("📝 [파트 1] 감성 평가 안내")
    st.write("---")
    st.info("""
    지금부터 **[파트 1] 감성 평가**가 시작됩니다.
    - 지금부터 여성 아우터 이미지를 순차적으로 보여드립니다. 각 이미지를 충분히 살펴보신 후, 해당 아우터에 대해 느껴지는 감성을 응답해 주십시오.
    - 정답이 있는 것이 아니므로, 직관적으로 느끼신 대로 응답해 주시면 됩니다.
    - 자극물 제시 순서는 참여자별로 무작위화 합니다.
    """)
    if st.button("파트 1 시작하기", use_container_width=True):
        st.session_state.page = 'part1_survey'
        st.rerun()

# --- 4. [3페이지] 파트 1: 감성 평가 ---
elif st.session_state.page == 'part1_survey':
    prevent_refresh_script()
    idx = st.session_state.p1_idx
    apply_common_css()
    components.html(auto_scroll_top_script(f"p1_{idx}"), height=0)
    
    total_p1 = len(st.session_state.p1_order)
    current_img_file = st.session_state.p1_order[idx]
    img_b64 = get_image_base64(current_img_file)
    img_src = f"data:image/png;base64,{img_b64}" if img_b64 else ""

    st.markdown(f'<div class="sticky-image"><p style="margin:0; font-size: 0.9em; font-weight:bold;">[파트 1] 감성 평가 ({idx+1}/{total_p1})</p><img src="{img_src}"><br><small style="color:#999;">{current_img_file}</small></div>', unsafe_allow_html=True)
    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
    
    adj_pairs = [("촌스럽다", "세련되다"), ("소박하다", "고급스럽다"), ("수수하다", "화려하다"), ("순수하다", "섹시하다"), ("투박하다", "우아하다"), ("단조롭다", "드라마틱하다"), ("온화하다", "강렬하다"), ("여리다", "단단하다"), ("부드럽다", "날카롭다"), ("복잡하다", "간결하다"), ("밋밋하다", "화사하다")]
    st.subheader("1. 감성 평가")

    step_responses = {}
    for i, (l, r) in enumerate(adj_pairs):
        key_name = f"{current_img_file}_emo{i+1}"
        center_col = st.columns([1,6,1])[1]
        with center_col:
            st.markdown(f'<div style="display:flex; justify-content:space-between; font-size:15px; font-weight:500; margin-bottom:-10px;"><span>{l}</span><span>{r}</span></div>', unsafe_allow_html=True)
            score = st.slider("", min_value=1, max_value=7, value=st.session_state.get(key_name, 4), step=1, key=key_name, label_visibility="collapsed")
            step_responses[key_name] = score
        st.write("")

    if st.button("다음 이미지로 ->", use_container_width=True):
        st.session_state.all_responses.update(step_responses)
        st.session_state.p1_idx += 1
        if st.session_state.p1_idx >= total_p1: st.session_state.page = 'part2_intro'
        with st.spinner("저장 중..."): save_progress_to_sheet()
        import time; time.sleep(0.15)
        st.rerun()

# --- 5. [4페이지] 파트 2 중간 안내 ---
elif st.session_state.page == 'part2_intro':
    prevent_refresh_script()
    components.html(auto_scroll_top_script("part2_intro"), height=0)
    st.title("🎉 파트 1 완료!")
    st.subheader("📝 [파트 2] 비교 평가 안내")
    st.info("""
    지금부터는 **[파트 2] 비교 평가**가 시작됩니다.
    - 지금부터는 1980년대 아우터 이미지(좌측)와 이를 재해석한 현대의 아우터 이미지(우측)가 쌍으로 제시됩니다.
    - 좌측 이미지와 비교하여 **우측 이미지**에 대한 수용 의도와 재해석 정도를 평가해 주시면 됩니다.
    - 자극물 제시 순서는 참여자별로 무작위화 합니다. 
    """)
    if st.button("파트 2 시작하기", use_container_width=True):
        st.session_state.page = 'part2_survey'
        st.rerun()

# --- 6. [5페이지] 파트 2: 비교 평가 ---
elif st.session_state.page == 'part2_survey':
    prevent_refresh_script()
    idx = st.session_state.p2_idx
    apply_common_css()
    components.html(auto_scroll_top_script(f"p2_{idx}"), height=0)
    
    total_p2 = len(st.session_state.p2_order)
    current_img_file = st.session_state.p2_order[idx]
    img_b64 = get_image_base64(current_img_file)
    img_src = f"data:image/png;base64,{img_b64}" if img_b64 else ""

    st.markdown(f'<div class="sticky-image"><p style="margin:0; font-size: 0.9em; font-weight:bold;">[파트 2] 비교 평가 ({idx+1}/{total_p2})</p><img src="{img_src}" width="480"><br><small style="color:#999;">{current_img_file}</small></div>', unsafe_allow_html=True)
    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
    
    step_responses = {}
    st.subheader("2. 수용 의도 평가")
    for i, item in enumerate(["수용할 가능성", "구매할 의향", "추천할 의향"]):
        st.write(f"나는 **우측 이미지**의 아우터를 **{item}**이 높다.")
        key_name = f"{current_img_file}_acc{i+1}"
        center_col = st.columns([1,6,1])[1]
        with center_col:
            st.markdown('<div style="display:flex; justify-content:space-between; font-size:15px; font-weight:500; margin-bottom:-10px;"><span>전혀 아니다</span><span>매우 그렇다</span></div>', unsafe_allow_html=True)
            score = st.slider("", min_value=1, max_value=7, value=st.session_state.get(key_name, 4), step=1, key=key_name, label_visibility="collapsed")
            step_responses[key_name] = score
        st.write("")

    st.subheader("3. 재해석 정도 평가")
    for i, item in enumerate(["실루엣", "색상", "소재", "디테일"]):
        st.write(f"우측 이미지는 좌측에 비해 **{item}**을 상당히 변형하였다.")
        key_name = f"{current_img_file}_re{i+1}"
        center_col = st.columns([1,6,1])[1]
        with center_col:
            st.markdown('<div style="display:flex; justify-content:space-between; font-size:15px; font-weight:500; margin-bottom:-10px;"><span>전혀 아니다</span><span>매우 그렇다</span></div>', unsafe_allow_html=True)
            score = st.slider("", min_value=1, max_value=7, value=st.session_state.get(key_name, 4), step=1, key=key_name, label_visibility="collapsed")
            step_responses[key_name] = score
        st.write("")

    if idx < total_p2 - 1:
        if st.button("다음 이미지 쌍으로 ->", use_container_width=True):
            st.session_state.all_responses.update(step_responses)
            st.session_state.p2_idx += 1
            with st.spinner("저장 중..."): save_progress_to_sheet()
            st.rerun()
    else:
        if st.button("✅ 모든 설문 완료 및 제출", use_container_width=True):
            st.session_state.all_responses.update(step_responses)
            st.session_state.page = "final"
            with st.spinner("최종 제출 중..."): save_progress_to_sheet()
            st.success("성공적으로 제출되었습니다! 감사합니다!")
            st.balloons()
