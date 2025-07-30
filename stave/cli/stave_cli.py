#!/usr/bin/env python3
"""
STAVE Command Line Interface
Basic CLI for testing and demonstrating STAVE functionality.
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from delta.delta_spec import Delta, DeltaLibrary, DeltaValidator
    from delta.delta_stack import DeltaStack
    from core.audio_asset import AudioAsset, AudioAssetManager
    STAVE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing STAVE modules: {e}")
    STAVE_MODULES_AVAILABLE = False

def create_test_project(name: str, output_dir: str) -> bool:
    """Create a test STAVE project with sample deltas"""
    if not STAVE_MODULES_AVAILABLE:
        print("❌ STAVE modules not available")
        return False
    
    try:
        project_dir = Path(output_dir) / name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🎵 Creating test project: {name}")
        
        # Create test stack
        stack = DeltaStack(f"{name}_main", "test_audio.wav")
        
        # Add sample deltas
        deltas = [
            DeltaLibrary.create_pitch_shift("test_audio.wav", +2.0, "00:00:10.000:00:00:15.000"),
            DeltaLibrary.create_emotional_shift("test_audio.wav", "excitement", 0.8, "00:00:15.000:00:00:25.000"),
            DeltaLibrary.create_prosody_adjustment("test_audio.wav", 1.3, ["amazing", "incredible"])
        ]
        
        for delta in deltas:
            stack.add_delta(delta)
        
        # Save project file
        project_file = project_dir / f"{name}.stave"
        project_data = {
            "project_name": name,
            "version": "0.1.0-luthier",
            "created": "2025-07-25T17:09:09Z",
            "stacks": [stack.to_dict()],
            "assets": [],
            "metadata": {
                "description": "Test STAVE project with sample deltas",
                "tags": ["test", "demo"]
            }
        }
        
        with open(project_file, 'w') as f:
            json.dump(project_data, f, indent=2)
        
        print(f"✅ Created project file: {project_file}")
        print(f"📊 Added {len(deltas)} sample deltas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test project: {e}")
        return False

def validate_delta_file(filepath: str) -> bool:
    """Validate a .cdelta file"""
    if not STAVE_MODULES_AVAILABLE:
        print("❌ STAVE modules not available")
        return False
    
    try:
        with open(filepath, 'r') as f:
            delta_data = json.load(f)
        
        # Handle single delta or array of deltas
        if isinstance(delta_data, list):
            deltas = [Delta.from_dict(d) for d in delta_data]
        else:
            deltas = [Delta.from_dict(delta_data)]
        
        print(f"🔍 Validating {len(deltas)} delta(s) from {filepath}")
        
        valid_count = 0
        for i, delta in enumerate(deltas):
            validation = DeltaValidator.validate_delta(delta)
            
            if validation["valid"]:
                valid_count += 1
                print(f"  ✅ Delta {i+1}: {delta.delta_id} - Valid")
            else:
                print(f"  ❌ Delta {i+1}: {delta.delta_id} - Invalid")
                for error in validation["errors"]:
                    print(f"     Error: {error}")
            
            if validation["warnings"]:
                for warning in validation["warnings"]:
                    print(f"     Warning: {warning}")
        
        print(f"📊 Validation complete: {valid_count}/{len(deltas)} valid")
        return valid_count == len(deltas)
        
    except Exception as e:
        print(f"❌ Error validating delta file: {e}")
        return False

def analyze_project(filepath: str) -> Dict[str, Any]:
    """Analyze a STAVE project file"""
    try:
        with open(filepath, 'r') as f:
            project_data = json.load(f)
        
        print(f"🎵 Analyzing project: {project_data.get('project_name', 'Unnamed')}")
        
        analysis = {
            "project_name": project_data.get("project_name", "Unknown"),
            "version": project_data.get("version", "Unknown"),
            "stacks": len(project_data.get("stacks", [])),
            "assets": len(project_data.get("assets", [])),
            "total_deltas": 0,
            "delta_types": {},
            "parameters": {}
        }
        
        # Analyze stacks
        for stack_data in project_data.get("stacks", []):
            deltas = stack_data.get("deltas", [])
            analysis["total_deltas"] += len(deltas)
            
            for delta_data in deltas:
                delta_type = delta_data.get("type", "unknown")
                parameter = delta_data.get("target", {}).get("parameter", "unknown")
                
                analysis["delta_types"][delta_type] = analysis["delta_types"].get(delta_type, 0) + 1
                analysis["parameters"][parameter] = analysis["parameters"].get(parameter, 0) + 1
        
        # Print analysis
        print(f"📊 Project Analysis:")
        print(f"   Name: {analysis['project_name']}")
        print(f"   Version: {analysis['version']}")
        print(f"   Stacks: {analysis['stacks']}")
        print(f"   Assets: {analysis['assets']}")
        print(f"   Total Deltas: {analysis['total_deltas']}")
        
        if analysis["delta_types"]:
            print(f"   Delta Types:")
            for delta_type, count in analysis["delta_types"].items():
                print(f"     {delta_type}: {count}")
        
        if analysis["parameters"]:
            print(f"   Parameters:")
            for param, count in analysis["parameters"].items():
                print(f"     {param}: {count}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error analyzing project: {e}")
        return {}

def test_audio_asset(filepath: str) -> bool:
    """Test audio asset loading and analysis"""
    if not STAVE_MODULES_AVAILABLE:
        print("❌ STAVE modules not available")
        return False
    
    try:
        print(f"🎵 Testing audio asset: {filepath}")
        
        # Create asset
        asset = AudioAsset(filepath, load_on_init=True)
        
        print(f"✅ Created asset: {asset.asset_id}")
        print(f"   File: {asset.filepath.name}")
        print(f"   Hash: {asset.content_hash[:16]}...")
        
        if asset.metadata:
            print(f"   Duration: {asset.metadata.duration:.2f}s")
            print(f"   Sample Rate: {asset.metadata.sample_rate}Hz")
            print(f"   Channels: {asset.metadata.channels}")
            print(f"   Format: {asset.metadata.format}")
        
        # Test analysis
        analysis = asset.analyze_audio()
        if analysis and "status" not in analysis:
            print(f"📊 Audio Analysis:")
            print(f"   RMS Energy: {analysis.get('rms_energy', 0):.4f}")
            print(f"   Peak Amplitude: {analysis.get('peak_amplitude', 0):.4f}")
            print(f"   Spectral Centroid: {analysis.get('spectral_centroid', 0):.1f}Hz")
            if analysis.get('estimated_tempo'):
                print(f"   Estimated Tempo: {analysis['estimated_tempo']:.1f}BPM")
        
        # Test memory usage
        usage = asset.get_memory_usage()
        print(f"💾 Memory Usage: {usage['total_size']/1024:.1f}KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing audio asset: {e}")
        return False

def run_system_test() -> bool:
    """Run comprehensive system test"""
    print("🧪 Running STAVE System Test")
    print("=" * 50)
    
    if not STAVE_MODULES_AVAILABLE:
        print("❌ STAVE modules not available - cannot run system test")
        return False
    
    try:
        # Test 1: Delta creation and validation
        print("\n1️⃣ Testing delta creation and validation...")
        test_delta = DeltaLibrary.create_pitch_shift("test.wav", +3.5)
        validation = DeltaValidator.validate_delta(test_delta)
        
        if validation["valid"]:
            print("   ✅ Delta creation and validation: PASS")
        else:
            print("   ❌ Delta creation and validation: FAIL")
            return False
        
        # Test 2: Delta stack operations
        print("\n2️⃣ Testing delta stack operations...")
        stack = DeltaStack("test_stack", "test.wav")
        
        # Add multiple deltas
        deltas = [
            DeltaLibrary.create_pitch_shift("test.wav", +1.0),
            DeltaLibrary.create_emotional_shift("test.wav", "calm", 0.6),
            DeltaLibrary.create_prosody_adjustment("test.wav", 0.9, ["slow", "gentle"])
        ]
        
        for delta in deltas:
            stack.add_delta(delta)
        
        stats = stack.get_stack_stats()
        if stats["total_deltas"] == len(deltas):
            print("   ✅ Delta stack operations: PASS")
        else:
            print("   ❌ Delta stack operations: FAIL")
            return False
        
        # Test 3: Stack serialization
        print("\n3️⃣ Testing stack serialization...")
        stack_dict = stack.to_dict()
        
        if "deltas" in stack_dict and len(stack_dict["deltas"]) == len(deltas):
            print("   ✅ Stack serialization: PASS")
        else:
            print("   ❌ Stack serialization: FAIL")
            return False
        
        # Test 4: Asset manager
        print("\n4️⃣ Testing asset manager...")
        manager = AudioAssetManager(cache_limit_mb=128)
        usage = manager.get_memory_usage()
        
        if usage["total_assets"] == 0:
            print("   ✅ Asset manager: PASS")
        else:
            print("   ❌ Asset manager: FAIL")
            return False
        
        print("\n🎉 All system tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ System test failed: {e}")
        return False

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="STAVE - Semantic Temporal Audio Vector Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  stave_cli.py test                           # Run system test
  stave_cli.py create-project MyProject ./   # Create test project
  stave_cli.py validate delta.cdelta          # Validate delta file
  stave_cli.py analyze project.stave          # Analyze project
  stave_cli.py audio-test audio.wav           # Test audio asset
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run system test')
    
    # Create project command
    create_parser = subparsers.add_parser('create-project', help='Create test project')
    create_parser.add_argument('name', help='Project name')
    create_parser.add_argument('output_dir', help='Output directory')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate delta file')
    validate_parser.add_argument('filepath', help='Path to .cdelta file')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze project file')
    analyze_parser.add_argument('filepath', help='Path to .stave file')
    
    # Audio test command
    audio_parser = subparsers.add_parser('audio-test', help='Test audio asset')
    audio_parser.add_argument('filepath', help='Path to audio file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("🎵 STAVE - Semantic Temporal Audio Vector Engine")
    print("   Version: 0.1.0-luthier")
    print("   Tagline: Don't record the world. Record the change.")
    print()
    
    success = False
    
    if args.command == 'test':
        success = run_system_test()
    
    elif args.command == 'create-project':
        success = create_test_project(args.name, args.output_dir)
    
    elif args.command == 'validate':
        success = validate_delta_file(args.filepath)
    
    elif args.command == 'analyze':
        result = analyze_project(args.filepath)
        success = bool(result)
    
    elif args.command == 'audio-test':
        success = test_audio_asset(args.filepath)
    
    if success:
        print("\n✅ Operation completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
