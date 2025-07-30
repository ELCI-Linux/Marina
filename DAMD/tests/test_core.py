"""
Tests for DAMD core functionality.
"""

import tempfile
import pytest
from pathlib import Path

from damd.core import DAMDFile, DAMDSegment, DAMDError
from damd.utils import calculate_checksum


class TestDAMDSegment:
    """Test DAMDSegment functionality."""
    
    def test_segment_creation(self):
        """Test creating a DAMD segment."""
        data = b"test data"
        segment = DAMDSegment(
            key="test",
            data=data,
            content_type="text/plain"
        )
        
        assert segment.key == "test"
        assert segment.data == data
        assert segment.content_type == "text/plain"
        assert segment.compressed is False
        assert segment.checksum is not None
        assert segment.checksum == calculate_checksum(data)
    
    def test_segment_to_dict(self):
        """Test converting segment to dictionary."""
        data = b"test data"
        segment = DAMDSegment(
            key="test",
            data=data,
            content_type="text/plain"
        )
        
        segment_dict = segment.to_dict()
        assert segment_dict["key"] == "test"
        assert segment_dict["data"] == data
        assert segment_dict["content_type"] == "text/plain"
    
    def test_segment_from_dict(self):
        """Test creating segment from dictionary."""
        data = b"test data"
        segment_dict = {
            "key": "test",
            "data": data,
            "content_type": "text/plain",
            "compressed": False,
            "checksum": calculate_checksum(data),
            "timestamp": None,
            "metadata": {}
        }
        
        segment = DAMDSegment.from_dict(segment_dict)
        assert segment.key == "test"
        assert segment.data == data
        assert segment.content_type == "text/plain"


class TestDAMDFile:
    """Test DAMDFile functionality."""
    
    def test_empty_file(self):
        """Test working with an empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            damd_file = DAMDFile(temp_file)
            damd_file.load()
            
            assert len(damd_file.list_segments()) == 0
            assert damd_file._original_size == 0
        finally:
            temp_file.unlink()
    
    def test_add_and_retrieve_segment(self):
        """Test adding and retrieving segments."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Original file content")
            temp_file = Path(f.name)
        
        try:
            damd_file = DAMDFile(temp_file)
            
            # Add a segment
            test_data = "This is test metadata"
            damd_file.add_segment(
                key="test_meta",
                data=test_data,
                content_type="text/plain"
            )
            
            # Retrieve the segment
            retrieved_data = damd_file.get_text("test_meta")
            assert retrieved_data == test_data
            
            # Check segment exists
            assert "test_meta" in damd_file.list_segments()
            
        finally:
            temp_file.unlink()
    
    def test_save_and_load_cycle(self):
        """Test saving and loading DAMD data."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Original file content")
            temp_file = Path(f.name)
        
        try:
            # Create and save DAMD data
            damd_file = DAMDFile(temp_file)
            damd_file.add_segment("key1", "value1")
            damd_file.add_segment("key2", "value2")
            damd_file.save()
            
            # Load from a new instance
            damd_file2 = DAMDFile(temp_file)
            damd_file2.load()
            
            assert len(damd_file2.list_segments()) == 2
            assert damd_file2.get_text("key1") == "value1"
            assert damd_file2.get_text("key2") == "value2"
            
        finally:
            temp_file.unlink()
    
    def test_remove_segment(self):
        """Test removing segments."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Original file content")
            temp_file = Path(f.name)
        
        try:
            damd_file = DAMDFile(temp_file)
            damd_file.add_segment("key1", "value1")
            damd_file.add_segment("key2", "value2")
            
            # Remove one segment
            success = damd_file.remove_segment("key1")
            assert success is True
            
            # Check it's gone
            assert "key1" not in damd_file.list_segments()
            assert "key2" in damd_file.list_segments()
            
            # Try to remove non-existent segment
            success = damd_file.remove_segment("nonexistent")
            assert success is False
            
        finally:
            temp_file.unlink()
    
    def test_binary_data(self):
        """Test handling binary data."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Original file content")
            temp_file = Path(f.name)
        
        try:
            damd_file = DAMDFile(temp_file)
            
            # Add binary data
            binary_data = b"\x00\x01\x02\x03\xFF\xFE\xFD\xFC"
            damd_file.add_segment(
                key="binary_test",
                data=binary_data,
                content_type="application/octet-stream",
                compress=False
            )
            
            # Retrieve binary data
            retrieved_data = damd_file.get_data("binary_test")
            assert retrieved_data == binary_data
            
        finally:
            temp_file.unlink()
    
    def test_file_info(self):
        """Test getting file information."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Original file content")
            temp_file = Path(f.name)
        
        try:
            damd_file = DAMDFile(temp_file)
            damd_file.add_segment("test", "data")
            
            info = damd_file.get_info()
            
            assert "filepath" in info
            assert "original_size" in info
            assert "segment_count" in info
            assert "total_metadata_size" in info
            assert "segments" in info
            
            assert info["segment_count"] == 1
            assert "test" in info["segments"]
            
        finally:
            temp_file.unlink()
    
    def test_nonexistent_file(self):
        """Test handling non-existent files."""
        nonexistent = Path("/nonexistent/path/file.txt")
        damd_file = DAMDFile(nonexistent)
        
        with pytest.raises(DAMDError):
            damd_file.load()
    
    def test_compression(self):
        """Test data compression."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Original file content")
            temp_file = Path(f.name)
        
        try:
            damd_file = DAMDFile(temp_file)
            
            # Add compressible data
            large_text = "Hello world! " * 100  # Repeating text should compress well
            damd_file.add_segment(
                key="compressible",
                data=large_text,
                compress=True
            )
            
            # Retrieve and verify
            retrieved_text = damd_file.get_text("compressible")
            assert retrieved_text == large_text
            
            # Check that it was marked as compressed
            segment = damd_file.get_segment("compressible")
            assert segment.compressed is True
            
        finally:
            temp_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__])
