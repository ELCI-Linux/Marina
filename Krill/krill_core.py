#!/usr/bin/env python3
"""
Krill Core Engine - Marina's Small File Transfer Optimizer
"Millions of specks, one intelligent swarm."

Core functionality for batching, optimizing, and transferring small files
with maximum efficiency on consumer hardware.
"""

import os
import sys
import json
import hashlib
import tarfile
import zipfile
import tempfile
import shutil
import time
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import zlib
import gzip
import lzma
from concurrent.futures import ThreadPoolExecutor, as_completed
import xxhash
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('krill')

@dataclass
class FileInfo:
    """Metadata for a single file in the Krill system"""
    path: str
    size: int
    hash_sha1: str
    hash_xxh64: Optional[str] = None
    mtime: float = 0.0
    entropy: float = 0.0
    compressibility: float = 0.0
    semantic_category: str = "unknown"
    access_frequency: int = 0
    last_access: float = 0.0
    compression_ratio: Optional[float] = None

@dataclass
class KrillBundle:
    """Represents a bundled collection of small files optimized for transfer"""
    bundle_id: str
    files: List[FileInfo]
    total_size: int
    compressed_size: int
    compression_type: str
    bundle_hash: str
    created_at: float
    transfer_priority: int = 0
    bundle_type: str = "standard"  # standard, delta, semantic, temporal

@dataclass
class TransferStats:
    """Statistics for transfer operations"""
    files_processed: int = 0
    files_skipped: int = 0
    files_transferred: int = 0
    bytes_scanned: int = 0
    bytes_transferred: int = 0
    bytes_saved: int = 0
    compression_ratio: float = 0.0
    transfer_time: float = 0.0
    throughput_mbps: float = 0.0

class KrillHashMesh:
    """Fast pre-transfer scanning to skip files already present on target"""
    
    def __init__(self, hash_cache_path: str = None):
        self.hash_cache_path = hash_cache_path or os.path.expanduser("~/.krill/hash_cache.json")
        self.hash_cache = self._load_hash_cache()
        self.hash_lock = threading.Lock()
    
    def _load_hash_cache(self) -> Dict[str, Dict]:
        """Load existing hash cache from disk"""
        try:
            if os.path.exists(self.hash_cache_path):
                with open(self.hash_cache_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load hash cache: {e}")
        return {}
    
    def save_hash_cache(self):
        """Save hash cache to disk"""
        try:
            os.makedirs(os.path.dirname(self.hash_cache_path), exist_ok=True)
            with open(self.hash_cache_path, 'w') as f:
                json.dump(self.hash_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save hash cache: {e}")
    
    def compute_file_hash(self, file_path: str, use_xxhash: bool = True) -> Tuple[str, Optional[str]]:
        """Compute SHA-1 and optional xxHash for a file"""
        sha1_hash = hashlib.sha1()
        xxh_hash = xxhash.xxh64() if use_xxhash else None
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha1_hash.update(chunk)
                    if xxh_hash:
                        xxh_hash.update(chunk)
            
            return sha1_hash.hexdigest(), xxh_hash.hexdigest() if xxh_hash else None
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            return "", None
    
    def is_file_cached(self, file_path: str, file_size: int, mtime: float) -> bool:
        """Check if file is already in cache and hasn't changed"""
        with self.hash_lock:
            cache_key = os.path.abspath(file_path)
            if cache_key in self.hash_cache:
                cached = self.hash_cache[cache_key]
                return (cached.get('size') == file_size and 
                       cached.get('mtime') == mtime)
        return False
    
    def get_or_compute_hash(self, file_path: str) -> FileInfo:
        """Get file hash from cache or compute if not cached"""
        abs_path = os.path.abspath(file_path)
        stat = os.stat(abs_path)
        
        if self.is_file_cached(abs_path, stat.st_size, stat.st_mtime):
            cached = self.hash_cache[abs_path]
            return FileInfo(
                path=file_path,
                size=stat.st_size,
                hash_sha1=cached['hash_sha1'],
                hash_xxh64=cached.get('hash_xxh64'),
                mtime=stat.st_mtime,
                entropy=cached.get('entropy', 0.0),
                compressibility=cached.get('compressibility', 0.0)
            )
        
        # Compute new hash
        sha1_hash, xxh_hash = self.compute_file_hash(abs_path)
        entropy = self._calculate_entropy(abs_path)
        compressibility = self._estimate_compressibility(abs_path)
        
        file_info = FileInfo(
            path=file_path,
            size=stat.st_size,
            hash_sha1=sha1_hash,
            hash_xxh64=xxh_hash,
            mtime=stat.st_mtime,
            entropy=entropy,
            compressibility=compressibility
        )
        
        # Cache the result
        with self.hash_lock:
            self.hash_cache[abs_path] = {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'hash_sha1': sha1_hash,
                'hash_xxh64': xxh_hash,
                'entropy': entropy,
                'compressibility': compressibility,
                'cached_at': time.time()
            }
        
        return file_info
    
    def _calculate_entropy(self, file_path: str) -> float:
        """Calculate Shannon entropy of file content"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(min(8192, os.path.getsize(file_path)))  # Sample first 8KB
            
            if not data:
                return 0.0
            
            # Count byte frequencies
            freq = [0] * 256
            for byte in data:
                freq[byte] += 1
            
            # Calculate entropy
            entropy = 0.0
            data_len = len(data)
            for count in freq:
                if count > 0:
                    p = count / data_len
                    entropy -= p * (p.bit_length() - 1 if p > 0 else 0)
            
            return min(entropy, 8.0)  # Normalize to 0-8 range
        except Exception:
            return 0.0
    
    def _estimate_compressibility(self, file_path: str) -> float:
        """Estimate how well a file will compress"""
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(min(4096, os.path.getsize(file_path)))
            
            if not sample:
                return 0.0
            
            # Test compression ratio with zlib
            compressed = zlib.compress(sample, level=1)  # Fast compression for estimation
            ratio = len(compressed) / len(sample)
            
            return 1.0 - ratio  # Higher value = more compressible
        except Exception:
            return 0.0

class KrillClusterBundler:
    """Dynamically batches thousands of small files into optimized bundles"""
    
    def __init__(self, max_bundle_size: int = 50 * 1024 * 1024):  # 50MB default
        self.max_bundle_size = max_bundle_size
        self.hash_mesh = KrillHashMesh()
        
    def scan_directory(self, directory: str, include_patterns: List[str] = None, 
                      exclude_patterns: List[str] = None, max_file_size: int = 10 * 1024 * 1024) -> List[FileInfo]:
        """Scan directory for small files matching criteria"""
        files = []
        directory = Path(directory)
        
        for file_path in directory.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Size filter
            if file_path.stat().st_size > max_file_size:
                continue
            
            # Pattern filters
            if include_patterns and not any(file_path.match(pattern) for pattern in include_patterns):
                continue
            
            if exclude_patterns and any(file_path.match(pattern) for pattern in exclude_patterns):
                continue
            
            file_info = self.hash_mesh.get_or_compute_hash(str(file_path))
            file_info.semantic_category = self._categorize_file(file_path)
            files.append(file_info)
        
        logger.info(f"Scanned {len(files)} files in {directory}")
        return files
    
    def _categorize_file(self, file_path: Path) -> str:
        """Categorize file based on extension and content"""
        ext = file_path.suffix.lower()
        
        categories = {
            'config': ['.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.cfg'],
            'code': ['.py', '.js', '.ts', '.go', '.rs', '.c', '.cpp', '.h', '.java'],
            'markup': ['.html', '.xml', '.md', '.rst', '.tex'],
            'data': ['.csv', '.tsv', '.sql', '.db'],
            'log': ['.log', '.out', '.err'],
            'text': ['.txt', '.readme'],
            'binary': ['.so', '.dll', '.exe', '.bin']
        }
        
        for category, extensions in categories.items():
            if ext in extensions:
                return category
        
        return 'misc'
    
    def create_entropy_bundles(self, files: List[FileInfo]) -> List[KrillBundle]:
        """Create bundles grouped by entropy/compressibility characteristics"""
        # Sort files by compressibility
        files.sort(key=lambda f: (f.compressibility, f.semantic_category))
        
        bundles = []
        current_bundle_files = []
        current_size = 0
        
        for file_info in files:
            if (current_size + file_info.size > self.max_bundle_size and 
                current_bundle_files):
                # Create bundle from current files
                bundle = self._create_bundle(current_bundle_files, "entropy")
                bundles.append(bundle)
                current_bundle_files = []
                current_size = 0
            
            current_bundle_files.append(file_info)
            current_size += file_info.size
        
        # Create final bundle if files remain
        if current_bundle_files:
            bundle = self._create_bundle(current_bundle_files, "entropy")
            bundles.append(bundle)
        
        return bundles
    
    def create_semantic_bundles(self, files: List[FileInfo]) -> List[KrillBundle]:
        """Create bundles grouped by semantic category"""
        category_files = defaultdict(list)
        
        for file_info in files:
            category_files[file_info.semantic_category].append(file_info)
        
        bundles = []
        for category, cat_files in category_files.items():
            # Further subdivide large categories
            while cat_files:
                bundle_files = []
                bundle_size = 0
                
                while cat_files and bundle_size < self.max_bundle_size:
                    file_info = cat_files.pop(0)
                    if bundle_size + file_info.size <= self.max_bundle_size:
                        bundle_files.append(file_info)
                        bundle_size += file_info.size
                    else:
                        cat_files.insert(0, file_info)
                        break
                
                if bundle_files:
                    bundle = self._create_bundle(bundle_files, f"semantic_{category}")
                    bundles.append(bundle)
        
        return bundles
    
    def _create_bundle(self, files: List[FileInfo], bundle_type: str) -> KrillBundle:
        """Create a bundle from a list of files"""
        bundle_id = f"krill_{int(time.time())}_{hash(tuple(f.path for f in files))[:8]}"
        total_size = sum(f.size for f in files)
        
        # Determine best compression based on file characteristics
        avg_compressibility = sum(f.compressibility for f in files) / len(files)
        if avg_compressibility > 0.7:
            compression_type = "lzma"
        elif avg_compressibility > 0.4:
            compression_type = "gzip"
        else:
            compression_type = "none"
        
        # Calculate transfer priority based on various factors
        priority = self._calculate_priority(files)
        
        return KrillBundle(
            bundle_id=bundle_id,
            files=files,
            total_size=total_size,
            compressed_size=0,  # Will be calculated during actual compression
            compression_type=compression_type,
            bundle_hash="",  # Will be calculated during compression
            created_at=time.time(),
            transfer_priority=priority,
            bundle_type=bundle_type
        )
    
    def _calculate_priority(self, files: List[FileInfo]) -> int:
        """Calculate transfer priority based on file characteristics"""
        # Higher priority for:
        # - Recently modified files
        # - Frequently accessed files
        # - Configuration files
        # - Smaller total size (faster to transfer)
        
        recent_bonus = sum(1 for f in files if time.time() - f.mtime < 86400)  # 24 hours
        config_bonus = sum(1 for f in files if f.semantic_category == 'config')
        size_penalty = sum(f.size for f in files) // (1024 * 1024)  # MB penalty
        
        priority = recent_bonus * 10 + config_bonus * 5 - size_penalty
        return max(0, min(100, priority))

class KrillTransferEngine:
    """Handles the actual transfer of Krill bundles with protocol optimization"""
    
    def __init__(self):
        self.stats = TransferStats()
        self.transfer_lock = threading.Lock()
    
    def create_physical_bundle(self, bundle: KrillBundle, output_path: str) -> str:
        """Create the actual compressed bundle file"""
        bundle_path = os.path.join(output_path, f"{bundle.bundle_id}.krill")
        
        if bundle.compression_type == "none":
            # Create uncompressed tar
            with tarfile.open(bundle_path, 'w') as tar:
                for file_info in bundle.files:
                    if os.path.exists(file_info.path):
                        tar.add(file_info.path, arcname=os.path.basename(file_info.path))
        
        elif bundle.compression_type == "gzip":
            # Create gzip compressed tar
            with tarfile.open(bundle_path, 'w:gz') as tar:
                for file_info in bundle.files:
                    if os.path.exists(file_info.path):
                        tar.add(file_info.path, arcname=os.path.basename(file_info.path))
        
        elif bundle.compression_type == "lzma":
            # Create LZMA compressed tar
            with tarfile.open(bundle_path, 'w:xz') as tar:
                for file_info in bundle.files:
                    if os.path.exists(file_info.path):
                        tar.add(file_info.path, arcname=os.path.basename(file_info.path))
        
        # Update bundle with actual compressed size and hash
        if os.path.exists(bundle_path):
            bundle.compressed_size = os.path.getsize(bundle_path)
            with open(bundle_path, 'rb') as f:
                bundle.bundle_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Save bundle metadata
        metadata_path = bundle_path + ".meta"
        with open(metadata_path, 'w') as f:
            json.dump(asdict(bundle), f, indent=2)
        
        logger.info(f"Created bundle {bundle.bundle_id}: {bundle.total_size} -> {bundle.compressed_size} bytes "
                   f"({bundle.compressed_size/bundle.total_size*100:.1f}% of original)")
        
        return bundle_path
    
    def extract_bundle(self, bundle_path: str, output_dir: str) -> bool:
        """Extract a Krill bundle to the specified directory"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            if bundle_path.endswith('.krill'):
                # Detect compression type by trying to open with different methods
                for open_mode in ['r:xz', 'r:gz', 'r']:
                    try:
                        with tarfile.open(bundle_path, open_mode) as tar:
                            tar.extractall(path=output_dir)
                        logger.info(f"Extracted bundle {bundle_path} to {output_dir}")
                        return True
                    except tarfile.ReadError:
                        continue
                
                logger.error(f"Failed to extract bundle {bundle_path}")
                return False
            
            return False
        except Exception as e:
            logger.error(f"Error extracting bundle {bundle_path}: {e}")
            return False
    
    def dry_run_analysis(self, source_dir: str, target_hashes: Set[str] = None) -> Dict:
        """Perform dry run analysis showing what would be transferred"""
        bundler = KrillClusterBundler()
        files = bundler.scan_directory(source_dir)
        
        if not files:
            return {"files_found": 0, "bundles": [], "total_size": 0}
        
        # Filter out files that already exist on target (if hash set provided)
        if target_hashes:
            files = [f for f in files if f.hash_sha1 not in target_hashes]
        
        # Create different bundle types for analysis
        entropy_bundles = bundler.create_entropy_bundles(files.copy())
        semantic_bundles = bundler.create_semantic_bundles(files.copy())
        
        analysis = {
            "files_found": len(files),
            "total_size": sum(f.size for f in files),
            "entropy_bundles": len(entropy_bundles),
            "semantic_bundles": len(semantic_bundles),
            "estimated_compression": {
                "entropy": sum(b.total_size for b in entropy_bundles),
                "semantic": sum(b.total_size for b in semantic_bundles)
            },
            "categories": dict(defaultdict(int))
        }
        
        for file_info in files:
            analysis["categories"][file_info.semantic_category] += 1
        
        return analysis

class KrillCLI:
    """Command-line interface for Krill operations"""
    
    def __init__(self):
        self.bundler = KrillClusterBundler()
        self.transfer_engine = KrillTransferEngine()
    
    def pack_command(self, source_dir: str, output_dir: str = None, bundle_type: str = "entropy",
                    include_patterns: List[str] = None, exclude_patterns: List[str] = None):
        """Pack directory into Krill bundles"""
        output_dir = output_dir or f"{source_dir}_krill_bundles"
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Packing {source_dir} -> {output_dir}")
        
        # Scan files
        files = self.bundler.scan_directory(source_dir, include_patterns, exclude_patterns)
        if not files:
            logger.warning("No files found to pack")
            return
        
        # Create bundles
        if bundle_type == "entropy":
            bundles = self.bundler.create_entropy_bundles(files)
        elif bundle_type == "semantic":
            bundles = self.bundler.create_semantic_bundles(files)
        else:
            bundles = self.bundler.create_entropy_bundles(files)  # Default
        
        # Create physical bundles
        bundle_paths = []
        for bundle in bundles:
            bundle_path = self.transfer_engine.create_physical_bundle(bundle, output_dir)
            bundle_paths.append(bundle_path)
        
        logger.info(f"Created {len(bundles)} bundles in {output_dir}")
        return bundle_paths
    
    def probe_command(self, source_dir: str, show_entropy: bool = False):
        """Analyze what would be transferred without actually doing it"""
        analysis = self.transfer_engine.dry_run_analysis(source_dir)
        
        print(f"\n🔍 Krill Probe Analysis for: {source_dir}")
        print(f"📁 Files found: {analysis['files_found']}")
        print(f"📦 Total size: {analysis['total_size'] / (1024*1024):.2f} MB")
        print(f"🗂️  Entropy bundles: {analysis['entropy_bundles']}")
        print(f"🏷️  Semantic bundles: {analysis['semantic_bundles']}")
        
        print("\n📊 File Categories:")
        for category, count in analysis["categories"].items():
            print(f"  {category}: {count} files")
        
        if show_entropy:
            print("\n⚡ Entropy Analysis:")
            print(f"  Entropy-based bundling: {analysis['estimated_compression']['entropy'] / (1024*1024):.2f} MB")
            print(f"  Semantic bundling: {analysis['estimated_compression']['semantic'] / (1024*1024):.2f} MB")
    
    def extract_command(self, bundle_path: str, output_dir: str):
        """Extract a Krill bundle"""
        success = self.transfer_engine.extract_bundle(bundle_path, output_dir)
        if success:
            logger.info(f"Successfully extracted {bundle_path}")
        else:
            logger.error(f"Failed to extract {bundle_path}")

def main():
    """Main entry point for Krill CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Krill - Marina's Small File Transfer Optimizer")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Pack command
    pack_parser = subparsers.add_parser('pack', help='Pack directory into Krill bundles')
    pack_parser.add_argument('source', help='Source directory to pack')
    pack_parser.add_argument('--output', '-o', help='Output directory for bundles')
    pack_parser.add_argument('--type', '-t', choices=['entropy', 'semantic'], default='entropy')
    pack_parser.add_argument('--include', nargs='*', help='Include patterns')
    pack_parser.add_argument('--exclude', nargs='*', help='Exclude patterns')
    
    # Probe command
    probe_parser = subparsers.add_parser('probe', help='Analyze directory without packing')
    probe_parser.add_argument('source', help='Source directory to analyze')
    probe_parser.add_argument('--show-entropy', action='store_true', help='Show entropy analysis')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract Krill bundle')
    extract_parser.add_argument('bundle', help='Bundle file to extract')
    extract_parser.add_argument('output', help='Output directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = KrillCLI()
    
    if args.command == 'pack':
        cli.pack_command(args.source, args.output, args.type, args.include, args.exclude)
    elif args.command == 'probe':
        cli.probe_command(args.source, args.show_entropy)
    elif args.command == 'extract':
        cli.extract_command(args.bundle, args.output)

if __name__ == "__main__":
    main()
