#!/usr/bin/env python3
"""Simple test script to verify Tavily API is working."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.config import get_logger  # noqa: E402
from app.infrastructure.http.tavily import TAVILY_API_KEY, search_news  # noqa: E402

logger = get_logger(__name__)


async def test_tavily():
    """Test Tavily API with a simple query."""
    print("=" * 60)
    print("TAVILY API TEST")
    print("=" * 60)
    
    # Check API key
    print("\n1. Checking TAVILY_API_KEY...")
    if not TAVILY_API_KEY:
        print("   ❌ TAVILY_API_KEY is NOT configured!")
        print("   Set it in your .env file or environment variables")
        return False
    else:
        key_length = len(TAVILY_API_KEY)
        if key_length > 12:
            masked_key = (
                f"{TAVILY_API_KEY[:8]}{'*' * (key_length - 12)}{TAVILY_API_KEY[-4:]}"
            )
        else:
            masked_key = "*" * key_length
        print(
            "   ✅ TAVILY_API_KEY is configured "
            f"(length: {key_length}, masked: {masked_key})"
        )
    
    # Test queries
    test_queries = [
        "Bitcoin price prediction 2024",
        "Ethereum news today",
        "Stock market today",
    ]
    
    print("\n2. Testing Tavily API with sample queries...")
    print("-" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Test {i}: Query = '{query}'")
        try:
            result = await search_news(query, max_results=5)
            
            articles = result.get("articles", [])
            answer = result.get("answer", "")
            
            print("   ✅ Success!")
            print(f"   - Articles found: {len(articles)}")
            print(f"   - Answer length: {len(answer)} characters")
            
            if articles:
                print("\n   First article:")
                first = articles[0]
                print(f"   - Title: {first.get('title', 'N/A')[:80]}")
                print(f"   - URL: {first.get('url', 'N/A')[:80]}")
                print(f"   - Source: {first.get('source', 'N/A')}")
            else:
                print("   ⚠️  No articles returned!")
            
            if answer:
                print(f"\n   Answer preview: {answer[:200]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 60)
    print("✅ Tavily API test completed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_tavily())
    sys.exit(0 if success else 1)

