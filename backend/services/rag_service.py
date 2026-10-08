from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from backend.config import Config
from langchain.docstore.document import Document

class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(api_key=Config.OPENAI_API_KEY)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
    def process_evidence_for_claim(self, claim_text, evidence_list):
        if not evidence_list:
            return []
            
        documents = []
        for ev in evidence_list:
            # We treat each piece of evidence as a document to split
            chunks = self.text_splitter.split_text(ev['text'])
            for chunk in chunks:
                documents.append(Document(
                    page_content=chunk,
                    metadata={"source_domain": ev['domain'], "source_url": ev['url'], "source_title": ev['title'], "quality": ev['quality']}
                ))
                
        if not documents:
            return []
            
        # Create temporary FAISS in-memory vector store
        vectorstore = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )
        
        # Retrieve top 4 most relevant chunks to the claim
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        relevant_docs = retriever.invoke(claim_text)
        
        # Convert back to list format for FactChecker
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

