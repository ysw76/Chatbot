"""
hospitals_search.py — 천안시 병원 정보 검색 모듈

병원 데이터: hospitals_data.json
기능:
  - 진료과별 병원 검색
  - 주말 진료 병원 검색
  - 병원 상세 정보 조회
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
HOSPITALS_PATH = BASE_DIR / "hospitals_data.json"


def load_hospitals() -> list:
    """JSON 파일에서 병원 정보 로드"""
    if not HOSPITALS_PATH.exists():
        return []

    with open(HOSPITALS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get('hospitals', [])


def search_by_category(category: str) -> list:
    """진료과별 병원 검색 (예: '소아청소년과', '가정의학과')"""
    hospitals = load_hospitals()
    return [h for h in hospitals if category in h['category']]


def search_weekend_hospitals() -> list:
    """주말 진료 가능한 병원 검색"""
    hospitals = load_hospitals()
    weekend_hospitals = []

    for h in hospitals:
        # 토요일 또는 일요일에 휴무가 아니면 주말 진료 가능
        if h['saturday_time'] != '휴무' or h['sunday_time'] != '휴무':
            weekend_hospitals.append(h)

    return weekend_hospitals


def search_by_symptom(symptom: str) -> str:
    """증상에 따른 병원 추천"""
    symptom_mapping = {
        "감기/코감기": "소아청소년과",
        "발열": "소아청소년과",
        "기침": "소아청소년과",
        "구토/소화불량": "소아청소년과",
        "피부질환": "소아청소년과",
        "예방접종": "소아청소년과",
        "소아청소년과": "소아청소년과",
        "가정의학과": "가정의학과",
    }

    recommended_category = symptom_mapping.get(symptom, "소아청소년과")
    hospitals = search_by_category(recommended_category)

    if not hospitals:
        return "해당하는 병원이 없습니다."

    # 주말 진료 병원 우선
    weekend_hospitals = [h for h in hospitals if h['saturday_time'] != '휴무' or h['sunday_time'] != '휴무']

    if weekend_hospitals:
        return format_hospital_info(weekend_hospitals)
    else:
        return format_hospital_info(hospitals)


def format_hospital_info(hospitals: list) -> str:
    """병원 정보를 포맷팅된 문자열로 반환"""
    if not hospitals:
        return "해당하는 병원이 없습니다."

    result = []
    for h in hospitals:
        info = f"""
🏥 **{h['name']}**
📍 주소: {h['address']}
📞 전화: {h['phone']}
🩺 진료과: {h['category']}
👨‍⚕️ 의사: {h['doctor']}

📅 진료 시간:
  • 평일: {h['weekday_time']}
  • 토요일: {h['saturday_time']}
  • 일요일: {h['sunday_time']}
  • 공휴일: {h['holiday_time']}

📝 특이사항: {h['notes']}
"""
        result.append(info)

    return "\n".join(result)


def get_hospital_by_id(hospital_id: int) -> dict:
    """병원 ID로 상세 정보 조회"""
    hospitals = load_hospitals()
    for h in hospitals:
        if h['id'] == hospital_id:
            return h
    return {}


def search_by_location(location: str) -> list:
    """지역별 병원 검색 (예: '서북구', '동남구')"""
    hospitals = load_hospitals()
    return [h for h in hospitals if location in h.get('location', '')]


def search_by_category_and_location(category: str, location: str) -> list:
    """진료과와 지역 모두로 검색"""
    hospitals = load_hospitals()
    return [h for h in hospitals
            if category in h['category'] and location in h.get('location', '')]


def query_hospitals(question: str) -> str:
    """질문에 따른 병원 검색"""
    question = question.lower()

    # 지역별 검색
    locations = {'서북구': '서북구', '동남구': '동남구', '백석': '서북구', '성정': '서북구', '두정': '동남구', '쌍용': '동남구'}
    found_location = None
    for key, loc in locations.items():
        if key in question:
            found_location = loc
            break

    # 주말 진료 관련 질문
    if any(word in question for word in ['주말', '토요일', '일요일', '공휴일']):
        hospitals = search_weekend_hospitals()

        # 지역이 지정된 경우 필터링
        if found_location:
            hospitals = [h for h in hospitals if h.get('location') == found_location]

        if hospitals:
            region_text = f" ({found_location})" if found_location else ""
            return f"주말 진료 가능한 병원 {len(hospitals)}곳{region_text}:\n\n" + format_hospital_info(hospitals)
        else:
            return f"{found_location if found_location else ''} 지역에서 주말 진료 가능한 병원이 없습니다."

    # 진료과 관련 질문
    if '소아청소년과' in question:
        if found_location:
            hospitals = search_by_category_and_location("소아청소년과", found_location)
            return f"{found_location} 소아청소년과 {len(hospitals)}곳:\n\n" + format_hospital_info(hospitals)
        else:
            hospitals = search_by_category("소아청소년과")
            return f"소아청소년과 {len(hospitals)}곳:\n\n" + format_hospital_info(hospitals)

    if '가정의학과' in question:
        if found_location:
            hospitals = search_by_category_and_location("가정의학과", found_location)
            return f"{found_location} 가정의학과 {len(hospitals)}곳:\n\n" + format_hospital_info(hospitals)
        else:
            hospitals = search_by_category("가정의학과")
            return f"가정의학과 {len(hospitals)}곳:\n\n" + format_hospital_info(hospitals)

    # 증상 관련 질문
    for symptom in ["감기", "발열", "기침", "구토", "피부", "예방접종"]:
        if symptom in question:
            hospitals_by_symptom = search_by_symptom(symptom)
            if found_location:
                # 증상별 추천 중 해당 지역만 필터링
                all_hospitals = load_hospitals()
                symptom_category = {'감기': '소아청소년과', '발열': '소아청소년과', '기침': '소아청소년과',
                                   '구토': '소아청소년과', '피부': '소아청소년과', '예방접종': '소아청소년과'}.get(symptom)
                filtered = search_by_category_and_location(symptom_category, found_location)
                if filtered:
                    return f"**{symptom}** 증상 관련 {found_location} 병원:\n\n" + format_hospital_info(filtered)
            return hospitals_by_symptom

    # 지역만 지정된 경우
    if found_location:
        hospitals = search_by_location(found_location)
        if hospitals:
            return f"{found_location} 지역의 모든 병원 {len(hospitals)}곳:\n\n" + format_hospital_info(hospitals)

    # 기본 응답
    all_hospitals = load_hospitals()
    return f"천안시 전체 {len(all_hospitals)}곳의 병원:\n\n" + format_hospital_info(all_hospitals)


if __name__ == "__main__":
    # 테스트
    print("=== 주말 진료 병원 ===")
    print(format_hospital_info(search_weekend_hospitals()))

    print("\n=== 소아청소년과 ===")
    print(format_hospital_info(search_by_category("소아청소년과")))

    print("\n=== 발열 증상 관련 ===")
    print(search_by_symptom("발열"))
