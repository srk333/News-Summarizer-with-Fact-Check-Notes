from flask import Blueprint, request, jsonify
from backend.services.article_extractor import ArticleExtractor
from backend.services.summarizer import Summarizer
from backend.services.claim_extractor import ClaimExtractor
from backend.services.search_service import SearchService
from backend.services.rag_service import RAGService
from backend.services.fact_checker import FactChecker
from backend.models.article import Article
from backend.models.claim import Claim
from backend.models.evidence import Evidence
from backend.database.db import db
from backend.utils.validators import is_valid_url
import json

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    text = data.get('text')
    
    if not url and not text:
        return jsonify({"error": "Either URL or text must be provided."}), 400
        
    if url and not is_valid_url(url):
        return jsonify({"error": "Invalid URL provided."}), 400

    try:
        # 1. Extraction
        if url:
            article_data = ArticleExtractor.extract_from_url(url)
        else:
            article_data = ArticleExtractor.extract_from_text(text)
            
        # 2. Summarization
        summarizer = Summarizer()
        summary_result = summarizer.summarize(article_data['text'])
        
        # Save basic article
        article = Article(
            url=url if url else None,
            title=article_data['title'],
            source=article_data['source'],
            article_text=article_data['text'],
            summary=json.dumps(summary_result.get('summary', '')),
            key_points=json.dumps(summary_result.get('key_points', []))
        )
        db.session.add(article)
        db.session.flush() # get ID
        
        # 3. Claim Extraction
        claim_extractor = ClaimExtractor()
        claims_data = claim_extractor.extract_claims(article_data['text'])
        
        # Initialize services
        search_service = SearchService()
        rag_service = RAGService()
        fact_checker = FactChecker()
        
        # 4. Process Claims
        for claim_dict in claims_data:
            claim_text = claim_dict.get('claim_text')
            
            # Save claim
            claim = Claim(
                article_id=article.id,
                claim_text=claim_text,
                claim_type=claim_dict.get('claim_type'),
                importance=claim_dict.get('importance')
            )
            db.session.add(claim)
            db.session.flush() # get ID
            
            # 5. Search for Evidence
            try:
                raw_evidence = search_service.search_evidence(claim_text)
            except Exception as e:
                # API not configured or failed
                raw_evidence = []
                
            # 6. RAG: Process Evidence
            if raw_evidence:
                refined_evidence = rag_service.process_evidence_for_claim(claim_text, raw_evidence)
            else:
                refined_evidence = []
                
            # Save Evidence to DB
            saved_evidence_list = []
            # We want unique sources to show to the user, not just chunks. 
            # We will save the original raw evidence as sources, and use refined for fact checking.
            for ev in raw_evidence:
                db_ev = Evidence(
                    claim_id=claim.id,
                    source_title=ev['title'],
                    source_url=ev['url'],
                    source_domain=ev['domain'],
                    evidence_text=ev['text'][:2000], # store a snippet
                    source_quality=ev['quality']
                )
                db.session.add(db_ev)
                saved_evidence_list.append(ev)
                
            # 7. Fact Check Analysis
            fact_check_result = fact_checker.check_claim(claim_text, refined_evidence)
            
            claim.verdict = fact_check_result.get('verdict', 'UNABLE TO VERIFY')
            claim.fact_check_note = fact_check_result.get('fact_check_note', 'No notes.')
            
        db.session.commit()
        
        # Return full article with claims and evidence
        return jsonify(article.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
