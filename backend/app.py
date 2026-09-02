from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import jwt
import bcrypt
import os
import uuid
from datetime import datetime, timedelta
from functools import wraps

from config import Config
from models import db, User, ScanHistory, VirusSignature
from database import init_db
from scanner import AntivirusScanner

app = Flask(__name__, static_folder='../frontend')
app.config.from_object(Config)
CORS(app)

init_db(app)
scanner = AntivirusScanner()

# Authentication middleware
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            token = token.split(' ')[1]  # Bearer token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Invalid token!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if user exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 409
    
    # Hash password
    hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user = User(
        username=data['username'],
        email=data.get('email', ''),
        password_hash=hashed.decode('utf-8'),
        api_key=str(uuid.uuid4())
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User created successfully',
        'api_key': user.api_key
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing credentials'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Generate JWT
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(seconds=app.config['JWT_EXPIRATION'])
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    })

@app.route('/api/scan', methods=['POST'])
@token_required
def scan_file(current_user):
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    # Check file size
    file_data = file.read()
    if len(file_data) > app.config['MAX_FILE_SIZE']:
        return jsonify({'message': 'File too large'}), 413
    
    # Scan file
    result = scanner.scan_file(file_data, file.filename)
    
    # Save scan history
    scan = ScanHistory(
        user_id=current_user.id,
        filename=secure_filename(file.filename),
        file_hash=result.get('file_hash'),
        file_size=len(file_data),
        scan_status=result['status'],
        threat_name=result.get('threat_name'),
        scan_result=result,
        scan_duration=result.get('duration', 0)
    )
    db.session.add(scan)
    db.session.commit()
    
    return jsonify({
        'scan_id': scan.id,
        'status': result['status'],
        'threat_name': result.get('threat_name'),
        'severity': result.get('severity', 'low'),
        'file_hash': result.get('file_hash'),
        'scan_duration': result.get('duration'),
        'details': result.get('details', {})
    })

@app.route('/api/scans', methods=['GET'])
@token_required
def get_scans(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    scans = ScanHistory.query.filter_by(user_id=current_user.id)\
        .order_by(ScanHistory.scanned_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'scans': [{
            'id': s.id,
            'filename': s.filename,
            'status': s.scan_status,
            'threat_name': s.threat_name,
            'scanned_at': s.scanned_at.isoformat(),
            'file_size': s.file_size,
            'scan_duration': s.scan_duration
        } for s in scans.items],
        'total': scans.total,
        'page': page,
        'pages': scans.pages
    })

@app.route('/api/scan/<int:scan_id>', methods=['GET'])
@token_required
def get_scan_detail(current_user, scan_id):
    scan = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first()
    
    if not scan:
        return jsonify({'message': 'Scan not found'}), 404
    
    return jsonify({
        'id': scan.id,
        'filename': scan.filename,
        'file_hash': scan.file_hash,
        'file_size': scan.file_size,
        'status': scan.scan_status,
        'threat_name': scan.threat_name,
        'scan_result': scan.scan_result,
        'scanned_at': scan.scanned_at.isoformat(),
        'scan_duration': scan.scan_duration
    })

@app.route('/api/signatures/update', methods=['POST'])
@token_required
def update_signatures(current_user):
    # Only admin can update signatures
    if current_user.username != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    # In production, download latest signatures from database
    # For demo, return mock data
    return jsonify({
        'message': 'Signatures updated successfully',
        'version': '1.0.1',
        'signatures_count': 1000000
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'scanner': 'active'
    })

# Serve frontend
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
