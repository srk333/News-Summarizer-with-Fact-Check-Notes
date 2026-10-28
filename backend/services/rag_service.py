from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from backend.config import Config


class RAGService:
    def __init__(self):
        embed_kwargs = dict(
            api_key=Config.OPENAI_API_KEY,
            model=Config.EMBEDDING_MODEL_NAME,
        )
        if Config.OPENAI_BASE_URL:
            embed_kwargs["base_url"] = Config.OPENAI_BASE_URL
        self.embeddings = OpenAIEmbeddings(**embed_kwargs)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

    def process_evidence_for_claim(self, claim_text, evidence_list):
        if not evidence_list:
            return []

        documents = []
        for ev in evidence_list:
            text = ev.get('text', '')
            if not text.strip():
                continue
            chunks = self.text_splitter.split_text(text)
            for chunk in chunks:
                documents.append(Document(
                    page_content=chunk,
                    metadata={
                        "source_domain": ev.get('domain', 'Unknown'),
                        "source_url": ev.get('url', ''),
                        "source_title": ev.get('title', ''),
                        "quality": ev.get('quality', 'LOWER TRUST')
                    }
                ))

        if not documents:
            return self._raw_fallback(evidence_list)

        try:
            vectorstore = FAISS.from_documents(documents=documents, embedding=self.embeddings)
            retriever = vectorstore.as_retriever(search_kwargs={"k": min(4, len(documents))})
            relevant_docs = retriever.invoke(claim_text)

            refined_evidence = []
            for doc in relevant_docs:
                refined_evidence.append({
                    'domain': doc.metadata.get('source_domain', 'Unknown'),
                    'url': doc.metadata.get('source_url', ''),
                    'title': doc.metadata.get('source_title', ''),
                    'quality': doc.metadata.get('quality', 'LOWER TRUST'),
                    'text': doc.page_content
                })
            return refined_evidence
        except Exception as e:
            print(f"RAG processing failed, using raw evidence: {str(e)}")
            return self._raw_fallback(evidence_list)

    def _raw_fallback(self, evidence_list):
        return [{
            'domain': ev.get('domain', 'Unknown'),
            'url': ev.get('url', ''),
            'title': ev.get('title', ''),
            'quality': ev.get('quality', 'LOWER TRUST'),
            'text': ev.get('text', '')[:500]
        } for ev in evidence_list[:4]]
