import json
import re
from langchain.vectorstores import Chroma
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from ai_client import GeminiClient
import config  # 이전에 만든 GeminiClient 사용

# 1. 텍스트 파일 로드
file_path = "data/book/childcare_guide_for_new_father.txt"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

book_title = "초보 아빠를 위한 육아 가이드"

# 2. 챕터/소챕터/문단 단위로 나누기
chapter_pattern = re.compile(r"^\[(\d{2})\. (.+?)\]$", re.MULTILINE)
subchapter_pattern = re.compile(r"^(\d{2})\. (.+)$", re.MULTILINE)

chapters = [(m.start(), m.group(1), m.group(2)) for m in chapter_pattern.finditer(text)]
chapters.append((len(text), None, None))  # 마지막 챕터 끝

documents = []

for i in range(len(chapters)-1):
    chap_start, chapter_id, chapter_name = chapters[i]
    chap_end = chapters[i+1][0]
    chap_text = text[chap_start:chap_end]

    subchapters = [(m.start(), m.group(1), m.group(2)) for m in subchapter_pattern.finditer(chap_text)]
    subchapters.append((len(chap_text), None, None))

    for j in range(len(subchapters)-1):
        sub_start, sub_id, sub_name = subchapters[j]
        sub_end = subchapters[j+1][0]
        sub_text = chap_text[sub_start:sub_end].strip()
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", sub_text) if p.strip()]

        for k, para in enumerate(paragraphs, 1):
            meta = {
                "bookname": book_title,
                "chapter_id": chapter_id,
                "chapter_name": chapter_name,
                "sub_chapter_name": sub_name,
                "paragraph_id": f"{k:02d}",
                "content": para
            }
            doc_text = f"책제목: {book_title}\nchapter_id: {chapter_id}\n챕터명: {chapter_name}\n소제목: {sub_name}\n문단번호: {k:02d}\n내용:\n{para}"
            documents.append(Document(page_content=doc_text, metadata=meta))

# JSON 파일로 저장
output_path = "chunk/childcare_guide_chunks.json"
documents_data = [
    {"page_content": doc.page_content, "metadata": doc.metadata} 
    for doc in documents
]

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(documents_data, f, ensure_ascii=False, indent=2)

print(f"총 {len(meta)}개의 청크가 {output_path}에 저장되었습니다.")

# 3. 임베딩 모델 초기화 (ko-sbert-nli)
embedding_model = HuggingFaceEmbeddings(
    model_name="jhgan/ko-sbert-nli",
    model_kwargs={'device': 'cpu'},  # GPU 있으면 'cuda'로 변경
    encode_kwargs={'normalize_embeddings': True}
)

# 4. Chroma 벡터 스토어 생성
persist_dir = "./vector_db"
vectorstore = Chroma(
    embedding_function=embedding_model,
    persist_directory=persist_dir
)

# 문서 추가 후 persist
vectorstore.add_documents(documents)
vectorstore.persist()

# 5. 검색용 Retriever 생성
vectorstore = Chroma(
    embedding_function=embedding_model,
    persist_directory=persist_dir
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# 6. LLM에 RAG 방식으로 연결
gemini = GeminiClient(api_key=config.GOOGLE_API_KEY)

query = "신생아 수면 습관을 개선하는 방법은?"
docs = retriever.get_relevant_documents(query)
print(f"검색된 문서 수: {len(docs)}")
for d in docs:
    print(d.metadata, d.page_content[:100], "...")
response = gemini.generate_response(query, context=[{"source": d.metadata.get("chapter_name",""), "content": d.page_content} for d in docs])
context_list = [{"source": d.metadata.get("chapter_name",""), "content": d.page_content} for d in docs]
print("Context 예시:", context_list[:1])
print(response)