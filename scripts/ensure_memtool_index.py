#!/usr/bin/env python3
"""
Ensure memtool server has an index loaded.

This script checks if the memtool server has an index, and if not,
builds/loads one from the wikicontent repository.

Usage:
    python scripts/ensure_memtool_index.py
"""
import sys
import os
from pathlib import Path
import toml

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    # Load config to get wikicontent path
    config_path = Path(__file__).parent.parent / "config.toml"
    if not config_path.exists():
        print("❌ config.toml not found")
        return 1
    
    config = toml.load(config_path)
    content_repo = Path(config['paths']['content_repo'])
    
    if not content_repo.exists():
        print(f"❌ wikicontent not found at: {content_repo}")
        return 1
    
    # Change to wikicontent directory
    os.chdir(content_repo)
    index_file = content_repo / ".memtool_index.json"
    
    try:
        from memtool.client import MemtoolClient
        
        # Connect to server
        try:
            client = MemtoolClient(port=18861)
        except Exception as e:
            print(f"❌ Cannot connect to memtool server on port 18861")
            print(f"   Make sure it's running: ./start.sh")
            return 1
        
        # Check if index is loaded
        status = client.status()
        
        if status['loaded']:
            print(f"✓ Index already loaded: {status['summary']['num_files']} files, {status['summary']['num_intervals']} intervals")
            client.close()
            return 0
        
        # Index not loaded - try to load from disk
        print("⚠️  No index loaded in server")
        
        if index_file.exists():
            print(f"   Loading index from: {index_file}")
            try:
                result = client.load_index(".memtool_index.json")
                print(f"✓ Index loaded: {result['summary']['num_files']} files, {result['summary']['num_intervals']} intervals")
                client.close()
                return 0
            except Exception as e:
                print(f"⚠️  Failed to load cached index: {e}")
                print("   Building fresh index...")
        else:
            print("   No cached index found, building fresh...")
        
        # Build fresh index
        print(f"   Indexing: {content_repo}")
        result = client.build_index(".")
        summary = result['summary']
        print(f"✓ Index built: {summary['num_files']} files, {summary['num_intervals']} intervals")
        
        # Save for next time
        client.save_index(".memtool_index.json")
        print(f"✓ Index saved to: {index_file}")
        
        client.close()
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

