#!/usr/bin/env python3
"""
Marina Web Client - Secure GUI Interface for Marina CLI

This web application provides a user-friendly interface for Marina's CLI functionality
while ensuring security through session isolation and sandboxed file operations.

Key Security Features:
- Each web session gets a dedicated workspace folder
- Users cannot access files outside their session directory
- All file operations are sandboxed
- Session-based authentication and isolation

Author: Marina AI Assistant
"""

import os
import sys
import json
import uuid
import shutil
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps

import flask
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Add Marina's parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate random secret key

# Configuration
UPLOAD_FOLDER = Path(__file__).parent / 'sessions'
UPLOAD_FOLDER.mkdir(exist_ok=True)
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'json', 'csv', 'xlsx', 'docx',
    'py', 'js', 'html', 'css', 'md', 'xml', 'yml', 'yaml'
}

# Marina CLI executable path
MARINA_CLI_PATH = Path(__file__).parent.parent / 'marina_cli.py'

class SessionManager:
    """Manages user sessions and their isolated workspaces"""
    
    @staticmethod
    def get_session_id():
        """Get or create a session ID"""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            session['created_at'] = datetime.now().isoformat()
        return session['session_id']
    
    @staticmethod
    def get_session_dir():
        """Get the session directory path"""
        session_id = SessionManager.get_session_id()
        session_dir = UPLOAD_FOLDER / session_id
        session_dir.mkdir(exist_ok=True)
        return session_dir
    
    @staticmethod
    def is_safe_path(path, base_dir):
        """Check if a path is within the allowed base directory"""
        try:
            real_path = Path(path).resolve()
            real_base = Path(base_dir).resolve()
            return str(real_path).startswith(str(real_base))
        except:
            return False

class MarinaCliExecutor:
    """Executes Marina CLI commands in a secure, isolated environment"""
    
    @staticmethod
    def execute_command(cmd_args, session_dir=None, timeout=300):
        """
        Execute a Marina CLI command safely
        
        Args:
            cmd_args (list): Command arguments to pass to marina_cli.py
            session_dir (Path): Session directory for file isolation
            timeout (int): Command timeout in seconds
            
        Returns:
            dict: Result containing stdout, stderr, return_code
        """
        try:
            # Build the full command
            full_cmd = ['python3', str(MARINA_CLI_PATH)] + cmd_args
            
            # Set up environment
            env = os.environ.copy()
            if session_dir:
                env['MARINA_SESSION_DIR'] = str(session_dir)
                env['MARINA_SAFE_MODE'] = '1'
            
            # Execute the command
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=session_dir if session_dir else None,
                env=env
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'return_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1
            }

def session_required(f):
    """Decorator to ensure session exists"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        SessionManager.get_session_id()  # This creates session if needed
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@session_required
def index():
    """Main dashboard"""
    session_info = {
        'session_id': session['session_id'][:8] + '...',  # Show only part of ID
        'created_at': session.get('created_at', 'Unknown'),
        'workspace': str(SessionManager.get_session_dir().name)
    }
    return render_template('index.html', session_info=session_info)

@app.route('/llm')
@session_required
def llm_interface():
    """LLM routing and task execution interface"""
    return render_template('llm.html')

@app.route('/superchat')
@session_required
def superchat_interface():
    """SuperChat - Multi-LLM chat interface"""
    return render_template('superchat.html')

@app.route('/api/llm/execute', methods=['POST'])
@session_required
def api_llm_execute():
    """Execute LLM task"""
    try:
        data = request.get_json()
        task = data.get('task', '').strip()
        
        if not task:
            return jsonify({'error': 'Task is required'}), 400
        
        # Build command arguments
        cmd_args = ['llm', task]
        
        # Add optional parameters
        if data.get('tokens'):
            cmd_args.extend(['--tokens', str(data['tokens'])])
        if data.get('model'):
            cmd_args.extend(['--model', data['model']])
        if data.get('save'):
            cmd_args.append('--save')
        if data.get('format') and data.get('format') != 'text':
            cmd_args.extend(['--format', data['format']])
        if data.get('language'):
            cmd_args.extend(['--language', data['language']])
        
        # Execute command
        session_dir = SessionManager.get_session_dir()
        result = MarinaCliExecutor.execute_command(cmd_args, session_dir)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/superchat/execute', methods=['POST'])
@session_required
def api_superchat_execute():
    """Execute SuperChat multi-LLM task using proper LLM router"""
    try:
        import sys
        import os
        # Add parent directory to path to import LLM router
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
            
        from llm import llm_router
        
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        enabled_models = data.get('enabled_models', [])
        whisper_mode = data.get('whisper_mode', False)
        shout_mode = data.get('shout_mode', False)
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        if not enabled_models:
            return jsonify({'error': 'At least one model must be enabled'}), 400
        
        results = []
        
        # Map UI model names to internal names
        model_mapping = {
            'GPT-4': 'gpt',
            'Gemini': 'gemini',
            'Claude': 'claude',
            'DeepSeek': 'deepseek',
            'LLaMA3': 'llama',
            'Mistral': 'mistral'
        }
        
        # Convert enabled models to internal names
        internal_models = [model_mapping.get(model, model.lower()) for model in enabled_models]
        
        # If whisper mode, send to only one (first enabled) LLM
        if whisper_mode and not shout_mode:
            internal_models = internal_models[:1]
        
        # Estimate token count
        token_estimate = len(prompt.split()) * 1.3
        
        for i, model in enumerate(internal_models):
            start_time = datetime.now()
            try:
                # Use the LLM router for proper routing
                selected_model, response = llm_router.route_task(
                    prompt, 
                    token_estimate, 
                    run=True, 
                    force_model=model
                )
                
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                # Determine success based on response
                success = response and not (isinstance(response, str) and response.startswith('[ERROR]'))
                
                result = {
                    'model': enabled_models[i],  # Use original UI model name
                    'success': success,
                    'stdout': response if success else '',
                    'stderr': response if not success else '',
                    'return_code': 0 if success else 1,
                    'timestamp': end_time.isoformat(),
                    'start_time': start_time.isoformat(),
                    'execution_time': execution_time,
                    'prompt_length': len(prompt),
                    'response_length': len(response) if response else 0,
                    'selected_model': selected_model,  # Track which model was actually used
                    'forced_model': model  # Track which model was requested
                }
                
                results.append(result)
                
            except Exception as e:
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                results.append({
                    'model': enabled_models[i],
                    'success': False,
                    'stdout': '',
                    'stderr': f'Model execution failed: {str(e)}',
                    'return_code': -1,
                    'timestamp': end_time.isoformat(),
                    'start_time': start_time.isoformat(),
                    'execution_time': execution_time,
                    'prompt_length': len(prompt),
                    'response_length': 0,
                    'forced_model': model,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'prompt': prompt,
            'whisper_mode': whisper_mode,
            'shout_mode': shout_mode,
            'total_models': len(enabled_models),
            'execution_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/context')
@session_required
def context_interface():
    """Context scanning interface"""
    return render_template('context.html')

@app.route('/api/context/scan', methods=['POST'])
@session_required
def api_context_scan():
    """Execute context scan"""
    try:
        data = request.get_json()
        
        # Build command arguments
        cmd_args = ['context']
        
        if data.get('mode'):
            cmd_args.extend(['--mode', data['mode']])
        if data.get('whitelist'):
            cmd_args.extend(['--whitelist'] + data['whitelist'])
        if data.get('blacklist'):
            cmd_args.extend(['--blacklist'] + data['blacklist'])
        
        # Execute command
        session_dir = SessionManager.get_session_dir()
        result = MarinaCliExecutor.execute_command(cmd_args, session_dir)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/models')
@session_required
def models_interface():
    """Model management interface"""
    return render_template('models.html')

@app.route('/api/models/<action>', methods=['POST', 'GET'])
@session_required
def api_models(action):
    """Model management API"""
    try:
        if action == 'status':
            cmd_args = ['models', 'status']
        elif action == 'suspend':
            data = request.get_json() if request.method == 'POST' else {}
            cmd_args = ['models', 'suspend']
            if data.get('all'):
                cmd_args.append('--all')
            elif data.get('model'):
                cmd_args.extend(['--model', data['model']])
        elif action == 'load':
            data = request.get_json()
            cmd_args = ['models', 'load']
            if data.get('model'):
                cmd_args.extend(['--model', data['model']])
            if data.get('task'):
                cmd_args.extend(['--task', data['task']])
        elif action == 'recommend':
            cmd_args = ['models', 'recommend']
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        # Execute command
        session_dir = SessionManager.get_session_dir()
        result = MarinaCliExecutor.execute_command(cmd_args, session_dir)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scraper')
@session_required
def scraper_interface():
    """Knowledge scraping interface"""
    return render_template('scraper.html')

@app.route('/api/scraper/execute', methods=['POST'])
@session_required
def api_scraper_execute():
    """Execute scraping task with enhanced analysis"""
    try:
        data = request.get_json()
        scraper_name = data.get('scraper', 'general')
        platform = data.get('platform', 'generic')
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Try to use enhanced scraper registry
        try:
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
            
            from knowledge_scrapers.scraper_registry_v2 import ScraperRegistry, ScrapingJob
            
            registry = ScraperRegistry()
            
            # Build parameters
            parameters = {
                'delay_between_requests': data.get('delay', 1.5),
                'max_pages': data.get('max_items', 10)
            }
            
            # Add scraper-specific parameters
            if scraper_name == 'academic' and data.get('query'):
                parameters['search_query'] = data['query']
                parameters['max_papers'] = data.get('max_items', 10)
            elif scraper_name == 'job' and data.get('query'):
                parameters['max_jobs'] = data.get('max_items', 10)
                url = f"https://www.indeed.com/jobs?q={data['query'].replace(' ', '+')}"
            elif scraper_name in ['ecommerce', 'general']:
                parameters['root_url'] = url
            elif scraper_name == 'social_media':
                parameters['max_posts'] = data.get('max_items', 10)
            elif scraper_name == 'forum':
                parameters['max_threads'] = data.get('max_items', 10)
                parameters['max_posts_per_thread'] = 25
            elif scraper_name == 'documentation':
                parameters['max_pages'] = data.get('max_items', 20)
            
            # Create and execute scraping job
            job = ScrapingJob(
                scraper_name=scraper_name,
                platform=platform,
                target_url=url,
                parameters=parameters
            )
            
            result = registry.run_scraping_job(job)
            
            # Enhanced result formatting
            if result['status'] == 'success':
                enhanced_result = {
                    'success': True,
                    'stdout': f"Scraping completed successfully!\n" +
                             f"Items scraped: {result['results_count']}\n" +
                             f"Execution time: {result['execution_time']:.2f}s",
                    'stderr': '',
                    'return_code': 0,
                    'results_count': result['results_count'],
                    'execution_time': result['execution_time']
                }
                
                # Add analysis data if available
                if 'pre_scrape_analysis' in result:
                    analysis = result['pre_scrape_analysis']
                    enhanced_result['pre_scrape_analysis'] = {
                        'risk_score': analysis.get('risk_score', 0),
                        'recommended_delay': analysis.get('recommended_delay', 1.5),
                        'anti_bot_measures': analysis.get('anti_bot_measures', []),
                        'estimated_pages': analysis.get('estimated_pages', 0)
                    }
                    enhanced_result['stdout'] += f"\nRisk Score: {analysis.get('risk_score', 0):.1f}/10"
                    enhanced_result['stdout'] += f"\nRecommended Delay: {analysis.get('recommended_delay', 1.5):.1f}s"
                
                if 'scraping_strategy' in result:
                    strategy = result['scraping_strategy']
                    enhanced_result['scraping_strategy'] = strategy
                    enhanced_result['stdout'] += f"\nRecommended Scraper: {strategy.get('recommended_scraper', 'N/A')}"
                    enhanced_result['stdout'] += f"\nSuccess Probability: {strategy.get('success_probability', 0):.2f}"
                
                if 'post_scrape_analysis' in result:
                    post_analysis = result['post_scrape_analysis']
                    enhanced_result['post_scrape_analysis'] = post_analysis
                    enhanced_result['stdout'] += f"\nContent Quality: {post_analysis.get('content_quality_score', 0):.2f}"
                    enhanced_result['stdout'] += f"\nAverage Content Length: {post_analysis.get('average_content_length', 0):.0f} chars"
                
                return jsonify(enhanced_result)
            else:
                return jsonify({
                    'success': False,
                    'stdout': '',
                    'stderr': result.get('error', 'Unknown error'),
                    'return_code': 1
                })
                
        except ImportError:
            # Fallback to CLI execution
            pass
        
        # Original CLI fallback
        cmd_args = ['scrape', 'run', scraper_name]
        
        # Add optional parameters
        if platform and platform != 'generic':
            cmd_args.extend(['--platform', platform])
        if url:
            cmd_args.extend(['--url', url])
        if data.get('query'):
            cmd_args.extend(['--query', data['query']])
        if data.get('max_items'):
            cmd_args.extend(['--max-items', str(data['max_items'])])
        if data.get('delay'):
            cmd_args.extend(['--delay', str(data['delay'])])
        
        # Execute command (with longer timeout for scraping)
        session_dir = SessionManager.get_session_dir()
        result = MarinaCliExecutor.execute_command(cmd_args, session_dir, timeout=3600)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/feedback')
@session_required
def feedback_interface():
    """Feedback system interface"""
    return render_template('feedback.html')

@app.route('/api/feedback/<action>', methods=['POST', 'GET'])
@session_required
def api_feedback(action):
    """Feedback system API"""
    try:
        if action == 'analyze':
            data = request.get_json() if request.method == 'POST' else {}
            days = data.get('days', 7)
            cmd_args = ['feedback', 'analyze', '--days', str(days)]
        elif action == 'summary':
            data = request.get_json() if request.method == 'POST' else {}
            days = data.get('days', 7)
            cmd_args = ['feedback', 'summary', '--days', str(days)]
        elif action == 'optimize':
            cmd_args = ['feedback', 'optimize']
        elif action == 'corpus':
            cmd_args = ['feedback', 'corpus']
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        # Execute command
        session_dir = SessionManager.get_session_dir()
        result = MarinaCliExecutor.execute_command(cmd_args, session_dir)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/files')
@session_required
def files_interface():
    """File management interface"""
    session_dir = SessionManager.get_session_dir()
    files = []
    
    try:
        for file_path in session_dir.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(session_dir)
                stat = file_path.stat()
                files.append({
                    'name': file_path.name,
                    'path': str(relative_path),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    except Exception as e:
        pass  # Handle gracefully
    
    return render_template('files.html', files=files)

@app.route('/api/files/upload', methods=['POST'])
@session_required
def api_files_upload():
    """Upload file to session directory"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        session_dir = SessionManager.get_session_dir()
        file_path = session_dir / filename
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset
        
        if size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)'}), 400
        
        # Save file
        file.save(str(file_path))
        
        return jsonify({
            'success': True,
            'filename': filename,
            'size': size
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/download/<path:filename>')
@session_required
def api_files_download(filename):
    """Download file from session directory"""
    try:
        session_dir = SessionManager.get_session_dir()
        file_path = session_dir / filename
        
        # Security check
        if not SessionManager.is_safe_path(file_path, session_dir):
            abort(403)
        
        if not file_path.exists() or not file_path.is_file():
            abort(404)
        
        return send_file(str(file_path), as_attachment=True)
        
    except Exception as e:
        abort(500)

@app.route('/api/files/delete/<path:filename>', methods=['DELETE'])
@session_required
def api_files_delete(filename):
    """Delete file from session directory"""
    try:
        session_dir = SessionManager.get_session_dir()
        file_path = session_dir / filename
        
        # Security check
        if not SessionManager.is_safe_path(file_path, session_dir):
            return jsonify({'error': 'Access denied'}), 403
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        file_path.unlink()
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/info')
@session_required
def api_session_info():
    """Get session information"""
    try:
        session_dir = SessionManager.get_session_dir()
        
        # Count files and calculate total size
        file_count = 0
        total_size = 0
        
        for file_path in session_dir.rglob('*'):
            if file_path.is_file():
                file_count += 1
                total_size += file_path.stat().st_size
        
        return jsonify({
            'session_id': session['session_id'][:8] + '...',
            'created_at': session.get('created_at'),
            'workspace_path': str(session_dir.name),
            'file_count': file_count,
            'total_size': total_size,
            'max_file_size': MAX_FILE_SIZE,
            'allowed_extensions': list(ALLOWED_EXTENSIONS)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/cleanup', methods=['POST'])
@session_required
def api_session_cleanup():
    """Clean up session directory"""
    try:
        session_dir = SessionManager.get_session_dir()
        
        # Remove all files in session directory
        for item in session_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        
        return jsonify({'success': True, 'message': 'Session workspace cleaned'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analysis')
@session_required
def analysis_interface():
    """Analysis dashboard interface"""
    return render_template('analysis.html')

@app.route('/api/analysis/data')
@session_required
def api_analysis_data():
    """Get analysis data from Marina CLI analysis command"""
    try:
        # Execute Marina CLI analysis command
        session_dir = SessionManager.get_session_dir()
        result = MarinaCliExecutor.execute_command(['analysis'], session_dir)
        
        if result['success']:
            # Try to parse the output as JSON if possible
            try:
                analysis_data = json.loads(result['stdout'])
                return jsonify({
                    'success': True,
                    'data': analysis_data,
                    'timestamp': datetime.now().isoformat()
                })
            except json.JSONDecodeError:
                # If not JSON, return as text
                return jsonify({
                    'success': True,
                    'data': {
                        'raw_output': result['stdout'],
                        'type': 'text'
                    },
                    'timestamp': datetime.now().isoformat()
                })
        else:
            return jsonify({
                'success': False,
                'error': result['stderr'] or 'Analysis command failed',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/sensory/status')
@session_required
def api_sensory_status():
    """Get status of all sensory engines"""
    try:
        # Import sensory checking functions
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        
        from perception import sensory
        
        # Helper function to safely call sensory checks
        def safe_sensory_check(check_func, engine_name):
            try:
                return check_func()
            except Exception as e:
                return {
                    'available': False,
                    'active': False,
                    'error': str(e),
                    'engine': engine_name
                }
        
        # Get status for all sensory engines with error handling
        status = {
            'audio': safe_sensory_check(sensory.check_microphone, 'audio'),
            'visual': {
                'camera': safe_sensory_check(sensory.check_camera, 'camera'),
                'screen': safe_sensory_check(sensory.check_screen, 'screen')
            },
            'thermal': safe_sensory_check(sensory.check_thermal_perception, 'thermal'),
            'kinetic': safe_sensory_check(sensory.check_kinetic_perception, 'kinetic'),
            'touch': safe_sensory_check(sensory.check_touch_perception, 'touch'),
            'time': safe_sensory_check(sensory.check_time_perception, 'time'),
            'taste': safe_sensory_check(sensory.check_taste_perception, 'taste'),
            'smell': safe_sensory_check(sensory.check_smell_perception, 'smell'),
            'proprioception': safe_sensory_check(sensory.check_proprioception, 'proprioception')
        }
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500

def cleanup_old_sessions():
    """Background task to clean up old sessions"""
    while True:
        try:
            current_time = datetime.now()
            for session_dir in UPLOAD_FOLDER.iterdir():
                if session_dir.is_dir():
                    # Check if session is older than 24 hours
                    created_time = datetime.fromtimestamp(session_dir.stat().st_ctime)
                    if current_time - created_time > timedelta(hours=24):
                        shutil.rmtree(session_dir)
                        print(f"Cleaned up old session: {session_dir.name}")
        except Exception as e:
            print(f"Error in session cleanup: {e}")
        
        # Sleep for 1 hour
        time.sleep(3600)

if __name__ == '__main__':
    # Start background session cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
    cleanup_thread.start()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
