"""
Web server for UniFi Documenter - provides real-time progress tracking and results viewing
"""
import os
import json
import logging
from datetime import datetime
import pytz
from pathlib import Path
from typing import Dict, List, Optional
from flask import Flask, render_template, jsonify, send_from_directory
from threading import Lock

from .config import Config

logger = logging.getLogger('unifi_documenter')


def _get_now_tz(config):
    """Get timezone-aware current time"""
    try:
        tz = pytz.timezone(config.TIMEZONE if hasattr(config, 'TIMEZONE') else 'UTC')
        return datetime.now(tz)
    except:
        return datetime.now()


class ProgressTracker:
    """Thread-safe progress tracking for analysis jobs"""
    
    def __init__(self):
        self.lock = Lock()
        self.current_job = None
        self.jobs_history = []
        
    def start_job(self, job_id: str, total_documents: int, groups: Dict):
        """Start tracking a new job"""
        with self.lock:
            self.current_job = {
                'id': job_id,
                'start_time': (_get_now_tz(self.config) if self.config else datetime.now()).isoformat(),
                'total_documents': total_documents,
                'groups': groups,
                'current_group': None,
                'current_batch': 0,
                'total_batches': 0,
                'processed_documents': 0,
                'status': 'running',
                'output_dir': None
            }
    
    def update_group(self, group_name: str, total_batches: int):
        """Update current processing group"""
        with self.lock:
            if self.current_job:
                self.current_job['current_group'] = group_name
                self.current_job['total_batches'] = total_batches
                self.current_job['current_batch'] = 0
    
    def update_batch(self, batch_num: int, documents_count: int):
        """Update batch progress"""
        with self.lock:
            if self.current_job:
                self.current_job['current_batch'] = batch_num
                self.current_job['processed_documents'] += documents_count
    
    def complete_job(self, output_dir: str, success: bool = True):
        """Mark job as complete"""
        with self.lock:
            if self.current_job:
                self.current_job['end_time'] = (_get_now_tz(self.config) if self.config else datetime.now()).isoformat()
                self.current_job['status'] = 'completed' if success else 'failed'
                self.current_job['output_dir'] = output_dir
                self.jobs_history.insert(0, self.current_job.copy())
                self.current_job = None
                
                # Keep only last 50 jobs
                if len(self.jobs_history) > 50:
                    self.jobs_history = self.jobs_history[:50]
    
    def get_current_status(self) -> Dict:
        """Get current job status"""
        with self.lock:
            if self.current_job:
                progress = (self.current_job['processed_documents'] / 
                           self.current_job['total_documents'] * 100) if self.current_job['total_documents'] > 0 else 0
                return {
                    **self.current_job,
                    'progress_percent': round(progress, 1)
                }
            return None
    
    def get_jobs_history(self) -> List[Dict]:
        """Get job history"""
        with self.lock:
            return self.jobs_history.copy()


# Global progress tracker
progress_tracker = ProgressTracker()


def create_app(config: Config) -> Flask:
    """Create Flask application"""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    app.config['OUTPUT_DIR'] = config.OUTPUT_DIR
    
    @app.route('/')
    def index():
        """Dashboard page"""
        return render_template('dashboard.html')
    
    @app.route('/api/status')
    def get_status():
        """Get current job status"""
        current = progress_tracker.get_current_status()
        history = progress_tracker.get_jobs_history()
        return jsonify({
            'current_job': current,
            'jobs_history': history[:10]  # Last 10 jobs
        })
    
    @app.route('/api/jobs')
    def get_jobs():
        """Get all jobs"""
        return jsonify(progress_tracker.get_jobs_history())
    
    @app.route('/job/<job_id>')
    def get_job(job_id):
        """Get specific job details page"""
        jobs = progress_tracker.get_jobs_history()
        job = next((j for j in jobs if j['id'] == job_id), None)
        if not job:
            return "Job not found", 404
        
        # Get output files if job is completed
        files = []
        if job['status'] == 'completed' and job.get('output_dir'):
            analysis_dir = os.path.join(job['output_dir'], 'analysis')
            if os.path.exists(analysis_dir):
                for file in os.listdir(analysis_dir):
                    if file.endswith(('.html', '.md')):
                        file_path = os.path.join(analysis_dir, file)
                        files.append({
                            'name': file,
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        })
        
        return render_template('job_details.html', job=job, files=files)
    
    @app.route('/api/job/<job_id>')
    def get_job_api(job_id):
        """Get specific job details as JSON (API endpoint)"""
        jobs = progress_tracker.get_jobs_history()
        job = next((j for j in jobs if j['id'] == job_id), None)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Get output files if job is completed
        files = []
        if job['status'] == 'completed' and job.get('output_dir'):
            analysis_dir = os.path.join(job['output_dir'], 'analysis')
            if os.path.exists(analysis_dir):
                for file in os.listdir(analysis_dir):
                    if file.endswith(('.html', '.md')):
                        file_path = os.path.join(analysis_dir, file)
                        files.append({
                            'name': file,
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        })
        
        return jsonify({
            **job,
            'files': files
        })
    
    @app.route('/view/<job_id>/<filename>')
    def view_file(job_id, filename):
        """View analysis file"""
        jobs = progress_tracker.get_jobs_history()
        job = next((j for j in jobs if j['id'] == job_id), None)
        if not job or not job.get('output_dir'):
            return "Job not found", 404
        
        analysis_dir = os.path.join(job['output_dir'], 'analysis')
        return send_from_directory(analysis_dir, filename)
    
    @app.route('/download/<job_id>/<filename>')
    def download_file(job_id, filename):
        """Download analysis file"""
        jobs = progress_tracker.get_jobs_history()
        job = next((j for j in jobs if j['id'] == job_id), None)
        if not job or not job.get('output_dir'):
            return "Job not found", 404
        
        analysis_dir = os.path.join(job['output_dir'], 'analysis')
        return send_from_directory(analysis_dir, filename, as_attachment=True)
    
    return app


def start_web_server(config: Config):
    """Start the web server in a separate thread"""
    if not config.WEB_ENABLED:
        logger.info("Web server disabled")
        return
    
    app = create_app(config)
    logger.info(f"Starting web server on port {config.WEB_PORT}")
    
    try:
        app.run(host='0.0.0.0', port=config.WEB_PORT, threaded=True, debug=False)
    except Exception as e:
        logger.error(f"Failed to start web server: {str(e)}")
