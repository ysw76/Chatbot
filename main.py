import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

# .env 파일 로드 (로컬 개발용)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from hospitals_search import query_hospitals
from claude_integration import get_consultant

# 페이지 설정
st.set_page_config(
    page_title="🏥 육아맘 의료진 찾기",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
    <style>
    /* 컬러 팔레트 */
    :root {
        --primary-blue: #7FC0FA;
        --accent-yellow: #F0FA73;
        --accent-red: #FA2E23;
        --dark-red: #A8120B;
        --neutral-gray: #607080;
        --muted-brown: #787A5B;
    }

    /* 메인 배경 */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    }

    /* 채팅 메시지 */
    .chat-message {
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
        display: flex;
        gap: 1rem;
        box-shadow: 0 2px 4px rgba(168, 18, 11, 0.1);
    }

    /* 사용자 메시지 (파란색) */
    .user-message {
        background: linear-gradient(135deg, #7FC0FA 0%, #5BA8E8 100%);
        flex-direction: row-reverse;
        color: white;
    }

    .user-message strong {
        color: #ffffff;
    }

    /* 봇 메시지 (회갈색/중립) */
    .bot-message {
        background: linear-gradient(135deg, #f5f5f5 0%, #f0f0f0 100%);
        border-left: 4px solid #7FC0FA;
    }

    /* 채팅 컨테이너 */
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        border: 2px solid #7FC0FA;
        padding: 1rem;
        border-radius: 0.75rem;
        background-color: #ffffff;
    }

    /* 정보 박스 */
    [data-testid="stAlert"] {
        border-radius: 0.75rem;
    }

    /* 버튼 스타일 */
    button {
        border-radius: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_info" not in st.session_state:
    st.session_state.user_info = {
        "name": "",
        "child_name": "",
        "child_age": "",
        "phone": "",
        "symptom": ""
    }

if "consultation_active" not in st.session_state:
    st.session_state.consultation_active = False

if "claude_mode" not in st.session_state:
    st.session_state.claude_mode = False

if "consultant" not in st.session_state:
    st.session_state.consultant = None

# 사이드바 - 사용자 정보 입력
st.sidebar.header("👶 아이 정보 & 증상")

with st.sidebar.form("user_form"):
    st.session_state.user_info["name"] = st.text_input(
        "엄마 이름",
        value=st.session_state.user_info["name"],
        placeholder="성명을 입력하세요"
    )

    st.session_state.user_info["child_name"] = st.text_input(
        "아이 이름",
        value=st.session_state.user_info["child_name"],
        placeholder="예: 철수, 영희"
    )

    st.session_state.user_info["child_age"] = st.text_input(
        "아이 나이",
        value=st.session_state.user_info["child_age"],
        placeholder="예: 3세, 5개월"
    )

    st.session_state.user_info["phone"] = st.text_input(
        "연락처",
        value=st.session_state.user_info["phone"],
        placeholder="010-0000-0000"
    )

    st.session_state.user_info["symptom"] = st.selectbox(
        "아이 증상/필요 진료과",
        [
            "선택하세요",
            "감기/코감기",
            "발열",
            "기침",
            "구토/소화불량",
            "피부질환",
            "예방접종",
            "소아청소년과",
            "가정의학과",
            "기타"
        ],
        index=["선택하세요", "감기/코감기", "발열", "기침", "구토/소화불량", "피부질환", "예방접종", "소아청소년과", "가정의학과", "기타"].index(st.session_state.user_info["symptom"]) if st.session_state.user_info["symptom"] else 0
    )

    submit_button = st.form_submit_button("정보 저장")

if submit_button:
    if (st.session_state.user_info["name"] and
        st.session_state.user_info["child_name"] and
        st.session_state.user_info["child_age"] and
        st.session_state.user_info["symptom"] != "선택하세요"):
        st.sidebar.success("✅ 정보가 저장되었습니다!")
        st.session_state.consultation_active = True
    else:
        st.sidebar.error("⚠️ 필수 정보를 입력해주세요!")

# 사이드바 - Claude AI 상담 설정
st.sidebar.header("🤖 AI 상담 설정 (선택)")
with st.sidebar.expander("Claude API 설정"):
    api_key_input = st.text_input(
        "Anthropic API 키",
        type="password",
        placeholder="sk-ant-... 형식의 키를 입력하세요"
    )

    if api_key_input:
        try:
            consultant = get_consultant(api_key_input)
            if consultant.is_available():
                st.sidebar.success("✅ Claude API 연결 완료!")
                st.session_state.consultant = consultant
                st.session_state.claude_mode = True
            else:
                st.sidebar.error("❌ API 키가 유효하지 않습니다.")
        except Exception as e:
            st.sidebar.error(f"❌ 오류: {str(e)}")
    elif st.session_state.claude_mode:
        st.sidebar.info("✅ Claude 상담 모드 활성화")
        if st.sidebar.button("Claude 모드 끄기"):
            st.session_state.claude_mode = False
            st.session_state.consultant = None
            st.rerun()

# 사이드바 - 검색 기록 관리
st.sidebar.header("📝 검색 기록")

if st.sidebar.button("새 검색 시작", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

if st.sidebar.button("검색 기록 저장", use_container_width=True):
    if st.session_state.messages:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_{timestamp}.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "user_info": st.session_state.user_info,
            "messages": st.session_state.messages
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        st.sidebar.success(f"✅ 저장됨: {filename}")
    else:
        st.sidebar.warning("⚠️ 저장할 검색 기록이 없습니다!")

# 사이드바 - 통계
st.sidebar.header("📊 통계")
st.sidebar.metric("총 메시지 수", len(st.session_state.messages))
st.sidebar.metric("사용자 메시지", sum(1 for m in st.session_state.messages if m["role"] == "user"))
st.sidebar.metric("상담사 메시지", sum(1 for m in st.session_state.messages if m["role"] == "assistant"))

# 메인 영역
title_col1, title_col2 = st.columns([4, 1])
with title_col1:
    st.title("🏥 육아맘 의료진 찾기")
with title_col2:
    if st.session_state.claude_mode and st.session_state.consultant:
        st.success("🤖 Claude 모드")

# 사용자 정보 표시
if st.session_state.consultation_active:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f"👤 {st.session_state.user_info['name']}")
    with col2:
        st.info(f"🧒 {st.session_state.user_info['child_name']}")
    with col3:
        st.info(f"📅 {st.session_state.user_info['child_age']}")
    with col4:
        st.info(f"🩺 {st.session_state.user_info['symptom']}")

    st.divider()

    # 검색 필터
    st.subheader("🔍 검색 필터")
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        search_region = st.selectbox(
            "지역 선택",
            ["전체", "서북구", "동남구"],
            index=0
        )

    with filter_col2:
        search_department = st.selectbox(
            "진료과",
            ["전체", "소아청소년과", "가정의학과"],
            index=0
        )

    with filter_col3:
        search_weekend = st.checkbox("주말 진료만", value=False)

    st.divider()

    # 빠른 검색 버튼
    st.subheader("⚡ 빠른 검색")
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

    quick_searches = {
        quick_col1: ("🏥 주말 진료", "주말에 진료 가능한 병원"),
        quick_col2: ("👶 소아청소년과", "소아청소년과 찾기"),
        quick_col3: ("🤒 발열", "아이가 열이 나요"),
        quick_col4: ("💊 예방접종", "예방접종 가능한 병원")
    }

    for col, (label, query) in quick_searches.items():
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": query,
                    "timestamp": datetime.now().isoformat()
                })

                bot_response = query_hospitals(query)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": bot_response,
                    "timestamp": datetime.now().isoformat()
                })
                st.rerun()

    st.divider()

    # 채팅 영역
    st.subheader("🗨️ 의료진 검색")

    # 메시지 표시
    with st.container():
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                    <div class="chat-message user-message">
                        <div>
                            <strong>👤 {st.session_state.user_info['name']}</strong><br>
                            {message['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="chat-message bot-message">
                        <div>
                            <strong>🏥 의료진 정보</strong><br>
                            {message['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # 입력 영역
    st.divider()

    user_input = st.text_area(
        "메시지를 입력하세요",
        placeholder="주말에 진료 가능한 의료진을 찾고 있습니다...",
        height=100,
        label_visibility="collapsed"
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("🔍 검색", use_container_width=True):
            if user_input.strip():
                # 사용자 메시지 추가
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat()
                })

                # Claude 모드 vs 일반 모드
                if st.session_state.claude_mode and st.session_state.consultant:
                    # Claude AI 상담
                    bot_response = st.session_state.consultant.consult(user_input)
                else:
                    # 기본 병원 검색
                    filter_query = user_input
                    if search_region != "전체":
                        filter_query += f" {search_region}"
                    if search_department != "전체":
                        filter_query += f" {search_department}"
                    if search_weekend:
                        filter_query += " 주말"

                    bot_response = query_hospitals(filter_query)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": bot_response,
                    "timestamp": datetime.now().isoformat()
                })

                st.rerun()
            else:
                st.warning("검색어를 입력해주세요!")

    with col2:
        if st.button("🗑️ 마지막 메시지 삭제", use_container_width=True):
            if st.session_state.messages:
                st.session_state.messages.pop()
                st.rerun()

    with col3:
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

else:
    st.info("👈 왼쪽 사이드바에서 정보를 입력하고 검색을 시작하세요!")

    # 가이드
    st.markdown("""
    ### 📖 이용 방법

    1. **아이 정보 입력**: 왼쪽 사이드바에서 필수 정보를 입력합니다
       - 엄마 이름
       - 아이 나이
       - 연락처
       - 아이 증상/필요 진료과

    2. **정보 저장**: 입력 완료 후 "정보 저장" 버튼을 클릭합니다

    3. **의료진 검색**: 주말에 진료 가능한 의료진을 검색합니다

    4. **기록 저장**: 검색 종료 후 "검색 기록 저장" 버튼으로 저장합니다

    ### 💡 주요 기능

    - 🏥 주말 진료 가능 의료진 검색
    - 📝 실시간 검색 기록
    - 💾 검색 기록 자동 저장
    - 📊 통계 정보 제공
    - 🔄 검색 관리 (수정, 삭제, 초기화)
    """)
