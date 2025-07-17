#!/usr/bin/env python3
"""
Marina LLM API Server
Simple HTTP server to handle LLM requests from the browser extension
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Add Marina project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Marina LLM router
from llm.llm_router import route_task, query_llm_response

class MarinaLLMHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Marina LLM API"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Parse URL
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/api/llm/query':
                self.handle_llm_query()
            elif parsed_path.path == '/api/audio/analyze':
                self.handle_audio_analysis()
            else:
                self.send_error(404, "Endpoint not found")
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/api/status':
                self.handle_status()
            elif parsed_path.path == '/api/models':
                self.handle_models()
            else:
                self.send_error(404, "Endpoint not found")
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_llm_query(self):
        """Handle LLM query requests"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "Empty request body")
                return
            
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Extract parameters
            prompt = data.get('prompt', '')
            model = data.get('model', 'auto')
            temperature = data.get('temperature', 0.7)
            
            if not prompt:
                self.send_error(400, "Missing 'prompt' parameter")
                return
            
            print(f"[Marina LLM API] Processing query: {prompt[:100]}...")
            
            # Route to appropriate LLM
            if model == 'auto':
                # Use automatic routing based on token estimation
                token_estimate = len(prompt.split()) * 1.3
                selected_model, result = route_task(prompt, token_estimate, run=True)
            else:
                # Use specific model
                result = query_llm_response(model, prompt)
                selected_model = model
            
            # Prepare response
            response_data = {
                'success': True,
                'response': result,
                'model_used': selected_model,
                'timestamp': time.time()
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(response_data, indent=2)
            self.wfile.write(response_json.encode('utf-8'))
            
            print(f"[Marina LLM API] Query processed successfully using {selected_model}")
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON in request body")
        except Exception as e:
            print(f"[Marina LLM API] Error processing query: {str(e)}")
            self.send_error(500, f"Error processing query: {str(e)}")
    
    def handle_status(self):
        """Handle status requests"""
        try:
            status_data = {
                'status': 'running',
                'service': 'Marina LLM API',
                'version': '1.0.0',
                'timestamp': time.time()
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(status_data, indent=2)
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error getting status: {str(e)}")
    
    def handle_models(self):
        """Handle available models request"""
        try:
            # Get available models from router
            from llm.llm_router import get_local_ollama_models
            
            ollama_models = get_local_ollama_models()
            
            models_data = {
                'available_models': {
                    'local': ollama_models,
                    'remote': ['gpt', 'gemini', 'deepseek'],
                    'auto': ['auto']
                },
                'default_model': 'auto',
                'timestamp': time.time()
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(models_data, indent=2)
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error getting models: {str(e)}")
    
    def handle_audio_analysis(self):
        """Handle audio analysis requests"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "Empty request body")
                return
            
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Extract parameters
            audio_data = data.get('audioData', '')
            analysis_type = data.get('analysisType', 'both')
            duration = data.get('duration', 10)
            
            if not audio_data:
                self.send_error(400, "Missing 'audioData' parameter")
                return
            
            print(f"[Marina LLM API] Processing audio analysis: {analysis_type} for {duration}s")
            
            # Process audio analysis
            result = self.process_audio_analysis(audio_data, analysis_type, duration)
            
            # Prepare response
            response_data = {
                'success': True,
                'results': result,
                'analysis_type': analysis_type,
                'duration': duration,
                'timestamp': time.time()
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(response_data, indent=2)
            self.wfile.write(response_json.encode('utf-8'))
            
            print(f"[Marina LLM API] Audio analysis processed successfully")
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON in request body")
        except Exception as e:
            print(f"[Marina LLM API] Error processing audio analysis: {str(e)}")
            self.send_error(500, f"Error processing audio analysis: {str(e)}")
    
    def process_audio_analysis(self, audio_data, analysis_type, duration):
        """Process audio analysis using Marina's real audio analysis modules"""
        import base64
        import tempfile
        import asyncio
        from perception.sonic.song_recognition import SongRecognitionManager
        from perception.sonic.soundscape_detector import SoundscapeDetector
        
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_filename = temp_file.name
            
            result = {}
            
            # Perform song recognition if requested
            if analysis_type in ['song', 'both']:
                try:
                    # Initialize song recognition manager
                    song_manager = SongRecognitionManager()
                    
                    # Run song recognition
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    song_name, artist_name = loop.run_until_complete(
                        song_manager.recognize_audio(temp_filename)
                    )
                    
                    if song_name and artist_name:
                        result['song'] = {
                            'title': song_name,
                            'artist': artist_name,
                            'confidence': 85,  # Shazam typically has high confidence
                            'duration': duration,
                            'source': 'Shazam'
                        }
                    
                    loop.close()
                    
                except Exception as e:
                    print(f"Song recognition error: {e}")
                    # Fall back to None if recognition fails
                    pass
            
            # Perform soundscape analysis if requested
            if analysis_type in ['soundscape', 'both']:
                try:
                    # Initialize soundscape detector
                    soundscape_detector = SoundscapeDetector()
                    
                    # Run soundscape analysis
                    soundscape_result = soundscape_detector.analyze_audio_file(temp_filename)
                    
                    if soundscape_result:
                        result['soundscape'] = {
                            'environment': soundscape_result.environment_type,
                            'confidence': int(soundscape_result.confidence * 100),
                            'noiseLevel': soundscape_result.noise_level,
                            'quality': soundscape_result.audio_quality,
                            'description': soundscape_result.description,
                            'soundEvents': soundscape_result.sound_events,
                            'acousticFeatures': {
                                'spectralCentroid': soundscape_result.acoustic_features.spectral_centroid,
                                'rmsEnergy': soundscape_result.acoustic_features.rms_energy,
                                'tempo': soundscape_result.acoustic_features.tempo
                            }
                        }
                    
                except Exception as e:
                    print(f"Soundscape analysis error: {e}")
                    # Fall back to None if analysis fails
                    pass
            
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            return result
            
        except Exception as e:
            print(f"Error in audio analysis processing: {e}")
            return {}
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[Marina LLM API] {format % args}")

def run_server(host='localhost', port=8000):
    """Run the Marina LLM API server"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, MarinaLLMHandler)
    
    print(f"[Marina LLM API] Starting server on http://{host}:{port}")
    print(f"[Marina LLM API] Available endpoints:")
    print(f"  POST /api/llm/query - Process LLM queries")
    print(f"  GET  /api/status    - Server status")
    print(f"  GET  /api/models    - Available models")
    print(f"[Marina LLM API] Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[Marina LLM API] Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Marina LLM API Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    
    args = parser.parse_args()
    
    # Run server
    run_server(args.host, args.port)
