import os
from typing import Any, Dict, List
import google.generativeai as genai


class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = os.getenv("GOOGLE_API_KEY", api_key)
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY가 존재하지 않습니다.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.chat_session = self.model.start_chat(history=[])

    def generate_response(self, prompt: str, context: List[Dict[str, Any]]) -> str:
        
        basic_text = ""
        for i, chunk in enumerate(context, 1):
            basic_text += f"\n[출처 {i}] {chunk['chapter_name']} - {chunk['sub_chapter_name']}\n"
            basic_text += f"(문단 {chunk['paragraph_id']})\n"
            basic_text += f"{chunk['raw_text']}\n"
            basic_text += "-" * 50 + "\n"

        final_prompt = f"""
        당신은 육아 전문가 입니다.
        아래 참고 자료를 바탕으로 질문에 답변해주시길 바랍니다.

        [참고 자료]
        {basic_text}

        [질문]
        {prompt}

        [규칙]
        - 참고 자료에 있는 모든 내용과 세부사항을 활용해서 답변하세요.
        - 특히 구체적인 장소나 방법, 예시까지 반드시 포함하세요.
        - 절대로 일반적인 요약만 하지 마세요.
        - 최대한 참고 자료의 원문 바탕으로 대답해주세요.
        - 만약 참고 자료에 답이 없다면 "참고 자료에 답이 없습니다."라고 답하세요.
        - 참고 자료의 내용을 몇 프로 이용했는지 반드시 명시하세요.
        - 가능한 한 친절하고 이해하기 쉽게 설명하세요.
        """
        
        response = self.chat_session.send_message(final_prompt, stream=False)
        return response.text