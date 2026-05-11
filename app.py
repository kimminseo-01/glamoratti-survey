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

# 파트 1 (단일 이미지 S1~S24) 랜덤 리스트
if 'p1_order' not in st.session_state:
    p1_list = [f"S{i}.png" for i in range(1, 25)] 
    random.shuffle(p1_list)
    st.session_state.p1_order = p1_list

# 파트 2 (이미지 쌍 pair) 랜덤 리스트
if 'p2_order' not in st.session_state:
    p2_list = [f"pair{i}.png" for i in range(1, 13)] 
    random.shuffle(p2_list)
    st.session_state.p2_order = p2_list

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return None

# --- 🌟 자동 스크롤 최종 안정화 버전 ---
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

# --- 공통 CSS ---
def apply_common_css():
    st.markdown("""
        <style>
        header {visibility: hidden;}
        .sticky-image { 
            position: fixed; 
            top: 0; 
            left: 0; 
            width: 100%; 
            background-color: white; 
            z-index: 1000; 
            padding: 8px 0; 
            border-bottom: 2px solid #ddd; 
            text-align: center; 
        }
        .sticky-image img {
            max-height: 1200px; 
            width: auto;
            max-width: 100%;
            object-fit: contain;
        }
        .spacer { margin-top: 300px; }
        .section-header { background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-top: 20px; }
        div[data-testid="stButton"] button { height: 40px; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. [1페이지] 인트로 ---
if st.session_state.page == 'intro':
    st.title("1980년대 패션의 재해석 수준에 따른 Glamoratti 아우터의 감성 인지 조사")
    st.write("---")
    st.subheader("실험 안내")
    st.info("""
    본 설문조사는 Glamoratti 패션 트렌드 이미지에 대한 소비자의 감성적 반응을 측정하기 위한 연구용 설문조사입니다.
    - 본 설문조사는 두 단계로 나뉘어 진행됩니다.
    - [1단계] 아우터 이미지를 보고 느껴지는 감성을 평가합니다.
    - [2단계] 두 이미지를 비교하며 수용 의도와 재해석 정도를 평가합니다.
    - 소요 시간: 약 20-30분 내외
    - 모든 응답은 익명으로 처리되며 연구 목적으로만 사용됩니다.
    - 설문조사 참여에 동의한다면 설문 시작하기 버튼을 눌러 설문을 시작해주십시오.
    """)
    st.warning("⚠️ 중간에 브라우저를 새로고침하면 응답이 초기화되니 주의해 주세요.")
    if st.button("설문 시작하기"):
        st.session_state.page = 'demographics'
        st.rerun()

# --- 3. [2페이지] 인구통계학적 설문 ---
elif st.session_state.page == 'demographics':
    st.title("인구통계학적 정보")
    st.write("---")
    gender = st.radio("본 설문조사는 한국 거주 여성을 대상으로 하고 있습니다. 귀하의 성별은 여성입니까? *", ["예", "아니오"], index=None)
    age = st.radio("귀하의 연령은 어떻게 되십니까? (만 나이 기준) *", ["만 19세 ~ 만 29 세", "만 30 세 ~ 만 39 세", "만 40 세 ~ 만 49 세", "만 50 세 ~ 만 59 세", "만 60 이상"], index=None)
    edu = st.radio("귀하의 최종 학력은 무엇입니까? *", ["고등학교 졸업", "대학교 재학", "대학교 졸업", "대학원 재학", "대학원 졸업"], index=None)
    major = st.radio("귀하의 현재 직종 혹은 전공 계열은 무엇입니까? *", ["예술·디자인 계열 (패션, 의류, 시각디자인 등)", "그 외"], index=None)
    spending = st.radio("귀하의 월 평균 의류 지출액은 어느 정도입니까? *", ["5만 원 미만", "5만 원 이상 ~ 10만 원 미만", "10만 원 이상 ~ 20만 원 미만", "20만 원 이상 ~ 30만 원 미만", "30만 원 이상 ~ 50만 원 미만", "50만 원 이상"], index=None)

    if st.button("다음 단계로"):
        if not (gender and age and edu and major and spending):
            st.error("모든 문항에 응답해 주세요.")
        else:
            st.session_state.user_data.update({"성별": gender, "연령": age, "학력": edu, "분야": major, "의류지출": spending})
            st.session_state.page = 'part1_survey'
            st.rerun()

# --- 4. [3페이지] 파트 1: 감성 인지 평가 ---
elif st.session_state.page == 'part1_survey':
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
        cols = st.columns([2.5, 1, 1, 1, 1, 1, 1, 1, 2.5])
        with cols[0]: st.markdown(f'<div style="text-align:right; padding-top:8px;">{l}</div>', unsafe_allow_html=True)
        key_name = f"{current_img_file}_emo{i+1}"
        if key_name not in st.session_state: st.session_state[key_name] = 4
        for score in range(1, 8):
            with cols[score]:
                if st.button(f"{score}", key=f"p1_{idx}_{i}_{score}", use_container_width=True, type="primary" if st.session_state[key_name] == score else "secondary"):
                    st.session_state[key_name] = score
                    st.rerun()
        step_responses[key_name] = st.session_state[key_name]
        with cols[8]: st.markdown(f'<div style="text-align:left; padding-top:8px;">{r}</div>', unsafe_allow_html=True)

    # 🌟 수동 맨 위로 버튼 (최종 안정화 버전)
    components.html("""
    <script>
    function goToTop() {
        window.parent.scrollTo({ top: 0, behavior: 'smooth' });
        const selectors = ['.main', '[data-testid="stAppViewContainer"]', '[data-testid="stMain"]', 'section.main'];
        selectors.forEach(selector => {
            const el = window.parent.document.querySelector(selector);
            if (el) {
                el.scrollTo({ top: 0, behavior: 'smooth' });
                el.scrollTop = 0;
            }
        });
        window.parent.document.documentElement.scrollTop = 0;
        window.parent.document.body.scrollTop = 0;
    }
    </script>
    <div style="margin-top:20px;">
        <button onclick="goToTop()" style="width:100%; padding:14px; background:#F0F2F6; border:1px solid #DAE1E7; border-radius:10px; font-size:16px; font-weight:600; cursor:pointer;">⬆️ 화면 맨 위로</button>
    </div>
    """, height=80)
    
    if st.button("다음 이미지로 ->", use_container_width=True):
        components.html("""
        <script>
        window.parent.scrollTo(0,0);
        const selectors = ['.main', '[data-testid="stAppViewContainer"]', '[data-testid="stMain"]', 'section.main'];
        selectors.forEach(selector => {
            const el = window.parent.document.querySelector(selector);
            if (el) {
                el.scrollTop = 0;
                if (el.scrollTo) { el.scrollTo({top: 0, behavior: 'instant'}); }
            }
        });
        window.parent.document.documentElement.scrollTop = 0;
        window.parent.document.body.scrollTop = 0;
        </script>
        """, height=0)
        st.session_state.all_responses.update(step_responses)
        st.session_state.p1_idx += 1
        if st.session_state.p1_idx >= total_p1:
            st.session_state.page = 'part2_intro'
        import time
        time.sleep(0.15)
        st.rerun()

elif st.session_state.page == 'part2_intro':
    st.title("🎉 파트 1 완료!")
    st.success("단일 이미지 감성 평가가 모두 끝났습니다.")
    st.subheader("[파트 2] 비교 평가 안내")
    st.write("지금부터는 이미지 쌍을 비교하며 우측 이미지에 대한 수용 의도와 재해석 정도를 평가합니다.")
    if st.button("파트 2 시작하기"):
        st.session_state.page = 'part2_survey'
        st.rerun()

elif st.session_state.page == 'part2_survey':
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
        cols = st.columns([2.5, 1, 1, 1, 1, 1, 1, 1, 2.5])
        with cols[0]: st.markdown('<div style="text-align:right; padding-top:8px;">전혀 아니다</div>', unsafe_allow_html=True)
        key_name = f"{current_img_file}_acc{i+1}"
        if key_name not in st.session_state: st.session_state[key_name] = 4
        for score in range(1, 8):
            with cols[score]:
                if st.button(f"{score}", key=f"p2_acc_{idx}_{i}_{score}", use_container_width=True, type="primary" if st.session_state[key_name] == score else "secondary"):
                    st.session_state[key_name] = score
                    st.rerun()
        step_responses[key_name] = st.session_state[key_name]
        with cols[8]: st.markdown('<div style="text-align:left; padding-top:8px;">매우 그렇다</div>', unsafe_allow_html=True)

    st.subheader("3. 재해석 정도 평가")
    re_items = ["실루엣", "색상", "소재", "디테일"]
    for i, item in enumerate(re_items):
        st.write(f"우측 이미지는 좌측에 비해 **{item}**을 상당히 변형하였다.")
        cols = st.columns([2.5, 1, 1, 1, 1, 1, 1, 1, 2.5])
        with cols[0]: st.markdown('<div style="text-align:right; padding-top:8px;">전혀 아니다</div>', unsafe_allow_html=True)
        key_name = f"{current_img_file}_re{i+1}"
        if key_name not in st.session_state: st.session_state[key_name] = 4
        for score in range(1, 8):
            with cols[score]:
                if st.button(f"{score}", key=f"p2_re_{idx}_{i}_{score}", use_container_width=True, type="primary" if st.session_state[key_name] == score else "secondary"):
                    st.session_state[key_name] = score
                    st.rerun()
        step_responses[key_name] = st.session_state[key_name]
        with cols[8]: st.markdown('<div style="text-align:left; padding-top:8px;">매우 그렇다</div>', unsafe_allow_html=True)

    # 🌟 수동 맨 위로 버튼
    components.html("""
    <script>
    function goToTop() {
        window.parent.scrollTo({ top: 0, behavior: 'smooth' });
        const selectors = ['.main', '[data-testid="stAppViewContainer"]', '[data-testid="stMain"]', 'section.main'];
        selectors.forEach(selector => {
            const el = window.parent.document.querySelector(selector);
            if (el) {
                el.scrollTo({ top: 0, behavior: 'smooth' });
                el.scrollTop = 0;
            }
        });
        window.parent.document.documentElement.scrollTop = 0;
        window.parent.document.body.scrollTop = 0;
    }
    </script>
    <div style="margin-top:20px;">
        <button onclick="goToTop()" style="width:100%; padding:14px; background:#F0F2F6; border:1px solid #DAE1E7; border-radius:10px; font-size:16px; font-weight:600; cursor:pointer;">⬆️ 화면 맨 위로</button>
    </div>
    """, height=80)
    
    if idx < total_p2 - 1:
        if st.button("다음 이미지 쌍으로 ->", key="next_pair_btn", use_container_width=True):
            components.html("""
            <script>
            window.parent.scrollTo(0,0);
            const selectors = ['.main', '[data-testid="stAppViewContainer"]', '[data-testid="stMain"]', 'section.main'];
            selectors.forEach(selector => {
                const el = window.parent.document.querySelector(selector);
                if (el) {
                    el.scrollTop = 0;
                    if (el.scrollTo) { el.scrollTo({top: 0, behavior: 'instant'}); }
                }
            });
            window.parent.document.documentElement.scrollTop = 0;
            window.parent.document.body.scrollTop = 0;
            </script>
            """, height=0)
            st.session_state.all_responses.update(step_responses)
            st.session_state.p2_idx += 1
            import time
            time.sleep(0.15)
            st.rerun()
    else:
        if st.button("✅ 모든 설문 완료 및 제출", key="submit_btn", use_container_width=True):
            st.session_state.all_responses.update(step_responses)
            final_data = {**st.session_state.user_data, **st.session_state.all_responses}
            conn = st.connection("gsheets", type=GSheetsConnection)
            spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
            sh = conn.client._client.open_by_url(spreadsheet_url)
            real_sheet_name = sh.get_worksheet(0).title
            try: existing_data = conn.read(worksheet=real_sheet_name, ttl=0)
            except Exception: existing_data = pd.DataFrame()
            updated_df = pd.concat([existing_data, pd.DataFrame([final_data])], ignore_index=True)
            conn.update(worksheet=real_sheet_name, data=updated_df)
            st.success("성공적으로 제출되었습니다!")
            st.balloons()
