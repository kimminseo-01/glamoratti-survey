import streamlit as st
import base64
import random  # NEW: 랜덤 순서를 위해 필요
import streamlit.components.v1 as components
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. 초기 설정 및 세션 상태 관리 ---
if 'page' not in st.session_state:
    st.session_state.page = 'intro'
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0  # 0번 인덱스(첫 번째 이미지)부터 시작
if 'all_responses' not in st.session_state:
    st.session_state.all_responses = {}

# 🌟 중요: 이미지 순서를 랜덤하게 섞어서 저장하는 로직
if 'random_order' not in st.session_state:
    # pair1.png ~ pair13.png 리스트 생성
    file_list = [f"pair{i}.png" for i in range(1, 14)] 
    random.shuffle(file_list)  # 리스트를 무작위로 섞음
    st.session_state.random_order = file_list

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return None

# --- 2. [1페이지] 인트로 ---
if st.session_state.page == 'intro':
    st.title("1980년대 패션의 재해석 수준에 따른 Glamoratti 아우터의 감성 인지 조사")
    st.write("---")
    st.subheader("실험 안내")
    st.info("""
    본 설문조사는 Glamoratti 패션 트렌드 이미지에 대한 소비자의 감성적 반응을 측정하기 위한 연구용 설문입니다.
    - 소요 시간: 약 20-30분 내외
    - 모든 응답은 익명으로 처리되며 연구 목적으로만 사용됩니다.
    """)
    st.warning("⚠️ 중간에 브라우저를 새로고침하면 응답이 초기화되니 주의해 주세요.")
    
    if st.button("설문 시작하기"):
        st.session_state.page = 'demographics'
        st.rerun()

# --- 3. [2페이지] 인구통계학적 설문 ---
elif st.session_state.page == 'demographics':
    st.title("인구통계학적 정보")
    st.write("본격적인 시작에 앞서 기초 정보를 입력해 주세요.")
    st.write("---")

    gender = st.radio("귀하의 성별은 무엇입니까? *", ["남자", "여자"], index=None)
    age = st.radio("귀하의 연령은 어떻게 되십니까? *", ["20대", "30대", "40대", "50대", "60대 이상"], index=None)
    edu = st.radio("귀하의 최종 학력은 무엇입니까? *", 
                   ["고등학교 졸업", "대학교 재학", "대학교 졸업", "석사과정 재학", "석사과정 졸업", "박사과정 재학", "박사과정 졸업"], index=None)
    
    major_list = ["예술·디자인 계열 (패션, 의류, 시각디자인 등)", "인문·사회 계열", "경영·경제 계열", 
                  "이공·자연 계열", "의약·보건 계열", "교육 계열", "해당 없음", "기타"]
    major = st.radio("귀하의 전공 계열은 무엇입니까? *", major_list, index=None)
    major_etc = ""
    if major == "기타":
        major_etc = st.text_input("기타 전공을 입력해 주세요.")

    job = st.text_input("귀하의 현재 직업은 무엇입니까? *")
    spending = st.radio("귀하의 월 평균 의류 지출액은 어느 정도입니까? *", 
                        ["5만 원 미만", "5만 원 이상 ~ 10만 원 미만", "10만 원 이상 ~ 20만 원 미만", 
                         "20만 원 이상 ~ 30만 원 미만", "30만 원 이상 ~ 50만 원 미만", "50만 원 이상"], index=None)

    if st.button("다음 단계로"):
        if not (gender and age and edu and major and job and spending):
            st.error("모든 문항에 응답해 주세요.")
        else:
            st.session_state.user_data.update({
                "성별": gender, "연령": age, "학력": edu, 
                "전공": major if major != "기타" else f"기타({major_etc})",
                "직업": job, "의류지출": spending
            })
            st.session_state.page = 'main_survey'
            st.rerun()

# --- 4. [3페이지] 메인 설문 (감성 평가 좌/우 분리 버전) ---
elif st.session_state.page == 'main_survey':
    idx = st.session_state.current_idx
    total_sets = len(st.session_state.random_order)
    current_img_file = st.session_state.random_order[idx]
    
    img_b64 = get_image_base64(current_img_file)
    img_src = f"data:image/png;base64,{img_b64}" if img_b64 else "https://via.placeholder.com/600x300.png?text=Image+Not+Found"

    # 1️⃣ 여기에 빈 컨테이너(placeholder)를 생성합니다.
    placeholder = st.empty()

    # 2️⃣ 이제 모든 UI 요소를 이 안에 넣습니다. (들여쓰기 주의!)
    with placeholder.container():

    # CSS 설정 (상단 고정 유지)
        st.markdown(f"""
            <style>
            header {{visibility: hidden;}}
            .sticky-image {{ position: fixed; top: 0; left: 0; width: 100%; background-color: white; z-index: 1000; padding: 10px 0; border-bottom: 2px solid #ddd; text-align: center; }}
            .spacer {{ margin-top: 420px; }}
            .section-header {{ background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-top: 20px; }}
            </style>
            <div class="sticky-image">
                <p style="margin:0; color: #888; font-size: 0.9em;">전체 13개 중 {idx+1}번째 평가</p>
                <img src="{img_src}" width="480"><br>
                <small style="color: #999;">파일명: {current_img_file}</small> 
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
    
        step_responses = {}
        adj_pairs = [
            ("촌스럽다", "세련되다"), ("소박하다", "고급스럽다"), ("수수하다", "화려하다"), 
            ("순수하다", "섹시하다"), ("투박하다", "우아하다"), ("단조롭다", "드라마틱하다"), 
            ("온화하다", "강렬하다"), ("여리다", "단단하다"), ("부드럽다", "날카롭다"), 
            ("복잡하다", "간결하다"), ("밋밋하다", "화사하다")
        ]

    # --- (1) 감성 인지 평가 (좌측/우측 각각 진행) ---
        st.subheader("1. 감성 인지 평가")
    
    # 1-1. 좌측 이미지 평가
        st.markdown('<div class="section-header"><strong>1-1. 좌측 이미지 평가</strong></div>', unsafe_allow_html=True)
        for i, (l, r) in enumerate(adj_pairs):
            cols = st.columns([2, 6, 2])
            with cols[0]: st.markdown(f"<div style='text-align:right; line-height:80px;'>{l}</div>", unsafe_allow_html=True)
            with cols[1]: 
                key_name = f"{current_img_file}_Left_emo{i+1}"
                step_responses[key_name] = st.select_slider(f"slider_{current_img_file}_L_emo{i}", options=[1,2,3,4,5,6,7], value=4, label_visibility="collapsed")
            with cols[2]: st.markdown(f"<div style='text-align:left; line-height:80px;'>{r}</div>", unsafe_allow_html=True)

        st.write("---")

    # 1-2. 우측 이미지 평가
        st.markdown("<div class='section-header'><strong>1-2. 우측 이미지 평가</strong></div>", unsafe_allow_html=True)
        for i, (l, r) in enumerate(adj_pairs):
            cols = st.columns([2, 6, 2])
            with cols[0]: st.markdown(f"<div style='text-align:right; line-height:80px;'>{l}</div>", unsafe_allow_html=True)
            with cols[1]: 
                key_name = f"{current_img_file}_Right_emo{i+1}"
                step_responses[key_name] = st.select_slider(f"slider_{current_img_file}_R_emo{i}", options=[1,2,3,4,5,6,7], value=4, label_visibility="collapsed")
            with cols[2]: st.markdown(f"<div style='text-align:left; line-height:80px;'>{r}</div>", unsafe_allow_html=True)

        st.write("---")

    # --- (2) 수용 의도 평가 (3문항) ---
        st.subheader("2. 수용 의도 평가")
        acc_items = ["수용할 가능성", "구매할 의향", "추천할 의향"]
        for i, item in enumerate(acc_items):
            st.write(f"나는 **우측 이미지**의 아우터를 **{item}**이 높다.")
            cols = st.columns([2, 6, 2])
            with cols[0]: st.write("전혀 아니다")
            with cols[1]: 
                key_name = f"{current_img_file}_acc{i+1}"
                step_responses[key_name] = st.select_slider(f"slider_{current_img_file}_acc{i}", options=[1,2,3,4,5,6,7], value=4, label_visibility="collapsed")
            with cols[2]: st.write("매우 그렇다")

        st.write("---")

    # --- (3) 재해석 정도 평가 (4문항) ---
        st.subheader("3. 재해석 정도 평가")
        re_items = ["실루엣", "색상", "소재", "디테일"]
        for i, item in enumerate(re_items):
            st.write(f"우측 이미지는 좌측에 비해 **{item}**을 상당히 변형하였다.")
            cols = st.columns([2, 6, 2])
            with cols[0]: st.write("전혀 아니다")
            with cols[1]: 
                key_name = f"{current_img_file}_re{i+1}"
                step_responses[key_name] = st.select_slider(f"slider_{current_img_file}_re{i}", options=[1,2,3,4,5,6,7], value=4, label_visibility="collapsed")
            with cols[2]: st.write("매우 그렇다")

        st.write("---")

    # 이동 버튼 로직
        if idx < total_sets - 1:
            if st.button("평가 완료 -> 다음 이미지로"):
                st.session_state.all_responses.update(step_responses)
                st.session_state.current_idx += 1
                st.rerun()
        else:
            if st.button("모든 설문 완료 및 제출"):
                st.session_state.all_responses.update(step_responses)
                final_data = {**st.session_state.user_data, **st.session_state.all_responses}
    
                conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 1. 실제 탭 이름 가져오기 (이전과 동일)
                spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
                sh = conn.client._client.open_by_url(spreadsheet_url)
                real_sheet_name = sh.get_worksheet(0).title

    # 2. [핵심 수정] ttl=0 을 추가하여 항상 "최신" 데이터를 읽어옵니다.
                try:
        # ttl=0은 캐시 수명을 0초로 설정하여 무조건 새로 읽어오게 합니다.
                    existing_data = conn.read(worksheet=real_sheet_name, ttl=0)
                except Exception:
                    existing_data = pd.DataFrame()

    # 3. 데이터 합치기
                new_data = pd.DataFrame([final_data])
    
    # 기존 데이터가 비어있지 않다면 아래에 행을 추가합니다.
                if not existing_data.empty:
        # concat 시 ignore_index=True를 주면 인덱스가 꼬이지 않고 아래로 쌓입니다.
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                else:
                    updated_df = new_data
    
    # 4. 시트에 전체 데이터 덮어쓰기 (기존 내용 + 새 내용)
                conn.update(worksheet=real_sheet_name, data=updated_df)
    
                st.success("데이터가 성공적으로 저장되었습니다! 응답해주셔서 감사합니다!")
                st.balloons()
