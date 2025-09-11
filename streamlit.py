import streamlit as st
from ai_client import GeminiClient
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import config
import time

st.set_page_config(page_title="Childcare RAG Chatbot")
st.title("Chat with Gemini AI 🍼👶🏻")

# GeminiClient 초기화
@st.cache_resource
def load_gemini():
    return GeminiClient(api_key=config.GOOGLE_API_KEY)

gemini = load_gemini()

# VectorStore 초기화
@st.cache_resource
def load_vectorstore():
    embedding_model = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sbert-nli",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    persist_dir = "./vector_db"
    vectorstore = Chroma(
        embedding_function=embedding_model,
        persist_directory=persist_dir
    )
    return vectorstore

vectorstore = load_vectorstore()

# 대화 기록 초기화
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# 현재 입력 저장 (중복 방지)
if "current_prompt" not in st.session_state:
    st.session_state["current_prompt"] = None

# RAG 함수
def run_rag(query: str, top_k=50):
    docs_with_scores = vectorstore.similarity_search_with_score(query, k=top_k)

    seen_ids = set()
    context = []
    for d, score in docs_with_scores:
        if score < 0.2:
            continue
        para_id = d.metadata.get("paragraph_id") or d.page_content[:30]
        if para_id in seen_ids:
            continue
        seen_ids.add(para_id)

        context.append({
            "bookname": d.metadata.get("bookname", "unknown"),
            "chapter_id": d.metadata.get("chapter_id", "unknown"),
            "chapter_name": d.metadata.get("chapter_name", "unknown"),
            "sub_chapter_name": d.metadata.get("sub_chapter_name", "unknown"),
            "paragraph_id": para_id,
            "content": d.metadata.get("content") or d.page_content,
            "raw_text": d.page_content,
            "score": min(score, 1.0)
        })

    # Gemini 답변 생성 (스트리밍용)
    return gemini.generate_response(query, context), context

# 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요:"):
    st.session_state["current_prompt"] = prompt

if st.session_state["current_prompt"]:
    prompt = st.session_state.pop("current_prompt")
    
    # 사용자 메시지 출력
    st.session_state["chat_history"].append({"role": "user", "message": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 메시지 처리 (스트리밍)
    with st.chat_message("ai"):
        message_placeholder = st.empty()
        full_response = ""
        answer, context = run_rag(prompt, top_k=50)
        
        # 스트리밍처럼 글자 단위 출력
        for char in answer:
            full_response += char
            message_placeholder.markdown(full_response)
            time.sleep(0.01)  # 출력 속도 조절

        # 대화 기록 저장
        st.session_state["chat_history"].append({"role": "ai", "message": full_response})

# 이전 대화 출력
for chat in st.session_state["chat_history"]:
    role = chat["role"]
    message = chat["message"]
    with st.chat_message(role):
        st.markdown(message)

# 참고 문서 확인 (옵션, 유사도 포함, 상위 3개)
if st.session_state.get("chat_history") and 'context' in locals():
    with st.expander("상위 3개 출처 상세보기"):
        for i, c in enumerate(sorted(context, key=lambda x: x['score'], reverse=True)[:3], 1):
            st.markdown(f"### 출처 {i} ({c['score']*100:.1f}% 유사)")
            st.markdown(f"- **책 명:** {c['bookname']}")
            st.markdown(f"- **챕터 - 소제목:** {c['chapter_name']} - {c['sub_chapter_name']}")
            st.markdown(f"- **문단 번호:** {c['paragraph_id']}")
            st.markdown(c['content'].replace("\n", "  \n"))