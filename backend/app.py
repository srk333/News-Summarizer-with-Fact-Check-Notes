import os
from flask import Flask, jsonify
from flask_cors import CORS
from backend.config import Config
from backend.database.db import db
from backend.routes.analysis_routes import analysis_bp
from backend.routes.history_routes import history_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app)
    db.init_app(app)
    
    app.register_blueprint(analysis_bp)
    app.register_blueprint(history_bp)
    
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({"status": "healthy"}), 200
        
    with app.app_context():
        db.create_all()
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
