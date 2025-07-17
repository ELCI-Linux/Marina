#!/usr/bin/env python3
"""
Test script for the Curiosity Engine
Demonstrates identification of unknowns and exploration processes
"""

import sys
import os
import time
import json
from datetime import datetime

# Add brain directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from curiosity_engine import CuriosityEngine, KnownUnknown, CuriosityLevel
from curiosity_interface import CuriosityInterface


def test_text_analysis():
    """Test unknown identification from text"""
    print("🔍 Testing Unknown Identification from Text")
    print("=" * 50)
    
    engine = CuriosityEngine()
    
    # Test texts with various types of unknowns
    test_texts = [
        {
            "text": "I'm not sure how machine learning models actually make decisions. The process seems like a black box to me.",
            "context": "Discussion about AI explainability"
        },
        {
            "text": "The quantum computer results are inconsistent. We need to investigate why the coherence time varies so much.",
            "context": "Quantum computing research"
        },
        {
            "text": "There's something unclear about the user behavior patterns. Why do engagement rates drop after 3 PM?",
            "context": "User analytics meeting"
        },
        {
            "text": "I understand the basic concept of neural networks, but I'm uncertain about how backpropagation actually works in practice.",
            "context": "Machine learning study"
        }
    ]
    
    discovered_unknowns = []
    
    for i, test_case in enumerate(test_texts, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Text: {test_case['text']}")
        print(f"Context: {test_case['context']}")
        
        unknown = engine.identify_unknown_from_text(test_case['text'], test_case['context'])
        
        if unknown:
            print(f"✅ Unknown identified: {unknown.title}")
            print(f"   Category: {unknown.category}")
            print(f"   Curiosity Level: {unknown.curiosity_level.value}")
            print(f"   Confidence: {unknown.confidence_score:.2f}")
            print(f"   Impact: {unknown.potential_impact:.2f}")
            
            engine.add_unknown(unknown)
            discovered_unknowns.append(unknown)
        else:
            print("❌ No unknown identified")
    
    return discovered_unknowns


def test_query_analysis():
    """Test unknown identification from query-response pairs"""
    print("\n🔍 Testing Unknown Identification from Query-Response Pairs")
    print("=" * 60)
    
    engine = CuriosityEngine()
    
    # Test query-response pairs
    test_pairs = [
        {
            "query": "How do transformers work in natural language processing?",
            "response": "Transformers use attention mechanisms, but the exact process of how they understand context is still being researched."
        },
        {
            "query": "What's the best way to optimize database queries?",
            "response": "It depends on your specific use case. Indexing helps, but there are many factors to consider that I'm not fully covering here."
        },
        {
            "query": "How does Marina's memory system work?",
            "response": "Marina uses various memory components, but the exact integration and decision-making process isn't fully documented."
        }
    ]
    
    discovered_unknowns = []
    
    for i, pair in enumerate(test_pairs, 1):
        print(f"\n📝 Test Pair {i}:")
        print(f"Query: {pair['query']}")
        print(f"Response: {pair['response']}")
        
        unknown = engine.identify_unknown_from_query(pair['query'], pair['response'])
        
        if unknown:
            print(f"✅ Unknown identified: {unknown.title}")
            print(f"   Category: {unknown.category}")
            print(f"   Curiosity Level: {unknown.curiosity_level.value}")
            print(f"   Related Topics: {', '.join(unknown.related_topics)}")
            
            engine.add_unknown(unknown)
            discovered_unknowns.append(unknown)
        else:
            print("❌ No unknown identified")
    
    return discovered_unknowns


def test_manual_unknown_creation():
    """Test manual creation of unknowns"""
    print("\n📝 Testing Manual Unknown Creation")
    print("=" * 40)
    
    engine = CuriosityEngine()
    
    # Create some manual unknowns
    manual_unknowns = [
        {
            "title": "Understanding Marina's decision-making hierarchy",
            "description": "How does Marina prioritize different types of tasks and decide which actions to take first?",
            "category": "ai_behavior",
            "curiosity_level": CuriosityLevel.HIGH,
            "related_topics": ["decision_making", "task_prioritization", "ai_architecture"]
        },
        {
            "title": "Optimal prompt engineering strategies",
            "description": "What are the most effective ways to structure prompts for different types of LLM tasks?",
            "category": "llm_optimization",
            "curiosity_level": CuriosityLevel.MEDIUM,
            "related_topics": ["prompt_engineering", "llm_performance", "natural_language"]
        },
        {
            "title": "Memory consolidation in AI systems",
            "description": "How should AI systems decide what information to retain long-term versus what to discard?",
            "category": "memory_management",
            "curiosity_level": CuriosityLevel.HIGH,
            "related_topics": ["memory_systems", "information_retention", "ai_cognition"]
        }
    ]
    
    created_unknowns = []
    
    for i, unknown_data in enumerate(manual_unknowns, 1):
        print(f"\n📝 Creating Unknown {i}: {unknown_data['title']}")
        
        unknown = KnownUnknown(
            id=engine._generate_id(),
            category=unknown_data['category'],
            title=unknown_data['title'],
            description=unknown_data['description'],
            context="Manual test creation",
            curiosity_level=unknown_data['curiosity_level'],
            discovery_method="manual_test",
            timestamp=datetime.now(),
            related_topics=unknown_data['related_topics'],
            confidence_score=0.8,
            complexity_score=0.6,
            potential_impact=0.7
        )
        
        success = engine.add_unknown(unknown)
        
        if success:
            print(f"✅ Successfully created: {unknown.title}")
            print(f"   ID: {unknown.id}")
            print(f"   Category: {unknown.category}")
            print(f"   Curiosity Level: {unknown.curiosity_level.value}")
            created_unknowns.append(unknown)
        else:
            print(f"❌ Failed to create unknown")
    
    return created_unknowns


def test_exploration_process():
    """Test the exploration process"""
    print("\n🚀 Testing Exploration Process")
    print("=" * 35)
    
    engine = CuriosityEngine()
    
    # Create a test unknown for exploration
    test_unknown = KnownUnknown(
        id=engine._generate_id(),
        category="technology",
        title="How does edge computing improve performance?",
        description="Understanding the specific mechanisms by which edge computing reduces latency and improves application performance",
        context="Technology research",
        curiosity_level=CuriosityLevel.HIGH,
        discovery_method="test_creation",
        timestamp=datetime.now(),
        related_topics=["edge_computing", "performance_optimization", "distributed_systems"],
        confidence_score=0.9,
        complexity_score=0.6,
        potential_impact=0.8
    )
    
    print(f"📝 Created test unknown: {test_unknown.title}")
    
    # Add to engine
    engine.add_unknown(test_unknown)
    
    # Start exploration
    print(f"🔍 Starting exploration for: {test_unknown.title}")
    task_id = engine.start_exploration(test_unknown.id)
    
    if task_id:
        print(f"✅ Exploration started with task ID: {task_id}")
        
        # Monitor exploration progress
        print("📊 Monitoring exploration progress...")
        
        for i in range(12):  # Check for 2 minutes
            time.sleep(10)
            
            status = engine.get_exploration_status(task_id)
            if status:
                print(f"   Status: {status['status']} - Completion: {status['completion_score']:.2f}")
                print(f"   Findings: {status['findings_count']} - Questions: {status['follow_up_questions_count']}")
                
                if status['status'] == 'completed':
                    print("✅ Exploration completed!")
                    break
                elif status['status'] == 'failed':
                    print("❌ Exploration failed!")
                    break
            else:
                print("⚠️ Could not get exploration status")
                break
    else:
        print("❌ Failed to start exploration")
    
    return task_id


def test_curiosity_interface():
    """Test the curiosity interface"""
    print("\n🧠 Testing Curiosity Interface")
    print("=" * 35)
    
    interface = CuriosityInterface()
    
    # Test callback registration
    def on_unknown_discovered(unknown):
        print(f"🔔 Callback: Unknown discovered - {unknown.title}")
    
    interface.register_callback('unknown_discovered', on_unknown_discovered)
    
    # Test query analysis
    print("\n📝 Testing query analysis...")
    query = "I'm confused about how Marina handles context in conversations"
    response = "Marina uses context windows and memory systems, but the exact mechanism is complex"
    
    unknown_id = interface.analyze_user_query(query, response)
    if unknown_id:
        print(f"✅ Query analysis created unknown: {unknown_id}")
    
    # Test manual entry
    print("\n📝 Testing manual entry...")
    manual_id = interface.manual_unknown_entry(
        title="Understanding token limits in LLMs",
        description="How do different LLMs handle token limits and what are the implications?",
        category="llm_architecture",
        curiosity_level="high",
        related_topics=["token_limits", "llm_architecture", "context_windows"]
    )
    print(f"✅ Manual entry created unknown: {manual_id}")
    
    # Test dashboard
    print("\n📊 Testing dashboard...")
    dashboard = interface.get_curiosity_dashboard()
    print(f"Dashboard Summary:")
    print(f"  Total unknowns: {dashboard['summary']['total_unknowns']}")
    print(f"  Active explorations: {dashboard['summary']['active_explorations']}")
    print(f"  Completion rate: {dashboard['summary']['completion_rate']:.2f}")
    
    # Test search
    print("\n🔍 Testing search...")
    results = interface.search_unknowns("neural network")
    print(f"Search results for 'neural network': {len(results)} found")
    
    for result in results[:3]:
        print(f"  - {result['title']} (Impact: {result['potential_impact']:.2f})")
    
    # Test exploration suggestion
    print("\n💭 Testing exploration suggestion...")
    suggestion = interface.generate_exploration_suggestion()
    if suggestion:
        print(f"Exploration suggestion: {suggestion['title']}")
        print(f"  Priority Score: {suggestion['priority_score']:.2f}")
        print(f"  Reasoning: {suggestion['reasoning']}")
    else:
        print("No exploration suggestions available")


def test_report_generation():
    """Test report generation"""
    print("\n📊 Testing Report Generation")
    print("=" * 35)
    
    engine = CuriosityEngine()
    
    # Generate comprehensive report
    report = engine.generate_curiosity_report()
    
    print("📈 Curiosity Report:")
    print(f"  Total unknowns: {report['total_unknowns']}")
    print(f"  Active explorations: {report['active_explorations']}")
    
    print("\n📂 Categories:")
    for category, count in report['by_category'].items():
        print(f"  - {category}: {count}")
    
    print("\n🎯 Curiosity Levels:")
    for level, count in report['by_curiosity_level'].items():
        print(f"  - {level}: {count}")
    
    print("\n🕐 Recent unknowns:")
    for unknown in report['recent_unknowns'][:5]:
        print(f"  - {unknown['title']} ({unknown['category']})")
    
    return report


def main():
    """Main test function"""
    print("🚀 Marina Curiosity Engine Test Suite")
    print("=" * 50)
    
    try:
        # Test 1: Text analysis
        text_unknowns = test_text_analysis()
        
        # Test 2: Query analysis
        query_unknowns = test_query_analysis()
        
        # Test 3: Manual creation
        manual_unknowns = test_manual_unknown_creation()
        
        # Test 4: Exploration process
        exploration_task = test_exploration_process()
        
        # Test 5: Interface testing
        test_curiosity_interface()
        
        # Test 6: Report generation
        report = test_report_generation()
        
        print("\n🎉 All tests completed successfully!")
        print(f"📊 Summary:")
        print(f"  Text unknowns discovered: {len(text_unknowns)}")
        print(f"  Query unknowns discovered: {len(query_unknowns)}")
        print(f"  Manual unknowns created: {len(manual_unknowns)}")
        print(f"  Exploration task: {'✅' if exploration_task else '❌'}")
        print(f"  Total unknowns in system: {report['total_unknowns']}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
