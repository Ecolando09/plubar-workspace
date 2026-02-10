#!/usr/bin/env python3
"""
Embed Memories
Embed and index memories in vector database for semantic search.
"""

import os
import json
from datetime import datetime

WORKSPACE = "/root/.openclaw/workspace"
MEMORY_DIR = f"{WORKSPACE}/memory"
VECTOR_DIR = f"{MEMORY_DIR}/vectors"

def embed_text(text, source):
    """Embed text using OpenAI or create metadata."""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    
    metadata = {
        'source': source,
        'timestamp': datetime.now().isoformat(),
        'text': text[:4000],
        'char_count': len(text)
    }
    
    if api_key:
        try:
            import openai
            response = openai.Embedding.create(
                model="text-embedding-3-small",
                input=text[:8000]
            )
            metadata['embedding'] = response['data'][0]['embedding']
            print(f"  Embedded {len(text)} chars with OpenAI")
        except Exception as e:
            print(f"  OpenAI embedding failed: {e}")
    else:
        print(f"  No API key - creating metadata only for {len(text)} chars")
    
    return metadata

def process_memory_files():
    """Process and embed all memory files."""
    os.makedirs(VECTOR_DIR, exist_ok=True)
    
    files_processed = []
    
    # Process daily memory files
    for filename in os.listdir(MEMORY_DIR):
        if filename.endswith('.md') and filename.startswith('20'):
            filepath = os.path.join(MEMORY_DIR, filename)
            with open(filepath, 'r') as f:
                content = f.read()
            
            output_file = os.path.join(VECTOR_DIR, f"{filename}.json")
            metadata = embed_text(content, filepath)
            
            with open(output_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            files_processed.append(filepath)
            print(f"Processed: {filename}")
    
    # Process pre-compaction dumps
    precompact_dir = os.path.join(MEMORY_DIR, 'precompact')
    if os.path.exists(precompact_dir):
        for filename in os.listdir(precompact_dir):
            if filename.endswith('.json') and filename != 'latest.json':
                filepath = os.path.join(precompact_dir, filename)
                with open(filepath, 'r') as f:
                    content = json.load(f)
                
                text = json.dumps(content)
                output_file = os.path.join(VECTOR_DIR, f"precompact_{filename}.json")
                metadata = embed_text(text, filepath)
                
                with open(output_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                files_processed.append(filepath)
                print(f"Processed: precompact/{filename}")
    
    print(f"\nTotal files processed: {len(files_processed)}")
    return files_processed

def main():
    """Run embedding job."""
    print(f"Running memory embedding at {datetime.now().isoformat()}")
    process_memory_files()

if __name__ == '__main__':
    main()
