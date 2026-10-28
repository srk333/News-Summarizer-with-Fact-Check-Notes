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
import traceback

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided."}), 400

    url = data.get('url', '').strip()
    text = data.get('text', '').strip()

    if not url and not text:
        return jsonify({"error": "Either URL or text must be provided."}), 400

    if url and not is_valid_url(url):
        return jsonify({"error": "Invalid URL provided. Please enter a full URL starting with http:// or https://"}), 400

    try:
        # STEP 1: Extract article
        if url:
            try:
                article_data = ArticleExtractor.extract_from_url(url)
            except Exception as e:
                return jsonify({"error": f"Could not extract article from URL: {str(e)}"}), 400
        else:
            try:
                article_data = ArticleExtractor.extract_from_text(text)
            except Exception as e:
                return jsonify({"error": f"Invalid text input: {str(e)}"}), 400

        if not article_data.get('text') or len(article_data['text'].strip()) < 30:
            return jsonify({"error": "Article content is too short or could not be extracted. Some sites (MSN, Bing News) block scrapers — please copy and paste the article text directly into the 'Paste Text' tab instead."}), 400

        # STEP 2: Summarization
        try:
            summarizer = Summarizer()
            summary_result = summarizer.summarize(article_data['text'])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        # STEP 3: Save article to DB
        article = Article(
            url=url if url else None,
            title=article_data.get('title', 'Untitled Article'),
            source=article_data.get('source', 'Unknown'),
            article_text=article_data['text'][:10000],
            summary=json.dumps(summary_result.get('summary', '')),
            key_points=json.dumps(summary_result.get('key_points', []))
        )
        db.session.add(article)
        db.session.flush()

        # STEP 4: Claim extraction
        try:
            claim_extractor = ClaimExtractor()
            claims_data = claim_extractor.extract_claims(article_data['text'])
        except Exception as e:
            claims_data = []

        # STEP 5: Initialize services
        search_service = SearchService()
        rag_service = RAGService()
        fact_checker = FactChecker()

        # STEP 6: Process each claim
        for claim_dict in claims_data:
            claim_text = claim_dict.get('claim_text', '')
            if not claim_text:
                continue

            claim = Claim(
                article_id=article.id,
                claim_text=claim_text,
                claim_type=claim_dict.get('claim_type', 'General'),
                importance=claim_dict.get('importance', 'MEDIUM')
            )
            db.session.add(claim)
            db.session.flush()

            # Search for evidence
            try:
                raw_evidence = search_service.search_evidence(claim_text)
            except Exception as e:
                raw_evidence = []

            # RAG processing
            if raw_evidence:
                try:
                    refined_evidence = rag_service.process_evidence_for_claim(claim_text, raw_evidence)
                except Exception as e:
                    refined_evidence = raw_evidence
            else:
                refined_evidence = []

            # Save evidence to DB
            for ev in raw_evidence:
                db_ev = Evidence(
                    claim_id=claim.id,
                    source_title=ev.get('title', 'Unknown'),
                    source_url=ev.get('url', ''),
                    source_domain=ev.get('domain', 'Unknown'),
                    evidence_text=ev.get('text', '')[:2000],
                    source_quality=ev.get('quality', 'LOWER TRUST')
                )
                db.session.add(db_ev)

            # Fact check
            fact_check_result = fact_checker.check_claim(claim_text, refined_evidence)
            claim.verdict = fact_check_result.get('verdict', 'UNABLE TO VERIFY')
            claim.fact_check_note = fact_check_result.get('fact_check_note', 'No notes available.')

        db.session.commit()
        return jsonify(article.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        print(traceback.format_exc())
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500
