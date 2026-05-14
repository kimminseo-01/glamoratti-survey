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

# 🌟 고유 ID (이어하기 번호)
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(random.randint(100000, 999999)) # 6자리 무작위 숫자

# 🌟 A/B 테스트
if 'survey_type' not in st.session_state:
    st.session_state.survey_type = random.choice(['A', 'B']) 

if 'p1_order' not in st.session_state:
    if st.session_state.survey_type == 'A':
        p1_list = [f"S{i}.png" for i in range(1, 13)] 
    else:
        p1_list = [f"S{i}.png" for i in range(13, 25)] 
    random.shuffle(p1_list)
    st.session_state.p1_order = p1_list

if 'p2_order' not in st.session_state:
    if st.session_state.survey_type == 'A':
        p2_list = [f"pair{i}.png" for i in range(1, 7)] 
    else:
        p2_list = [f"pair{i}.png" for i in range(7, 13)] 
    random.shuffle(p2_list)
    st.session_state.p2_order = p2_list

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return None

# --- 🌟 [핵심 기능] 실시간 시트 저장 (자동 저장) ---
def save_progress_to_sheet():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sh = conn.client._client.open_by_url(spreadsheet_url)
        target_sheet_name = f"{st.session_state.survey_type}형"
        
        try: existing_data = conn.read(worksheet=target_sheet_name, ttl=0)
        except Exception: existing_data = pd.DataFrame()

        current_data = {
            "ID": st.session_state.user_id,
            "설문유형": st.session_state.survey_type,
            "현재페이지": st.session_state.page,
            "p1_idx": st.session_state.p1_idx,
            "p2_idx": st.session_state.p2_idx,
            **st.session_state.user_data,
            **st.session_state.all_responses
        }
        
        new_df = pd.DataFrame([current_data])
        
        # ID가 이미 존재하면 덮어쓰기 (Update), 없으면 추가
        if not existing_data.empty and "ID" in existing_data.columns:
            existing_data['ID'] = existing_data['ID'].astype(str)
            if str(st.session_state.user_id) in existing_data['ID'].values:
                existing_data = existing_data[existing_data['ID'] != str(st.session_state.user_id)]
        
        updated_df = pd.concat([existing_data, new_df], ignore_index=True)
        conn.update(worksheet=target_sheet_name, data=updated_df)
    except Exception as e:
        # 시트 오류 시 멈추지 않도록 예외 처리
        pass

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

# --- 자동 스크롤 ---
def auto_scroll_top_script():
    return """
    <script>
    function scrollParent() {
        window.parent.scrollTo(0, 0);
        const selectors = ['.main', '[data-testid="stAppViewContainer"]', '[data-testid="stMain"]', 'section.main'];
        selectors.forEach(selector => {
            const el = window.parent.document.querySelector(selector);
            if (el) {
                el.scrollTop = 0;
                if (el.scrollTo) {
                    el.scrollTo({ top: 0, behavior: 'instant' });
                }
            }
        });
        window.parent.document.documentElement.scrollTop = 0;
        window.parent.document.body.scrollTop = 0;
    }
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
    st.subheader("실험 안내")
    st.info(f"""
    본 설문조사는 Glamoratti 패션 트렌드 이미지에 대한 소비자의 감성적 반응을 측정하기 위한 연구용 설문조사입니다.
    - 본 설문조사는 두 단계로 나뉘어 진행됩니다.
    - [1단계] 아우터 이미지를 보고 느껴지는 감성을 평가합니다.
    - [2단계] 두 이미지를 비교하며 수용 의도와 재해석 정도를 평가합니다.
    - 소요 시간: 약 20-30분 내외
    - 모든 응답은 익명으로 처리되며 연구 목적으로만 사용됩니다.
    - 설문조사 참여에 동의한다면 설문 시작하기 버튼을 눌러 설문을 시작해주십시오.
    
    🔑 **귀하의 고유 참가자 번호는 [{st.session_state.user_id}] 입니다.**
    (중간에 설문이 중단되더라도, 해당 번호로 이어서 진행하실 수 있으니 복사해 두시길 권장합니다.)
    """)
    
    st.warning("⚠️ 본 설문조사는 만 19세 이상 한국 거주 여성을 대상으로 하고 있습니다.")
    st.warning("⚠️ 중간에 브라우저를 새로고침하면 설문이 중단되니 주의해 주세요.")
    st.warning("⚠️ 모든 문항에 대한 응답을 완료하였을 경우, 제출 버튼 클릭 후 제출 완료 문구가 표시될 때까지 기다려주세요.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("처음부터 시작하기", use_container_width=True):
            st.session_state.page = 'demographics'
            st.rerun()
            
    with col2:
        # 🌟 이어하기 복구 로직
        with st.expander("이전에 하던 설문 이어하기"):
            resume_id = st.text_input("고유 참가자 번호 6자리를 입력하세요")
            resume_type = st.radio("배정받으셨던 유형을 선택하세요", ["A형", "B형"], horizontal=True)
            
            if st.button("불러오기"):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
                    sh = conn.client._client.open_by_url(spreadsheet_url)
                    existing_data = conn.read(worksheet=resume_type, ttl=0)
                    
                    # 입력한 ID 검색
                    existing_data['ID'] = existing_data['ID'].astype(str)
                    match = existing_data[existing_data['ID'] == str(resume_id)]
                    
                    if not match.empty:
                        user_record = match.iloc[-1].to_dict() # 가장 최신 기록
                        
                        # 세션 복구
                        st.session_state.user_id = user_record.get('ID')
                        st.session_state.survey_type = user_record.get('설문유형')
                        st.session_state.page = user_record.get('현재페이지')
                        st.session_state.p1_idx = int(user_record.get('p1_idx', 0))
                        st.session_state.p2_idx = int(user_record.get('p2_idx', 0))
                        
                        # 유저 데이터 및 이전 응답 복구 (기본 정보 컬럼 제외)
                        exclude_keys = ['ID', '설문유형', '현재페이지', 'p1_idx', 'p2_idx']
                        for k, v in user_record.items():
                            if k not in exclude_keys and pd.notna(v):
                                if k in ["성별", "연령", "학력", "분야", "의류지출"]:
                                    st.session_state.user_data[k] = v
                                else:
                                    st.session_state.all_responses[k] = v
                                    # 문항 값도 세션으로 복구 (슬라이더 오류 방지)
                                    st.session_state[k] = int(v) 

                        st.success("데이터를 성공적으로 불러왔습니다!")
                        import time; time.sleep(1)
                        st.rerun()
                    else:
                        st.error("해당 번호의 기록을 찾을 수 없습니다.")
                except Exception as e:
                    st.error("불러오는 중 오류가 발생했습니다. 시트 설정을 확인하세요.")


# --- 3. [2페이지] 인구통계학적 설문 ---
elif st.session_state.page == 'demographics':
    prevent_refresh_script()
    st.title("인구통계학적 정보")
    st.write("---")
    gender = st.radio("귀하의 성별은 여성입니까? *", ["예", "아니오"], index=None)
    age = st.radio("귀하의 연령은 어떻게 되십니까? (만 나이 기준) *", ["만 19세 ~ 만 29 세", "만 30 세 ~ 만 39 세", "만 40 세 ~ 만 49 세", "만 50 세 ~ 만 59 세", "만 60 이상"], index=None)
    edu = st.radio("귀하의 최종 학력은 무엇입니까? *", ["고등학교 졸업", "대학교 재학", "대학교 졸업", "대학원 재학", "대학원 졸업"], index=None)
    major = st.radio("귀하의 현재 직종 혹은 전공 계열은 무엇입니까? *", ["예술·디자인 계열 (패션, 의류, 시각디자인 등)", "그 외"], index=None)
    spending = st.radio("귀하의 월 평균 의류 지출액은 어느 정도입니까? *", ["5만 원 미만", "5만 원 이상 ~ 10만 원 미만", "10만 원 이상 ~ 20만 원 미만", "20만 원 이상 ~ 30만 원 미만", "30만 원 이상 ~ 50만 원 미만", "50만 원 이상"], index=None)

    if st.button("다음 단계로"):
        if not (gender and age and edu and major and spending):
            st.error("모든 문항에 응답해 주세요.")
        else:
            st.session_state.user_data.update({"성별": gender, "연령": age, "학력": edu, "분야": major, "의류지출": spending})
            st.session_state.page = 'part1_intro'
            with st.spinner("저장 중..."): save_progress_to_sheet() # 🌟 자동 저장
            st.rerun()

# --- [새로 추가된 페이지] 파트 1 중간 안내 ---
elif st.session_state.page == 'part1_intro':
    prevent_refresh_script()
    components.html(auto_scroll_top_script(), height=0)
    st.title("📝 [파트 1] 감성 평가 안내")
    st.write("---")
    st.info("""
    지금부터 **[파트 1] 감성 평가**가 시작됩니다.
    
    - 지금부터 여성 아우터 이미지를 순차적으로 보여드립니다. 각 이미지를 충분히 살펴보신 후, 해당 아우터에 대해 느끼시는 감성에 대해 응답해 주십시오.
    - 정답이 있는 것이 아니므로, 직관적으로 느끼신 대로 응답해 주시면 됩니다.
    - 자극물 제시 순서는 참여자별로 무작위화 합니다.
    """)
    st.write("")
    if st.button("파트 1 시작하기", use_container_width=True):
        st.session_state.page = 'part1_survey'
        st.rerun()

# --- 4. [3페이지] 파트 1: 감성 인지 평가 ---
elif st.session_state.page == 'part1_survey':
    prevent_refresh_script()
    idx = st.session_state.p1_idx
    apply_common_css()
    components.html(auto_scroll_top_script(), height=0)
    
    total_p1 = len(st.session_state.p1_order)
    current_img_file = st.session_state.p1_order[idx]
    img_b64 = get_image_base64(current_img_file)
    img_src = f"data:image/png;base64,{img_b64}" if img_b64 else ""

    st.markdown(f'<div class="sticky-image"><p style="margin:0; font-size: 0.9em; font-weight:bold;">[파트 1] 감성 평가 ({idx+1}/{total_p1})</p><img src="{img_src}"><br><small style="color:#999;">{current_img_file}</small></div>', unsafe_allow_html=True)
    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
    
    step_responses = {}
    adj_pairs = [("촌스럽다", "세련되다"), ("소박하다", "고급스럽다"), ("수수하다", "화려하다"), ("순수하다", "섹시하다"), ("투박하다", "우아하다"), ("단조롭다", "드라마틱하다"), ("온화하다", "강렬하다"), ("여리다", "단단하다"), ("부드럽다", "날카롭다"), ("복잡하다", "간결하다"), ("밋밋하다", "화사하다")]
    st.subheader("1. 감성 평가")

    for i, (l, r) in enumerate(adj_pairs):
        key_name = f"{current_img_file}_emo{i+1}"
        center_col = st.columns([1,6,1])[1]
        
        with center_col:
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; font-size:15px; font-weight:500; margin-bottom:-10px;">
                    <span>{l}</span><span>{r}</span>
                </div>
                """, unsafe_allow_html=True
            )
            score = st.slider("", min_value=1, max_value=7, value=st.session_state.get(key_name, 4), step=1, key=key_name, label_visibility="collapsed")
            step_responses[key_name] = score
        st.write("")

    components.html("""
    <script>
    function goToTop() {
        window.parent.scrollTo({ top: 0, behavior: 'smooth' });
        const selectors = ['.main', '[data-testid="stAppViewContainer"]', '[data-testid="stMain"]', 'section.main'];
        selectors.forEach(selector => {
            const el = window.parent.document.querySelector(selector);
            if (el) { el.scrollTo({ top: 0, behavior: 'smooth' }); el.scrollTop = 0; }
        });
        window.parent.document.documentElement.scrollTop = 0; window.parent.document.body.scrollTop = 0;
    }
    </script>
    <div style="margin-top:20px;"><button onclick="goToTop()" style="width:100%; padding:14px; background:#F0F2F6; border:1px solid #DAE1E7; border-radius:10px; font-size:16px; font-weight:600; cursor:pointer;">⬆️ 화면 맨 위로</button></div>
    """, height=80)
    
    if st.button("다음 이미지로 ->", use_container_width=True):
        st.session_state.all_responses.update(step_responses)
        st.session_state.p1_idx += 1
        
        if st.session_state.p1_idx >= total_p1:
            st.session_state.page = 'part2_intro'
            
        with st.spinner("저장 중..."): save_progress_to_sheet() # 🌟 실시간 자동 저장
        import time; time.sleep(0.15)
        st.rerun()

# --- 5. [4페이지] 파트 2 중간 안내 ---
elif st.session_state.page == 'part2_intro':
    prevent_refresh_script()
    components.html(auto_scroll_top_script(), height=0)
    st.title("🎉 파트 1 완료!")
    st.success("단일 이미지 감성 평가가 모두 끝났습니다. 수고하셨습니다!")
    st.write("---")
    st.subheader("📝 [파트 2] 비교 평가 안내")
    st.info("""
    지금부터는 **[파트 2] 비교 평가**가 시작됩니다.
    - 지금부터는 1980년대 아우터 이미지(좌측)와 이를 재해석한 현대의 아우터 이미지(우측)가 쌍으로 제시됩니다.
    - 좌측 이미지와 비교하여 **우측 이미지**에 대한 수용 의도와 재해석 정도를 평가해 주시면 됩니다.
    - 자극물 제시 순서는 참여자별로 무작위화 합니다. 
    """)
    st.write("")
    if st.button("파트 2 시작하기", use_container_width=True):
        st.session_state.page = 'part2_survey'
        st.rerun()

# --- 6. [5페이지] 파트 2: 비교 평가 ---
elif st.session_state.page == 'part2_survey':
    prevent_refresh_script()
    idx = st.session_state.p2_idx
    apply_common_css()
    components.html(auto_scroll_top_script(), height=0)
    
    total_p2 = len(st.session_state.p2_order)
    current_img_file = st.session_state.p2_order[idx]
    img_b64 = get_image_base64(current_img_file)
    img_src = f"data:image/png;base64,{img_b64}" if img_b64 else ""

    st.markdown(f'<div class="sticky-image"><p style="margin:0; font-size: 0.9em; font-weight:bold;">[파트 2] 비교 평가 ({idx+1}/{total_p2})</p><img src="{img_src}" width="480"><br><small style="color:#999;">{current_img_file}</small></div>', unsafe_allow_html=True)
    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
    
    step_responses = {}
    st.subheader("2. 수용 의도 평가")
    acc_items = ["수용할 가능성", "구매할 의향", "추천할 의향"]
    for i, item in enumerate(acc_items):
        st.write(f"나는 **우측 이미지**의 아우터를 **{item}**이 높다.")
        l, r = "전혀 아니다", "매우 그렇다"
        key_name = f"{current_img_file}_acc{i+1}"
        center_col = st.columns([1,6,1])[1]
        with center_col:
            st.markdown(f'<div style="display:flex; justify-content:space-between; font-size:15px; font-weight:500; margin-bottom:-10px;"><span>{l}</span><span>{r}</span></div>', unsafe_allow_html=True)
            score = st.slider("", min_value=1, max_value=7, value=st.session_state.get(key_name, 4), step=1, key=key_name, label_visibility="collapsed")
            step_responses[key_name] = score
        st.write("")

    st.subheader("3. 재해석 정도 평가")
    re_items = ["실루엣", "색상", "소재", "디테일"]
    for i, item in enumerate(re_items):
        st.write(f"우측 이미지는 좌측에 비해 **{item}**을 상당히 변형하였다.")
        l, r = "전혀 아니다", "매우 그렇다"
        key_name = f"{current_img_file}_re{i+1}"
        center_col = st.columns([1,6,1])[1]
        with center_col:
            st.markdown(f'<div style="display:flex; justify-content:space-between; font-size:15px; font-weight:500; margin-bottom:-10px;"><span>{l}</span><span>{r}</span></div>', unsafe_allow_html=True)
            score = st.slider("", min_value=1, max_value=7, value=st.session_state.get(key_name, 4), step=1, key=key_name, label_visibility="collapsed")
            step_responses[key_name] = score
        st.write("")

    components.html("""
    <script>
    function goToTop() {
        window.parent.scrollTo({ top: 0, behavior: 'smooth' });
        const selectors = ['.main', '[data-testid="stAppViewContainer"]', '[data-testid="stMain"]', 'section.main'];
        selectors.forEach(selector => {
            const el = window.parent.document.querySelector(selector);
            if (el) { el.scrollTo({ top: 0, behavior: 'smooth' }); el.scrollTop = 0; }
        });
        window.parent.document.documentElement.scrollTop = 0; window.parent.document.body.scrollTop = 0;
    }
    </script>
    <div style="margin-top:20px;"><button onclick="goToTop()" style="width:100%; padding:14px; background:#F0F2F6; border:1px solid #DAE1E7; border-radius:10px; font-size:16px; font-weight:600; cursor:pointer;">⬆️ 화면 맨 위로</button></div>
    """, height=80)
    
    if idx < total_p2 - 1:
        if st.button("다음 이미지 쌍으로 ->", key="next_pair_btn", use_container_width=True):
            st.session_state.all_responses.update(step_responses)
            st.session_state.p2_idx += 1
            with st.spinner("저장 중..."): save_progress_to_sheet() # 🌟 실시간 자동 저장
            import time; time.sleep(0.15)
            st.rerun()
    else:
        if st.button("✅ 모든 설문 완료 및 제출", key="submit_btn", use_container_width=True):
            st.session_state.all_responses.update(step_responses)
            st.session_state.page = "final"
            with st.spinner("최종 제출 중..."): save_progress_to_sheet()
            st.success("성공적으로 제출되었습니다! 설문에 참여해주셔서 감사합니다!")
            st.balloons()
