"""
claude_integration.py — Claude API를 이용한 고급 상담 기능

Claude API를 사용하여 자연스러운 의료 상담 제공
- 단순 병원 검색 + AI 기반 상담
- 증상 분석 및 병원 추천
- 자연스러운 대화형 상담
"""

import os
from typing import Optional

try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False


class ClaudeConsultant:
    def __init__(self, api_key: Optional[str] = None):
        """Claude API 초기화"""
        if not CLAUDE_AVAILABLE:
            self.available = False
            return

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            self.available = False
            return

        self.client = Anthropic(api_key=self.api_key)
        self.available = True
        self.conversation_history = []

        # 시스템 프롬프트
        self.system_prompt = """당신은 육아맘을 위한 친절한 의료 상담 AI입니다.

역할:
- 아이의 증상을 자세히 듣고 공감하기
- 언제 병원에 가야 하는지 조언하기
- 천안시 지역 병원 정보 제공하기
- 의료 상담만 제공하고, 의료 진단은 절대 하지 않기

말투:
- 따뜻하고 친근한 톤
- 육아맘의 불안을 이해하는 표현 사용
- 항상 의사 진료를 우선순위로 권유

제공할 정보:
- 증상별 대처 방법
- 응급 증상 판단
- 천안시 병원 정보 (병원명, 주소, 전화, 진료시간)
- 예방 및 건강 관리 팁"""

    def is_available(self) -> bool:
        """Claude API 사용 가능 여부"""
        return self.available

    def consult(self, user_message: str) -> str:
        """사용자와의 상담"""
        if not self.available:
            return "Claude API를 사용할 수 없습니다. API 키를 확인해주세요."

        try:
            # 대화 기록에 사용자 메시지 추가
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            # Claude 호출
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=self.system_prompt,
                messages=self.conversation_history
            )

            # 응답 추출
            assistant_message = response.content[0].text

            # 대화 기록에 응답 추가
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            return f"상담 중 오류가 발생했습니다: {str(e)}"

    def reset_conversation(self):
        """대화 기록 초기화"""
        self.conversation_history = []

    def format_hospital_info_for_claude(self, hospitals: list) -> str:
        """병원 정보를 Claude에게 전달하기 위해 포맷팅"""
        if not hospitals:
            return "해당하는 병원이 없습니다."

        formatted = "다음 병원들을 추천합니다:\n\n"
        for h in hospitals:
            formatted += f"""
🏥 {h['name']}
📍 주소: {h['address']}
📞 전화: {h['phone']}
📅 진료시간:
   - 평일: {h['weekday_time']}
   - 토요일: {h['saturday_time']}
   - 일요일: {h['sunday_time']}
📝 특이사항: {h['notes']}
"""
        return formatted


def get_consultant(api_key: Optional[str] = None) -> ClaudeConsultant:
    """Claude 상담사 인스턴스 생성"""
    return ClaudeConsultant(api_key)


if __name__ == "__main__":
    # 테스트
    consultant = get_consultant()

    if consultant.is_available():
        print("✅ Claude API 사용 가능")

        # 테스트 상담
        response = consultant.consult("3살 아이가 감기에 걸렸는데 어떻게 해야 하나요?")
        print("\n상담사 응답:")
        print(response)
    else:
        print("❌ Claude API를 사용할 수 없습니다.")
        print("   API 키 확인: ANTHROPIC_API_KEY 환경변수 설정")
