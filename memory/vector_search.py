#!/usr/bin/env python3
"""
Vector Memory Search
Semantic search over memories using embeddings.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
MEMORY_DIR = f"{WORKSPACE}/memory"
VECTOR_DIR = f"{MEMORY_DIR}/vectors"

def get_embedding(text):
    """Get embedding for text using OpenAI or fallback to hash."""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    
    if not api_key:
        # Fallback to simple hash-based representation
        return {
            'text_hash': hashlib.md5(text.encode()).hexdigest(),
            'keywords': extract_keywords(text),
            'timestamp': datetime.now().isoformat()
        }
    
    try:
        import openai
        response = openai.Embedding.create(
            model="text-embedding-3-small",
            input=text[:8000]
        )
        return {
            'embedding': response['data'][0]['embedding'],
            'text_hash': hashlib.md5(text.encode()).hexdigest(),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Embedding error: {e}")
        return {
            'text_hash': hashlib.md5(text.encode()).hexdigest(),
            'keywords': extract_keywords(text),
            'timestamp': datetime.now().isoformat()
        }

def extract_keywords(text):
    """Extract simple keywords from text."""
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
                 'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                 'from', 'as', 'into', 'through', 'during', 'before', 'after',
                 'above', 'below', 'between', 'under', 'again', 'further', 'then',
                 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
                 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
                 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
                 'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while',
                 'this', 'that', 'these', 'those', 'i', 'me', 'my', 'myself',
                 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'he',
                 'him', 'his', 'she', 'her', 'hers', 'it', 'its', 'they', 'them',
                 'their', 'theirs', 'what', 'which', 'who', 'whom', 'itself'}
    
    words = text.lower().split()
    keywords = [w for w in words if len(w) > 3 and w not in stopwords]
    return list(set(keywords))[:20]

def keyword_search(query, documents, top_k=5):
    """Simple keyword-based search."""
    query_keywords = set(extract_keywords(query))
    
    scored = []
    for doc in documents:
        doc_keywords = set(doc.get('keywords', []))
        score = len(query_keywords & doc_keywords)
        if score > 0:
            scored.append((score, doc))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:top_k]]

def semantic_search(query, memories_dir=None, top_k=5):
    """Search memories semantically."""
    if memories_dir is None:
        memories_dir = MEMORY_DIR
    
    # Collect all memory files
    memory_files = []
    
    # Daily memory files
    if os.path.exists(memories_dir):
        for f in os.listdir(memories_dir):
            if f.endswith('.md') and f.startswith('20'):
                memory_files.append(os.path.join(memories_dir, f))
    
    # Pre-compaction dumps
    precompact_dir = os.path.join(memories_dir, 'precompact')
    if os.path.exists(precompact_dir):
        for f in os.listdir(precompact_dir):
            if f.endswith('.json') and f != 'latest.json':
                memory_files.append(os.path.join(precompact_dir, f))
    
    # Read and index memories
    documents = []
    for filepath in memory_files:
        try:
            if filepath.endswith('.md'):
                with open(filepath, 'r') as f:
                    content = f.read()
                    documents.append({
                        'source': filepath,
                        'content': content,
                        'keywords': extract_keywords(content),
                        'timestamp': os.path.getmtime(filepath)
                    })
            elif filepath.endswith('.json'):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    content = json.dumps(data)
                    documents.append({
                        'source': filepath,
                        'content': content,
                        'keywords': extract_keywords(content),
                        'timestamp': os.path.getmtime(filepath)
                    })
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    
    # Search
    results = keyword_search(query, documents, top_k)
    
    return results

def get_relevant_memories(query, hours=24):
    """Get memories from last N hours."""
    cutoff = datetime.now() - timedelta(hours=hours)
    
    results = semantic_search(query, top_k=10)
    
    # Filter by recency
    recent_results = []
    for r in results:
        try:
            ts = datetime.fromisoformat(r.get('timestamp', '2000-01-01'))
            if ts > cutoff:
                recent_results.append(r)
        except:
            recent_results.append(r)
    
    return recent_results[:5]

def inject_memories_into_context(query):
    """Main entry point - find and return relevant memories."""
    memories = get_relevant_memories(query, hours=24)
    
    if not memories:
        return None
    
    context = "=== RELEVANT MEMORIES ===\n"
    for i, m in enumerate(memories, 1):
        source = os.path.basename(m.get('source', 'unknown'))
        content = m.get('content', '')[:500]
        context += f"\n{i}. [{source}]\n{content}\n"
    
    context += "\n=== END MEMORIES ===\n"
    return context

def main():
    """Test memory search."""
    query = "Google Drive OAuth setup"
    results = semantic_search(query, top_k=3)
    
    print(f"Search for '{query}':")
    for r in results:
        print(f"  - {r.get('source', 'unknown')}")
        print(f"    Score: {r.get('keywords', [])[:5]}")

if __name__ == '__main__':
    main()
