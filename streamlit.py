import streamlit as st
from ai_client import GeminiClient
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import time
import config

st.set_page_config(page_title="Childcare RAG Chatbot")
st.title("Chat with Gemini AI 🍼👶🏻")

@st.cache_resource
def load_gemini():
    return GeminiClient(api_key=config.GOOGLE_API_KEY)

@st.cache_resource
def load_vectorstore():
    embedding_model = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sbert-nli",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    persist_dir = "./vector_db"
    return Chroma(embedding_function=embedding_model, persist_directory=persist_dir)

gemini = load_gemini()
vectorstore = load_vectorstore()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def run_rag(query: str, top_k: int = 50):
    docs_with_scores = vectorstore.similarity_search_with_score(query, k=top_k)
    seen_ids = set()
    context = []
    for doc, score in docs_with_scores:
        para_id = doc.metadata.get("paragraph_id") or doc.page_content[:30]
        if para_id in seen_ids:
            continue
        seen_ids.add(para_id)
        score = score if score <= 1.0 else 0.0
        context.append({
            "bookname": doc.metadata.get("bookname", "정보 없음"),
            "chapter_name": doc.metadata.get("chapter_name", "정보 없음"),
            "sub_chapter_name": doc.metadata.get("sub_chapter_name", "정보 없음"),
            "paragraph_id": para_id,
            "content": doc.metadata.get("content") or doc.page_content,
            "score": score
        })
    answer = gemini.generate_response(query, context)
    return answer, context

for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["message"])
    if chat["role"] == "ai":
        with st.expander("답변 생성에 사용된 출처 보기"):
            for i, c in enumerate(chat.get("context", [])[:3], 1):
                st.markdown(f"#### 출처 {i} ({c['score']*100:.1f}% 유사)")
                st.markdown(f"- **책 이름:** {c['bookname']}")
                st.markdown(f"- **챕터:** {c['chapter_name']} - {c['sub_chapter_name']}")
                st.markdown(f"- **문단 ID:** {c['paragraph_id']}")
                st.info(c['content'].replace("\n", "  \n"))

if prompt := st.chat_input("질문을 입력하세요:"):
    st.session_state.chat_history.append({"role": "user", "message": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("ai"):
        message_placeholder = st.empty()
        full_response = ""
        answer, context = run_rag(prompt, top_k=50)

        for char in answer:
            full_response += char
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.01)
        message_placeholder.markdown(full_response)

    # AI 답변과 context를 함께 저장
    st.session_state.chat_history.append({
        "role": "ai",
        "message": full_response,
        "context": context  # context 포함
    })

    latest_ai = next((c for c in reversed(st.session_state.chat_history) if c["role"] == "ai"), None)
    if latest_ai and latest_ai["context"]:  # context가 있을 때만 표시
        with st.expander("답변 생성에 사용된 출처 보기"):
            for i, c in enumerate(latest_ai["context"][:3], 1):
                st.markdown(f"#### 출처 {i} ({min(c['score'],1.0)*100:.1f}% 유사)")
                st.markdown(f"- **책 이름:** {c['bookname']}")
                st.markdown(f"- **챕터:** {c['chapter_name']} - {c['sub_chapter_name']}")
                st.markdown(f"- **문단 ID:** {c['paragraph_id']}")
                text = c['content']
                if "내용:" in text:
                    text = text.split("내용:")[-1].strip()
                st.info(text[:300] + ("..." if len(text) > 300 else ""))