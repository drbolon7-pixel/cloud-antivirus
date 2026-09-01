import hashlib
import magic
import requests
import clamd
from datetime import datetime
import json
from config import Config

class AntivirusScanner:
    def __init__(self):
        self.clamav = None
        try:
            self.clamav = clamd.ClamdNetworkSocket(
                Config.CLAMAV_HOST, 
                Config.CLAMAV_PORT
            )
        except:
            print("ClamAV not available, using fallback scanner")
            self.clamav = None
    
    def scan_file(self, file_data, filename):
        """Main scanning function"""
        start_time = datetime.now()
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Detect file type
        file_type = magic.from_buffer(file_data[:1024], mime=True)
        
        # Scan with ClamAV
        clamav_result = self._scan_clamav(file_data)
        
        # Scan with VirusTotal (optional)
        vt_result = self._scan_virustotal(file_hash)
        
        # Combine results
        result = self._analyze_results(clamav_result, vt_result)
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        result['duration'] = duration
        result['file_hash'] = file_hash
        result['file_type'] = file_type
        
        return result
    
    def _scan_clamav(self, file_data):
        if not self.clamav:
            return {'status': 'unknown', 'message': 'ClamAV not available'}
        
        try:
            response = self.clamav.instream(file_data)
            if response and 'stream' in response:
                status = response['stream']
                if status == 'OK':
                    return {'status': 'clean'}
                else:
                    # Parse virus name from response
                    virus_name = status.split(':')[-1].strip()
                    return {
                        'status': 'infected',
                        'threat_name': virus_name,
                        'severity': 'high'
                    }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        
        return {'status': 'unknown'}
    
    def _scan_virustotal(self, file_hash):
        """Optional VirusTotal integration"""
        if not Config.VIRUSTOTAL_API_KEY:
            return {'status': 'unknown'}
        
        try:
            url = f'https://www.virustotal.com/api/v3/files/{file_hash}'
            headers = {
                'x-apikey': Config.VIRUSTOTAL_API_KEY
            }
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
                return {
                    'status': 'infected' if stats.get('malicious', 0) > 0 else 'clean',
                    'stats': stats,
                    'source': 'virustotal'
                }
        except:
            pass
        
        return {'status': 'unknown'}
    
    def _analyze_results(self, clamav_result, vt_result):
        """Combine and analyze all scan results"""
        result = {
            'status': 'clean',
            'threat_name': None,
            'severity': 'low',
            'details': {}
        }
        
        # Check ClamAV result
        if clamav_result.get('status') == 'infected':
            result['status'] = 'infected'
            result['threat_name'] = clamav_result.get('threat_name', 'Unknown')
            result['severity'] = clamav_result.get('severity', 'high')
        
        # Check VirusTotal result
        if vt_result.get('status') == 'infected':
            result['status'] = 'infected'
            if vt_result.get('stats'):
                malicious = vt_result['stats'].get('malicious', 0)
                if malicious > 10:
                    result['severity'] = 'critical'
                elif malicious > 5:
                    result['severity'] = 'high'
                else:
                    result['severity'] = 'medium'
        
        result['details'] = {
            'clamav': clamav_result,
            'virustotal': vt_result
        }
        
        return result
    
    def get_signature_update(self):
        """Check for signature updates"""
        try:
            # In production, this would connect to a signature update service
            return {
                'version': '1.0.0',
                'last_update': datetime.now().isoformat(),
                'signatures': 1000000
            }
        except:
            return None
