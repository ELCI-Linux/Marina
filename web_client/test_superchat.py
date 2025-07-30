#!/usr/bin/env python3
"""
Test script for SuperChat routing functionality
"""

import sys
import os
import json

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from llm import llm_router

def test_superchat_routing():
    """Test the SuperChat routing with different models"""
    
    # Test prompt
    test_prompt = "Hello, this is a test message for SuperChat routing"
    
    # Model mapping (same as in app.py)
    model_mapping = {
        'GPT-4': 'gpt',
        'Gemini': 'gemini', 
        'Claude': 'claude',
        'DeepSeek': 'deepseek',
        'LLaMA3': 'llama',
        'Mistral': 'mistral'
    }
    
    print("🧪 Testing SuperChat Routing")
    print("=" * 50)
    
    # Test each model
    for ui_model, internal_model in model_mapping.items():
        print(f"\n🔍 Testing {ui_model} ({internal_model})...")
        
        try:
            # Estimate token count
            token_estimate = len(test_prompt.split()) * 1.3
            
            # Use LLM router with forced model
            selected_model, response = llm_router.route_task(
                test_prompt,
                token_estimate,
                run=True,
                force_model=internal_model
            )
            
            # Check result
            if response and not (isinstance(response, str) and response.startswith('[ERROR]')):
                print(f"✅ {ui_model}: SUCCESS")
                print(f"   Selected: {selected_model}")
                print(f"   Response: {response[:80]}...")
            else:
                print(f"❌ {ui_model}: FAILED")
                print(f"   Selected: {selected_model}")
                print(f"   Error: {response}")
                
        except Exception as e:
            print(f"❌ {ui_model}: EXCEPTION")
            print(f"   Error: {str(e)}")
    
    print(f"\n🔄 Testing Whisper Mode (single model)")
    print("-" * 30)
    
    # Test whisper mode (should only use first model)
    enabled_models = ['GPT-4', 'Gemini', 'Claude']
    internal_models = [model_mapping.get(model, model.lower()) for model in enabled_models]
    
    # Whisper mode: only first model
    whisper_models = internal_models[:1]
    
    print(f"Original models: {enabled_models}")
    print(f"Whisper mode models: {whisper_models}")
    
    for model in whisper_models:
        try:
            selected_model, response = llm_router.route_task(
                "Whisper mode test",
                50,
                run=True,
                force_model=model
            )
            print(f"✅ Whisper mode working with {model}")
            break
        except Exception as e:
            print(f"❌ Whisper mode failed with {model}: {e}")

if __name__ == "__main__":
    test_superchat_routing()
