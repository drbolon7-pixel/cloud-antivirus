from flask_sqlalchemy import SQLAlchemy
from models import db, User, ScanHistory, VirusSignature

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@antivirus.com',
                password_hash='temporary'  # Will be hashed on first login
            )
            db.session.add(admin)
            db.session.commit()

def save_scan_result(user_id, filename, file_hash, file_size, result):
    scan = ScanHistory(
        user_id=user_id,
        filename=filename,
        file_hash=file_hash,
        file_size=file_size,
        scan_status=result['status'],
        threat_name=result.get('threat_name'),
        scan_result=result,
        scan_duration=result.get('duration', 0)
    )
    db.session.add(scan)
    db.session.commit()
    return scan
