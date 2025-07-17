#!/usr/bin/env python3
"""
Curiosity Interface for Marina
Provides easy integration between the curiosity engine and Marina's existing systems
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import threading
import asyncio

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curiosity_engine import CuriosityEngine, KnownUnknown, CuriosityLevel
from llm.llm_router import LLMRouter


class CuriosityInterface:
    """Interface for integrating curiosity engine with Marina's systems"""
    
    def __init__(self, db_path: str = "curiosity.db"):
        self.engine = CuriosityEngine(db_path)
        self.llm_router = LLMRouter()
        
        # Callback functions for various events
        self.callbacks = {
            'unknown_discovered': [],
            'exploration_started': [],
            'exploration_completed': [],
            'insight_generated': []
        }
        
        # Auto-analysis settings
        self.auto_analyze_queries = True
        self.auto_analyze_conversations = True
        self.auto_analyze_documents = True
        
        # Start monitoring thread
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start monitoring thread for curiosity events"""
        def monitor():
            while True:
                try:
                    # Check for completed explorations
                    self._check_completed_explorations()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    print(f"Error in curiosity monitoring: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def _check_completed_explorations(self):
        """Check for newly completed explorations and trigger callbacks"""
        active_explorations = self.engine.get_active_explorations()
        
        for exploration in active_explorations:
            if exploration['status'] == 'completed':
                # Trigger completion callbacks
                for callback in self.callbacks['exploration_completed']:
                    try:
                        callback(exploration)
                    except Exception as e:
                        print(f"Error in exploration completion callback: {e}")
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register a callback for curiosity events"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def analyze_user_query(self, query: str, response: str = "") -> Optional[str]:
        """Analyze a user query for unknown unknowns"""
        if not self.auto_analyze_queries:
            return None
        
        try:
            # Identify unknown from query-response pair
            unknown = self.engine.identify_unknown_from_query(query, response)
            
            if unknown:
                # Add to engine
                self.engine.add_unknown(unknown)
                
                # Trigger callbacks
                for callback in self.callbacks['unknown_discovered']:
                    try:
                        callback(unknown)
                    except Exception as e:
                        print(f"Error in unknown discovery callback: {e}")
                
                return unknown.id
                
        except Exception as e:
            print(f"Error analyzing user query: {e}")
            
        return None
    
    def analyze_conversation(self, conversation_text: str, context: str = "") -> List[str]:
        """Analyze a conversation for multiple unknowns"""
        if not self.auto_analyze_conversations:
            return []
        
        unknown_ids = []
        
        try:
            # Split conversation into chunks for analysis
            chunks = self._split_conversation(conversation_text)
            
            for chunk in chunks:
                unknown = self.engine.identify_unknown_from_text(chunk, context)
                
                if unknown:
                    self.engine.add_unknown(unknown)
                    unknown_ids.append(unknown.id)
                    
                    # Trigger callbacks
                    for callback in self.callbacks['unknown_discovered']:
                        try:
                            callback(unknown)
                        except Exception as e:
                            print(f"Error in unknown discovery callback: {e}")
                            
        except Exception as e:
            print(f"Error analyzing conversation: {e}")
            
        return unknown_ids
    
    def _split_conversation(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        """Split conversation into manageable chunks"""
        chunks = []
        sentences = text.split('.')
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk + sentence) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence + "."
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def analyze_document(self, document_text: str, document_type: str = "unknown", 
                        title: str = "") -> List[str]:
        """Analyze a document for unknowns"""
        if not self.auto_analyze_documents:
            return []
        
        unknown_ids = []
        
        try:
            # Enhanced analysis for documents
            analysis_prompt = f"""
            Analyze this {document_type} document for knowledge gaps, uncertainties, and areas requiring further investigation.
            
            Title: {title}
            Document Type: {document_type}
            
            Content: {document_text[:3000]}...
            
            Look for:
            1. Explicit mentions of uncertainty or unknowns
            2. Questions posed but not answered
            3. Areas marked for future research
            4. Incomplete information or data gaps
            5. Contradictory information that needs resolution
            6. Technical terms or concepts that need clarification
            
            For each unknown found, provide:
            - Category (technical, research, operational, etc.)
            - Brief title
            - Description
            - Estimated complexity (low/medium/high)
            - Potential impact (low/medium/high)
            
            Format as JSON array of objects with the above fields.
            """
            
            response = self.llm_router.route_request(analysis_prompt)
            
            try:
                unknowns_data = json.loads(response)
                
                for unknown_data in unknowns_data:
                    unknown = KnownUnknown(
                        id=self.engine._generate_id(),
                        category=unknown_data.get('category', 'general'),
                        title=unknown_data.get('title', 'Unknown'),
                        description=unknown_data.get('description', ''),
                        context=f"Document: {title} ({document_type})",
                        curiosity_level=self._map_complexity_to_curiosity(
                            unknown_data.get('complexity', 'medium')
                        ),
                        discovery_method='document_analysis',
                        timestamp=datetime.now(),
                        related_topics=unknown_data.get('related_topics', []),
                        confidence_score=0.7,
                        complexity_score=self._map_complexity_score(
                            unknown_data.get('complexity', 'medium')
                        ),
                        potential_impact=self._map_impact_score(
                            unknown_data.get('potential_impact', 'medium')
                        )
                    )
                    
                    self.engine.add_unknown(unknown)
                    unknown_ids.append(unknown.id)
                    
                    # Trigger callbacks
                    for callback in self.callbacks['unknown_discovered']:
                        try:
                            callback(unknown)
                        except Exception as e:
                            print(f"Error in unknown discovery callback: {e}")
                            
            except json.JSONDecodeError:
                print("Failed to parse document analysis response")
                
        except Exception as e:
            print(f"Error analyzing document: {e}")
            
        return unknown_ids
    
    def _map_complexity_to_curiosity(self, complexity: str) -> CuriosityLevel:
        """Map complexity level to curiosity level"""
        mapping = {
            'low': CuriosityLevel.MEDIUM,
            'medium': CuriosityLevel.HIGH,
            'high': CuriosityLevel.URGENT
        }
        return mapping.get(complexity.lower(), CuriosityLevel.MEDIUM)
    
    def _map_complexity_score(self, complexity: str) -> float:
        """Map complexity string to numeric score"""
        mapping = {
            'low': 0.3,
            'medium': 0.5,
            'high': 0.8
        }
        return mapping.get(complexity.lower(), 0.5)
    
    def _map_impact_score(self, impact: str) -> float:
        """Map impact string to numeric score"""
        mapping = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.9
        }
        return mapping.get(impact.lower(), 0.6)
    
    def manual_unknown_entry(self, title: str, description: str, 
                           category: str = "general", 
                           curiosity_level: str = "medium",
                           related_topics: List[str] = None) -> str:
        """Manually add a known unknown"""
        if related_topics is None:
            related_topics = []
        
        unknown = KnownUnknown(
            id=self.engine._generate_id(),
            category=category,
            title=title,
            description=description,
            context="Manual entry",
            curiosity_level=CuriosityLevel(curiosity_level),
            discovery_method="manual_input",
            timestamp=datetime.now(),
            related_topics=related_topics,
            confidence_score=0.8,
            complexity_score=0.5,
            potential_impact=0.7
        )
        
        self.engine.add_unknown(unknown)
        
        # Trigger callbacks
        for callback in self.callbacks['unknown_discovered']:
            try:
                callback(unknown)
            except Exception as e:
                print(f"Error in unknown discovery callback: {e}")
        
        return unknown.id
    
    def get_curiosity_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive curiosity dashboard data"""
        report = self.engine.generate_curiosity_report()
        
        # Add additional insights
        recent_unknowns = self.engine.get_recent_unknowns(10)
        active_explorations = self.engine.get_active_explorations()
        
        # Calculate trends
        trends = self._calculate_trends(recent_unknowns)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(report, trends)
        
        dashboard = {
            'summary': {
                'total_unknowns': report.get('total_unknowns', 0),
                'active_explorations': report.get('active_explorations', 0),
                'completion_rate': self._calculate_completion_rate(active_explorations),
                'average_curiosity_level': self._calculate_avg_curiosity_level(recent_unknowns)
            },
            'categories': report.get('by_category', {}),
            'curiosity_levels': report.get('by_curiosity_level', {}),
            'trends': trends,
            'recent_unknowns': [
                {
                    'id': unknown.id,
                    'title': unknown.title,
                    'category': unknown.category,
                    'curiosity_level': unknown.curiosity_level.value,
                    'timestamp': unknown.timestamp.isoformat()
                }
                for unknown in recent_unknowns
            ],
            'active_explorations': active_explorations,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }
        
        return dashboard
    
    def _calculate_trends(self, unknowns: List[KnownUnknown]) -> Dict[str, Any]:
        """Calculate trends from recent unknowns"""
        if not unknowns:
            return {}
        
        # Group by day
        daily_counts = {}
        category_trends = {}
        
        for unknown in unknowns:
            day = unknown.timestamp.date().isoformat()
            
            # Daily counts
            if day not in daily_counts:
                daily_counts[day] = 0
            daily_counts[day] += 1
            
            # Category trends
            if unknown.category not in category_trends:
                category_trends[unknown.category] = 0
            category_trends[unknown.category] += 1
        
        # Sort by date
        sorted_days = sorted(daily_counts.items())
        
        return {
            'daily_discovery_rate': sorted_days,
            'trending_categories': sorted(
                category_trends.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5],
            'discovery_velocity': len(unknowns) / max(len(set(u.timestamp.date() for u in unknowns)), 1)
        }
    
    def _calculate_completion_rate(self, explorations: List[Dict]) -> float:
        """Calculate completion rate of explorations"""
        if not explorations:
            return 0.0
        
        completed = sum(1 for e in explorations if e['status'] == 'completed')
        return completed / len(explorations) if explorations else 0.0
    
    def _calculate_avg_curiosity_level(self, unknowns: List[KnownUnknown]) -> float:
        """Calculate average curiosity level"""
        if not unknowns:
            return 0.0
        
        level_scores = {
            CuriosityLevel.LOW: 1,
            CuriosityLevel.MEDIUM: 2,
            CuriosityLevel.HIGH: 3,
            CuriosityLevel.URGENT: 4
        }
        
        total_score = sum(level_scores.get(u.curiosity_level, 2) for u in unknowns)
        return total_score / len(unknowns)
    
    def _generate_recommendations(self, report: Dict, trends: Dict) -> List[str]:
        """Generate recommendations based on curiosity analysis"""
        recommendations = []
        
        # High-level recommendations
        if report.get('active_explorations', 0) == 0:
            recommendations.append("Consider exploring some of your known unknowns to gain new insights")
        
        if report.get('total_unknowns', 0) > 20:
            recommendations.append("You have many unknowns - consider prioritizing high-impact ones")
        
        # Category-based recommendations
        categories = report.get('by_category', {})
        if categories:
            top_category = max(categories, key=categories.get)
            recommendations.append(f"Focus on {top_category} category as it has the most unknowns")
        
        # Trend-based recommendations
        if trends.get('discovery_velocity', 0) > 5:
            recommendations.append("High discovery rate - consider increasing exploration capacity")
        
        return recommendations
    
    def search_unknowns(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search through known unknowns"""
        unknowns = self.engine.get_recent_unknowns(100)  # Get more for searching
        
        results = []
        query_lower = query.lower()
        
        for unknown in unknowns:
            # Simple text matching
            if (query_lower in unknown.title.lower() or 
                query_lower in unknown.description.lower() or
                query_lower in unknown.category.lower() or
                any(query_lower in topic.lower() for topic in unknown.related_topics)):
                
                results.append({
                    'id': unknown.id,
                    'title': unknown.title,
                    'description': unknown.description,
                    'category': unknown.category,
                    'curiosity_level': unknown.curiosity_level.value,
                    'confidence_score': unknown.confidence_score,
                    'potential_impact': unknown.potential_impact,
                    'timestamp': unknown.timestamp.isoformat()
                })
        
        # Sort by relevance (simple scoring)
        results.sort(key=lambda x: x['potential_impact'] * x['confidence_score'], reverse=True)
        
        return results[:limit]
    
    def start_exploration(self, unknown_id: str) -> Optional[str]:
        """Start exploration of a specific unknown"""
        return self.engine.start_exploration(unknown_id)
    
    def get_exploration_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get results of an exploration task"""
        return self.engine.get_exploration_status(task_id)
    
    def set_auto_analysis(self, queries: bool = True, conversations: bool = True, documents: bool = True):
        """Configure automatic analysis settings"""
        self.auto_analyze_queries = queries
        self.auto_analyze_conversations = conversations
        self.auto_analyze_documents = documents
    
    def generate_exploration_suggestion(self) -> Optional[Dict[str, Any]]:
        """Generate a suggestion for what to explore next"""
        unknowns = self.engine.get_recent_unknowns(20)
        
        if not unknowns:
            return None
        
        # Score unknowns for exploration priority
        scored_unknowns = []
        for unknown in unknowns:
            score = (
                unknown.confidence_score * 0.3 +
                unknown.potential_impact * 0.4 +
                (1 - unknown.complexity_score) * 0.2 +
                (1 if unknown.curiosity_level == CuriosityLevel.HIGH else 0.5) * 0.1
            )
            scored_unknowns.append((unknown, score))
        
        # Sort by score
        scored_unknowns.sort(key=lambda x: x[1], reverse=True)
        
        if scored_unknowns:
            best_unknown, score = scored_unknowns[0]
            return {
                'unknown_id': best_unknown.id,
                'title': best_unknown.title,
                'description': best_unknown.description,
                'category': best_unknown.category,
                'curiosity_level': best_unknown.curiosity_level.value,
                'priority_score': score,
                'reasoning': f"High priority due to {best_unknown.curiosity_level.value} curiosity level and {best_unknown.potential_impact:.1f} impact score"
            }
        
        return None


# Example callback functions
def on_unknown_discovered(unknown: KnownUnknown):
    """Example callback for when an unknown is discovered"""
    print(f"🔍 New unknown discovered: {unknown.title} (Category: {unknown.category})")

def on_exploration_completed(exploration: Dict[str, Any]):
    """Example callback for when an exploration is completed"""
    print(f"✅ Exploration completed: {exploration['task_id']} (Score: {exploration['completion_score']:.2f})")

def on_insight_generated(insight: Dict[str, Any]):
    """Example callback for when an insight is generated"""
    print(f"💡 New insight: {insight.get('summary', 'No summary available')}")


# Example usage
if __name__ == "__main__":
    # Initialize curiosity interface
    curiosity = CuriosityInterface()
    
    # Register callbacks
    curiosity.register_callback('unknown_discovered', on_unknown_discovered)
    curiosity.register_callback('exploration_completed', on_exploration_completed)
    curiosity.register_callback('insight_generated', on_insight_generated)
    
    # Example usage
    print("🧠 Curiosity Interface initialized")
    
    # Simulate analyzing a user query
    query = "How do neural networks actually learn? I'm not sure I understand the backpropagation process."
    response = "Neural networks learn through backpropagation, but the exact mechanism is complex and involves gradient descent."
    
    unknown_id = curiosity.analyze_user_query(query, response)
    if unknown_id:
        print(f"📝 Identified unknown from query: {unknown_id}")
    
    # Add a manual unknown
    manual_id = curiosity.manual_unknown_entry(
        title="Understanding Marina's decision-making process",
        description="How does Marina prioritize tasks and make decisions?",
        category="ai_behavior",
        curiosity_level="high",
        related_topics=["decision_making", "task_prioritization", "ai_behavior"]
    )
    print(f"📝 Manually added unknown: {manual_id}")
    
    # Get dashboard
    dashboard = curiosity.get_curiosity_dashboard()
    print(f"📊 Dashboard: {dashboard['summary']['total_unknowns']} unknowns, {dashboard['summary']['active_explorations']} active explorations")
    
    # Generate exploration suggestion
    suggestion = curiosity.generate_exploration_suggestion()
    if suggestion:
        print(f"💭 Exploration suggestion: {suggestion['title']} (Priority: {suggestion['priority_score']:.2f})")
    
    print("🔄 Curiosity interface is running...")
    
    # Keep running to demonstrate background processing
    try:
        while True:
            time.sleep(30)
            dashboard = curiosity.get_curiosity_dashboard()
            print(f"📊 Status: {dashboard['summary']['total_unknowns']} unknowns, {dashboard['summary']['active_explorations']} active explorations")
    except KeyboardInterrupt:
        print("🛑 Stopping curiosity interface...")
