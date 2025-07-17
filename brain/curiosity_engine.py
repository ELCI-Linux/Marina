#!/usr/bin/env python3
"""
Curiosity Engine for Marina
Identifies known unknowns and launches exploratory processes using LLM-generated prompts
"""

import json
import os
import sys
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm import llm_router


class CuriosityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ExplorationStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class KnownUnknown:
    """Represents a known unknown - something we know we don't know"""
    id: str
    category: str
    title: str
    description: str
    context: str
    curiosity_level: CuriosityLevel
    discovery_method: str
    timestamp: datetime
    related_topics: List[str]
    confidence_score: float  # How certain we are this is worth exploring
    complexity_score: float  # How complex the exploration might be
    potential_impact: float  # How valuable the knowledge might be
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['curiosity_level'] = self.curiosity_level.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnownUnknown':
        """Create from dictionary"""
        data['curiosity_level'] = CuriosityLevel(data['curiosity_level'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ExplorationTask:
    """Represents an active exploration task"""
    id: str
    unknown_id: str
    prompts: List[str]
    status: ExplorationStatus
    created_at: datetime
    updated_at: datetime
    llm_responses: List[Dict[str, Any]]
    findings: List[str]
    follow_up_questions: List[str]
    completion_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExplorationTask':
        """Create from dictionary"""
        data['status'] = ExplorationStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class CuriosityEngine:
    """Main curiosity engine that identifies and explores known unknowns"""
    
    def __init__(self, db_path: str = "curiosity.db"):
        self.db_path = db_path
        self.logger = self._setup_logging()
        
        # Initialize database
        self._init_database()
        
        # Active exploration tasks
        self.active_tasks: Dict[str, ExplorationTask] = {}
        
        # Configuration
        self.max_concurrent_explorations = 3
        self.exploration_timeout = 300  # 5 minutes
        self.curiosity_threshold = 0.5
        
        # Load existing tasks
        self._load_active_tasks()
        
        # Start background worker
        self._start_background_worker()
    
    def _route_llm_request(self, prompt: str) -> str:
        """Route LLM request using Marina's router"""
        try:
            # Estimate token count
            token_estimate = len(prompt.split()) * 1.3
            
            # Route the task
            model, result = llm_router.route_task(prompt, token_estimate, run=True)
            
            if result and not result.startswith('[ERROR]'):
                return result
            else:
                self.logger.error(f"LLM routing failed: {result}")
                return "ERROR: LLM routing failed"
                
        except Exception as e:
            self.logger.error(f"Error routing LLM request: {e}")
            return f"ERROR: {str(e)}"
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the curiosity engine"""
        logger = logging.getLogger('curiosity_engine')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize SQLite database for storing unknowns and explorations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create knowns_unknowns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS known_unknowns (
                id TEXT PRIMARY KEY,
                category TEXT,
                title TEXT,
                description TEXT,
                context TEXT,
                curiosity_level TEXT,
                discovery_method TEXT,
                timestamp TEXT,
                related_topics TEXT,
                confidence_score REAL,
                complexity_score REAL,
                potential_impact REAL
            )
        ''')
        
        # Create exploration_tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exploration_tasks (
                id TEXT PRIMARY KEY,
                unknown_id TEXT,
                prompts TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT,
                llm_responses TEXT,
                findings TEXT,
                follow_up_questions TEXT,
                completion_score REAL,
                FOREIGN KEY (unknown_id) REFERENCES known_unknowns (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_active_tasks(self):
        """Load active exploration tasks from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM exploration_tasks 
            WHERE status IN ('pending', 'active', 'paused')
        ''')
        
        for row in cursor.fetchall():
            task_data = {
                'id': row[0],
                'unknown_id': row[1],
                'prompts': json.loads(row[2]) if row[2] else [],
                'status': row[3],
                'created_at': row[4],
                'updated_at': row[5],
                'llm_responses': json.loads(row[6]) if row[6] else [],
                'findings': json.loads(row[7]) if row[7] else [],
                'follow_up_questions': json.loads(row[8]) if row[8] else [],
                'completion_score': row[9] or 0.0
            }
            
            task = ExplorationTask.from_dict(task_data)
            self.active_tasks[task.id] = task
        
        conn.close()
        self.logger.info(f"Loaded {len(self.active_tasks)} active exploration tasks")
    
    def _start_background_worker(self):
        """Start background worker thread for processing explorations"""
        def worker():
            while True:
                try:
                    self._process_explorations()
                    time.sleep(10)  # Check every 10 seconds
                except Exception as e:
                    self.logger.error(f"Error in background worker: {e}")
                    time.sleep(30)  # Wait longer on error
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        self.logger.info("Background exploration worker started")
    
    def identify_unknown_from_text(self, text: str, context: str = "") -> Optional[KnownUnknown]:
        """Identify potential known unknowns from text using LLM analysis"""
        prompt = f"""
        Analyze the following text and identify any "known unknowns" - things that are explicitly mentioned as unknown, uncertain, or requiring further investigation.

        Text: {text}
        Context: {context}

        Look for:
        1. Direct statements of uncertainty ("I don't know", "unclear", "uncertain")
        2. Questions that remain unanswered
        3. Gaps in information or understanding
        4. Areas that need further research or investigation
        5. Missing data or incomplete information

        If you find a known unknown, respond with JSON in this format:
        {{
            "category": "category_name",
            "title": "brief_title",
            "description": "detailed_description",
            "curiosity_level": "low|medium|high|urgent",
            "related_topics": ["topic1", "topic2"],
            "confidence_score": 0.0-1.0,
            "complexity_score": 0.0-1.0,
            "potential_impact": 0.0-1.0
        }}

        If no clear unknown is found, respond with "NO_UNKNOWN_FOUND"
        """
        
        try:
            response = self._route_llm_request(prompt)
            
            if response and "NO_UNKNOWN_FOUND" not in response:
                try:
                    data = json.loads(response)
                    
                    # Create KnownUnknown object
                    unknown = KnownUnknown(
                        id=self._generate_id(),
                        category=data.get('category', 'general'),
                        title=data.get('title', 'Unknown'),
                        description=data.get('description', ''),
                        context=context,
                        curiosity_level=CuriosityLevel(data.get('curiosity_level', 'medium')),
                        discovery_method='text_analysis',
                        timestamp=datetime.now(),
                        related_topics=data.get('related_topics', []),
                        confidence_score=data.get('confidence_score', 0.5),
                        complexity_score=data.get('complexity_score', 0.5),
                        potential_impact=data.get('potential_impact', 0.5)
                    )
                    
                    return unknown
                    
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse LLM response as JSON")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error identifying unknown from text: {e}")
            
        return None
    
    def identify_unknown_from_query(self, query: str, response: str) -> Optional[KnownUnknown]:
        """Identify unknowns from a query-response pair"""
        prompt = f"""
        Analyze this query and response pair to identify any known unknowns that emerge:

        Query: {query}
        Response: {response}

        Look for:
        1. Questions that weren't fully answered
        2. Areas where the response indicates uncertainty
        3. Follow-up questions that naturally arise
        4. Gaps in the provided information
        5. Related topics that need exploration

        If you find a known unknown, respond with JSON in this format:
        {{
            "category": "category_name",
            "title": "brief_title",
            "description": "detailed_description",
            "curiosity_level": "low|medium|high|urgent",
            "related_topics": ["topic1", "topic2"],
            "confidence_score": 0.0-1.0,
            "complexity_score": 0.0-1.0,
            "potential_impact": 0.0-1.0
        }}

        If no clear unknown is found, respond with "NO_UNKNOWN_FOUND"
        """
        
        try:
            response = self._route_llm_request(prompt)
            
            if response and "NO_UNKNOWN_FOUND" not in response:
                try:
                    data = json.loads(response)
                    
                    unknown = KnownUnknown(
                        id=self._generate_id(),
                        category=data.get('category', 'general'),
                        title=data.get('title', 'Unknown'),
                        description=data.get('description', ''),
                        context=f"Query: {query}\nResponse: {response}",
                        curiosity_level=CuriosityLevel(data.get('curiosity_level', 'medium')),
                        discovery_method='query_analysis',
                        timestamp=datetime.now(),
                        related_topics=data.get('related_topics', []),
                        confidence_score=data.get('confidence_score', 0.5),
                        complexity_score=data.get('complexity_score', 0.5),
                        potential_impact=data.get('potential_impact', 0.5)
                    )
                    
                    return unknown
                    
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse LLM response as JSON")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error identifying unknown from query: {e}")
            
        return None
    
    def add_unknown(self, unknown: KnownUnknown) -> bool:
        """Add a known unknown to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO known_unknowns 
                (id, category, title, description, context, curiosity_level, 
                 discovery_method, timestamp, related_topics, confidence_score, 
                 complexity_score, potential_impact)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                unknown.id,
                unknown.category,
                unknown.title,
                unknown.description,
                unknown.context,
                unknown.curiosity_level.value,
                unknown.discovery_method,
                unknown.timestamp.isoformat(),
                json.dumps(unknown.related_topics),
                unknown.confidence_score,
                unknown.complexity_score,
                unknown.potential_impact
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Added unknown: {unknown.title}")
            
            # Automatically start exploration if it meets threshold
            if self._should_explore(unknown):
                self.start_exploration(unknown.id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding unknown: {e}")
            return False
    
    def _should_explore(self, unknown: KnownUnknown) -> bool:
        """Determine if an unknown should be explored automatically"""
        # Calculate exploration score based on various factors
        score = (
            unknown.confidence_score * 0.3 +
            unknown.potential_impact * 0.4 +
            (1 - unknown.complexity_score) * 0.2 +  # Lower complexity = higher score
            (1 if unknown.curiosity_level == CuriosityLevel.HIGH else 0.5) * 0.1
        )
        
        return score >= self.curiosity_threshold
    
    def start_exploration(self, unknown_id: str) -> Optional[str]:
        """Start exploration of a known unknown"""
        try:
            # Check if we're at max concurrent explorations
            active_count = len([task for task in self.active_tasks.values() 
                              if task.status == ExplorationStatus.ACTIVE])
            
            if active_count >= self.max_concurrent_explorations:
                self.logger.info(f"Max concurrent explorations reached, queuing {unknown_id}")
                return None
            
            # Get the unknown from database
            unknown = self.get_unknown(unknown_id)
            if not unknown:
                self.logger.error(f"Unknown {unknown_id} not found")
                return None
            
            # Generate exploration prompts
            prompts = self._generate_exploration_prompts(unknown)
            
            # Create exploration task
            task = ExplorationTask(
                id=self._generate_id(),
                unknown_id=unknown_id,
                prompts=prompts,
                status=ExplorationStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                llm_responses=[],
                findings=[],
                follow_up_questions=[],
                completion_score=0.0
            )
            
            # Save to database
            self._save_exploration_task(task)
            
            # Add to active tasks
            self.active_tasks[task.id] = task
            
            self.logger.info(f"Started exploration task {task.id} for unknown {unknown_id}")
            
            return task.id
            
        except Exception as e:
            self.logger.error(f"Error starting exploration: {e}")
            return None
    
    def _generate_exploration_prompts(self, unknown: KnownUnknown) -> List[str]:
        """Generate LLM prompts for exploring an unknown"""
        meta_prompt = f"""
        Generate 3-5 specific, targeted prompts to explore this known unknown:

        Title: {unknown.title}
        Description: {unknown.description}
        Context: {unknown.context}
        Category: {unknown.category}
        Related Topics: {', '.join(unknown.related_topics)}

        Create prompts that will:
        1. Gather foundational information
        2. Explore different perspectives or approaches
        3. Identify practical applications or implications
        4. Uncover related questions or areas for further investigation
        5. Synthesize findings into actionable insights

        Format as JSON array: ["prompt1", "prompt2", "prompt3", ...]
        """
        
        try:
            response = self._route_llm_request(meta_prompt)
            prompts = json.loads(response)
            
            if isinstance(prompts, list):
                return prompts
            else:
                self.logger.error("Generated prompts not in expected format")
                return self._get_default_prompts(unknown)
                
        except Exception as e:
            self.logger.error(f"Error generating exploration prompts: {e}")
            return self._get_default_prompts(unknown)
    
    def _get_default_prompts(self, unknown: KnownUnknown) -> List[str]:
        """Get default exploration prompts if generation fails"""
        return [
            f"What is {unknown.title}? Provide a comprehensive explanation.",
            f"What are the key aspects and components of {unknown.title}?",
            f"How does {unknown.title} relate to {', '.join(unknown.related_topics[:3])}?",
            f"What are the practical implications or applications of understanding {unknown.title}?",
            f"What questions remain unanswered about {unknown.title}?"
        ]
    
    def _process_explorations(self):
        """Process active exploration tasks"""
        for task_id, task in list(self.active_tasks.items()):
            try:
                if task.status == ExplorationStatus.PENDING:
                    # Start the exploration
                    task.status = ExplorationStatus.ACTIVE
                    task.updated_at = datetime.now()
                    self._save_exploration_task(task)
                    
                elif task.status == ExplorationStatus.ACTIVE:
                    # Process the next prompt
                    if len(task.llm_responses) < len(task.prompts):
                        self._process_next_prompt(task)
                    else:
                        # All prompts processed, analyze findings
                        self._analyze_exploration_results(task)
                        
            except Exception as e:
                self.logger.error(f"Error processing exploration {task_id}: {e}")
                task.status = ExplorationStatus.FAILED
                task.updated_at = datetime.now()
                self._save_exploration_task(task)
    
    def _process_next_prompt(self, task: ExplorationTask):
        """Process the next prompt in an exploration task"""
        try:
            prompt_index = len(task.llm_responses)
            prompt = task.prompts[prompt_index]
            
            self.logger.info(f"Processing prompt {prompt_index + 1}/{len(task.prompts)} for task {task.id}")
            
            # Send prompt to LLM
            response = self._route_llm_request(prompt)
            
            # Store response
            task.llm_responses.append({
                'prompt': prompt,
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Extract findings from response
            findings = self._extract_findings(response)
            task.findings.extend(findings)
            
            # Extract follow-up questions
            follow_ups = self._extract_follow_up_questions(response)
            task.follow_up_questions.extend(follow_ups)
            
            # Update completion score
            task.completion_score = len(task.llm_responses) / len(task.prompts)
            task.updated_at = datetime.now()
            
            self._save_exploration_task(task)
            
        except Exception as e:
            self.logger.error(f"Error processing prompt for task {task.id}: {e}")
            task.status = ExplorationStatus.FAILED
            task.updated_at = datetime.now()
            self._save_exploration_task(task)
    
    def _extract_findings(self, response: str) -> List[str]:
        """Extract key findings from LLM response"""
        # Simple extraction - in practice, you might want more sophisticated parsing
        findings = []
        
        # Look for bullet points or numbered lists
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                findings.append(line[1:].strip())
            elif line and len(line) > 20 and ('important' in line.lower() or 'key' in line.lower()):
                findings.append(line)
        
        return findings[:5]  # Limit to top 5 findings
    
    def _extract_follow_up_questions(self, response: str) -> List[str]:
        """Extract follow-up questions from LLM response"""
        questions = []
        
        # Look for question marks
        sentences = response.split('.')
        for sentence in sentences:
            if '?' in sentence:
                question = sentence.strip()
                if len(question) > 10:
                    questions.append(question)
        
        return questions[:3]  # Limit to top 3 questions
    
    def _analyze_exploration_results(self, task: ExplorationTask):
        """Analyze exploration results and generate summary"""
        try:
            # Generate summary prompt
            summary_prompt = f"""
            Analyze the following exploration results and provide a comprehensive summary:

            Original Unknown: {self.get_unknown(task.unknown_id).title}
            
            Findings:
            {chr(10).join(task.findings)}
            
            Follow-up Questions:
            {chr(10).join(task.follow_up_questions)}
            
            Provide:
            1. A concise summary of what was learned
            2. Key insights or conclusions
            3. Recommendations for next steps
            4. Assessment of how well the unknown was addressed (0-100%)
            
            Format as JSON:
            {{
                "summary": "...",
                "insights": ["insight1", "insight2", ...],
                "recommendations": ["rec1", "rec2", ...],
                "completion_percentage": 0-100
            }}
            """
            
            response = self._route_llm_request(summary_prompt)
            analysis = json.loads(response)
            
            # Update task with analysis
            task.completion_score = analysis.get('completion_percentage', 50) / 100
            task.status = ExplorationStatus.COMPLETED
            task.updated_at = datetime.now()
            
            # Store analysis in findings
            task.findings.append(f"SUMMARY: {analysis.get('summary', '')}")
            task.findings.extend([f"INSIGHT: {insight}" for insight in analysis.get('insights', [])])
            task.findings.extend([f"RECOMMENDATION: {rec}" for rec in analysis.get('recommendations', [])])
            
            self._save_exploration_task(task)
            
            self.logger.info(f"Completed exploration task {task.id}")
            
            # Generate new unknowns from follow-up questions
            self._generate_followup_unknowns(task)
            
        except Exception as e:
            self.logger.error(f"Error analyzing exploration results: {e}")
            task.status = ExplorationStatus.FAILED
            task.updated_at = datetime.now()
            self._save_exploration_task(task)
    
    def _generate_followup_unknowns(self, task: ExplorationTask):
        """Generate new unknowns from follow-up questions"""
        try:
            original_unknown = self.get_unknown(task.unknown_id)
            
            for question in task.follow_up_questions[:3]:  # Limit to top 3
                follow_up_unknown = KnownUnknown(
                    id=self._generate_id(),
                    category=original_unknown.category,
                    title=question.strip('?'),
                    description=f"Follow-up question from exploration of '{original_unknown.title}'",
                    context=f"Generated from exploration task {task.id}",
                    curiosity_level=CuriosityLevel.MEDIUM,
                    discovery_method='exploration_followup',
                    timestamp=datetime.now(),
                    related_topics=original_unknown.related_topics,
                    confidence_score=0.6,
                    complexity_score=0.5,
                    potential_impact=0.4
                )
                
                self.add_unknown(follow_up_unknown)
                
        except Exception as e:
            self.logger.error(f"Error generating follow-up unknowns: {e}")
    
    def get_unknown(self, unknown_id: str) -> Optional[KnownUnknown]:
        """Get a known unknown by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM known_unknowns WHERE id = ?', (unknown_id,))
            row = cursor.fetchone()
            
            if row:
                unknown_data = {
                    'id': row[0],
                    'category': row[1],
                    'title': row[2],
                    'description': row[3],
                    'context': row[4],
                    'curiosity_level': row[5],
                    'discovery_method': row[6],
                    'timestamp': row[7],
                    'related_topics': json.loads(row[8]) if row[8] else [],
                    'confidence_score': row[9],
                    'complexity_score': row[10],
                    'potential_impact': row[11]
                }
                
                return KnownUnknown.from_dict(unknown_data)
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error getting unknown: {e}")
            
        return None
    
    def _save_exploration_task(self, task: ExplorationTask):
        """Save exploration task to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO exploration_tasks
                (id, unknown_id, prompts, status, created_at, updated_at, 
                 llm_responses, findings, follow_up_questions, completion_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id,
                task.unknown_id,
                json.dumps(task.prompts),
                task.status.value,
                task.created_at.isoformat(),
                task.updated_at.isoformat(),
                json.dumps(task.llm_responses),
                json.dumps(task.findings),
                json.dumps(task.follow_up_questions),
                task.completion_score
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error saving exploration task: {e}")
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())
    
    def get_exploration_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an exploration task"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                'task_id': task.id,
                'unknown_id': task.unknown_id,
                'status': task.status.value,
                'completion_score': task.completion_score,
                'findings_count': len(task.findings),
                'follow_up_questions_count': len(task.follow_up_questions),
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            }
        return None
    
    def get_active_explorations(self) -> List[Dict[str, Any]]:
        """Get all active exploration tasks"""
        return [self.get_exploration_status(task_id) for task_id in self.active_tasks.keys()]
    
    def get_recent_unknowns(self, limit: int = 10) -> List[KnownUnknown]:
        """Get recent known unknowns"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM known_unknowns 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            unknowns = []
            for row in cursor.fetchall():
                unknown_data = {
                    'id': row[0],
                    'category': row[1],
                    'title': row[2],
                    'description': row[3],
                    'context': row[4],
                    'curiosity_level': row[5],
                    'discovery_method': row[6],
                    'timestamp': row[7],
                    'related_topics': json.loads(row[8]) if row[8] else [],
                    'confidence_score': row[9],
                    'complexity_score': row[10],
                    'potential_impact': row[11]
                }
                unknowns.append(KnownUnknown.from_dict(unknown_data))
            
            conn.close()
            return unknowns
            
        except Exception as e:
            self.logger.error(f"Error getting recent unknowns: {e}")
            return []
    
    def generate_curiosity_report(self) -> Dict[str, Any]:
        """Generate a comprehensive curiosity report"""
        try:
            unknowns = self.get_recent_unknowns(50)
            active_explorations = self.get_active_explorations()
            
            # Calculate statistics
            total_unknowns = len(unknowns)
            by_category = {}
            by_curiosity_level = {}
            
            for unknown in unknowns:
                # By category
                if unknown.category not in by_category:
                    by_category[unknown.category] = 0
                by_category[unknown.category] += 1
                
                # By curiosity level
                level = unknown.curiosity_level.value
                if level not in by_curiosity_level:
                    by_curiosity_level[level] = 0
                by_curiosity_level[level] += 1
            
            return {
                'total_unknowns': total_unknowns,
                'active_explorations': len(active_explorations),
                'by_category': by_category,
                'by_curiosity_level': by_curiosity_level,
                'recent_unknowns': [unknown.to_dict() for unknown in unknowns[:10]],
                'active_exploration_details': active_explorations,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating curiosity report: {e}")
            return {'error': str(e)}


# Example usage and testing
if __name__ == "__main__":
    # Initialize curiosity engine
    engine = CuriosityEngine()
    
    # Example: Add a known unknown manually
    example_unknown = KnownUnknown(
        id=engine._generate_id(),
        category="technology",
        title="How does quantum computing affect encryption?",
        description="Understanding the implications of quantum computing on current encryption methods",
        context="Discussion about cybersecurity and future technologies",
        curiosity_level=CuriosityLevel.HIGH,
        discovery_method="manual_input",
        timestamp=datetime.now(),
        related_topics=["encryption", "quantum physics", "cybersecurity"],
        confidence_score=0.8,
        complexity_score=0.7,
        potential_impact=0.9
    )
    
    # Add the unknown
    engine.add_unknown(example_unknown)
    
    print("Curiosity Engine initialized and example unknown added.")
    print("Background exploration worker is running...")
    
    # Keep the process running to see exploration in action
    try:
        while True:
            time.sleep(10)
            report = engine.generate_curiosity_report()
            print(f"Active explorations: {report['active_explorations']}")
            print(f"Total unknowns: {report['total_unknowns']}")
    except KeyboardInterrupt:
        print("Stopping curiosity engine...")
