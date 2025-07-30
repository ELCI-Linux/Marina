#!/usr/bin/env python3
"""
DAMD Demo Script

This script demonstrates various DAMD operations:
1. Creating DAMD-enabled files
2. Adding metadata segments
3. Reading embedded data
4. File type-specific processing
"""

import json
import tempfile
from pathlib import Path

from damd import DAMDFile
from damd.handlers import get_handler


def demo_basic_operations():
    """Demonstrate basic DAMD operations."""
    print("=== Basic DAMD Operations Demo ===")
    
    # Create a temporary file to work with
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a sample text file for DAMD demonstration.\n")
        f.write("It contains some content that we'll add metadata to.\n")
        temp_file = Path(f.name)
    
    try:
        # Create DAMD file instance
        damd_file = DAMDFile(temp_file)
        
        # Add some metadata segments
        print(f"Adding metadata to {temp_file.name}...")
        
        damd_file.add_segment(
            key="description",
            data="This is a demo file for DAMD operations",
            content_type="text/plain"
        )
        
        damd_file.add_segment(
            key="tags",
            data=json.dumps(["demo", "example", "text", "damd"]),
            content_type="application/json"
        )
        
        damd_file.add_segment(
            key="author",
            data="DAMD Demo Script",
            content_type="text/plain"
        )
        
        # Save the DAMD data
        damd_file.save()
        print("✓ Metadata segments added and saved")
        
        # List segments
        segments = damd_file.list_segments()
        print(f"✓ Found {len(segments)} segments: {', '.join(segments)}")
        
        # Read back the data
        print("\nReading back metadata:")
        for key in segments:
            data = damd_file.get_text(key)
            print(f"  {key}: {data}")
        
        # Show file info
        info = damd_file.get_info()
        print(f"\nFile info:")
        print(f"  Original size: {info['original_size']} bytes")
        print(f"  Metadata size: {info['total_metadata_size']} bytes")
        print(f"  Segments: {info['segment_count']}")
        
    finally:
        # Cleanup
        temp_file.unlink()


def demo_image_processing():
    """Demonstrate image-specific DAMD operations."""
    print("\n=== Image Processing Demo ===")
    
    # Create a simple test image
    try:
        from PIL import Image
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_image = Path(f.name)
        
        # Create a simple test image
        img = Image.new('RGB', (200, 100), color='red')
        img.save(temp_image)
        
        print(f"Created test image: {temp_image.name}")
        
        # Get appropriate handler
        handler = get_handler(temp_image)
        if handler:
            print(f"✓ Found handler: {handler.__class__.__name__}")
            
            # Process the image
            damd_file = DAMDFile(temp_image)
            handler.process_file(temp_image, damd_file)
            damd_file.save()
            
            print("✓ Image processed and metadata extracted")
            
            # Show what was extracted
            segments = damd_file.list_segments()
            print(f"✓ Extracted segments: {', '.join(segments)}")
            
            # Show image info if available
            if 'image_info' in segments:
                info_data = damd_file.get_text('image_info')
                info = json.loads(info_data)
                print(f"  Image dimensions: {info['width']}x{info['height']}")
                print(f"  Format: {info['format']}")
        else:
            print("✗ No handler found for image files")
        
        temp_image.unlink()
        
    except ImportError:
        print("✗ PIL not available, skipping image demo")


def demo_json_processing():
    """Demonstrate JSON file processing."""
    print("\n=== JSON Processing Demo ===")
    
    # Create a test JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_data = {
            "name": "DAMD Demo",
            "version": "1.0",
            "features": ["metadata", "compression", "handlers"],
            "config": {
                "compression": True,
                "checksum": True
            }
        }
        json.dump(test_data, f, indent=2)
        temp_json = Path(f.name)
    
    try:
        print(f"Created test JSON: {temp_json.name}")
        
        # Get appropriate handler
        handler = get_handler(temp_json)
        if handler:
            print(f"✓ Found handler: {handler.__class__.__name__}")
            
            # Process the JSON file
            damd_file = DAMDFile(temp_json)
            handler.process_file(temp_json, damd_file)
            damd_file.save()
            
            print("✓ JSON processed and metadata extracted")
            
            # Show what was extracted
            segments = damd_file.list_segments()
            print(f"✓ Extracted segments: {', '.join(segments)}")
            
            # Show text statistics
            if 'text_stats' in segments:
                stats_data = damd_file.get_text('text_stats')
                stats = json.loads(stats_data)
                print(f"  Lines: {stats['line_count']}")
                print(f"  Words: {stats['word_count']}")
                print(f"  Characters: {stats['char_count']}")
            
            # Show JSON schema info
            if 'json_schema' in segments:
                schema_data = damd_file.get_text('json_schema')
                schema = json.loads(schema_data)
                print(f"  JSON type: {schema['type']}")
                if schema['keys']:
                    print(f"  Top-level keys: {', '.join(schema['keys'])}")
        else:
            print("✗ No handler found for JSON files")
        
    finally:
        temp_json.unlink()


def demo_custom_metadata():
    """Demonstrate adding custom metadata."""
    print("\n=== Custom Metadata Demo ===")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Sample file for custom metadata demo.")
        temp_file = Path(f.name)
    
    try:
        damd_file = DAMDFile(temp_file)
        
        # Add various types of custom metadata
        print("Adding custom metadata...")
        
        # Text metadata
        damd_file.add_segment(
            key="notes",
            data="This file demonstrates custom metadata storage",
            content_type="text/plain"
        )
        
        # JSON metadata
        metadata_obj = {
            "created_by": "demo_script",
            "purpose": "demonstration",
            "timestamp": "2024-01-01T00:00:00Z",
            "tags": ["demo", "metadata", "custom"]
        }
        damd_file.add_segment(
            key="custom_metadata",
            data=json.dumps(metadata_obj),
            content_type="application/json"
        )
        
        # Binary metadata (simulate a small thumbnail or hash)
        binary_data = b"\x00\x01\x02\x03\xFF\xFE\xFD\xFC"
        damd_file.add_segment(
            key="binary_data",
            data=binary_data,
            content_type="application/octet-stream",
            compress=False  # Don't compress small binary data
        )
        
        damd_file.save()
        print("✓ Custom metadata added")
        
        # Verify the data
        print("\nVerifying custom metadata:")
        
        notes = damd_file.get_text("notes")
        print(f"  Notes: {notes}")
        
        custom_meta = damd_file.get_text("custom_metadata")
        custom_obj = json.loads(custom_meta)
        print(f"  Custom metadata keys: {', '.join(custom_obj.keys())}")
        
        binary = damd_file.get_data("binary_data")
        print(f"  Binary data: {binary.hex()} ({len(binary)} bytes)")
        
    finally:
        temp_file.unlink()


if __name__ == "__main__":
    print("DAMD (Data As Metadata in Data) Demo")
    print("=" * 50)
    
    try:
        demo_basic_operations()
        demo_image_processing()
        demo_json_processing()
        demo_custom_metadata()
        
        print("\n" + "=" * 50)
        print("✓ All demos completed successfully!")
        print("\nTry the CLI tools:")
        print("  damdinfo  - Show available handlers")
        print("  damdwrite <file> - Process file and add metadata")
        print("  damdls <file> - List segments in file")
        print("  damdcat <file> <key> - Show segment data")
        print("  damdrm <file> <key> - Remove segment")
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
