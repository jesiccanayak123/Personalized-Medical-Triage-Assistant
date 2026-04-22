#!/usr/bin/env python3
"""
Seed script to ingest ICD-10 codes into pgvector for RAG.

Usage:
    python scripts/seed_icd10.py           # Interactive mode
    python scripts/seed_icd10.py --force   # Force re-seed without prompting
    python scripts/seed_icd10.py --check   # Just check existing data

This script loads ICD-10 codes from seed_icd10_data.json and ingests them
into the pgvector-enabled PostgreSQL database for semantic search.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection_manager import init_connection_manager, get_connection_manager
from modules.rag.service import RAGService
from database.dao.rag_documents import RAGDocumentsDao


async def load_seed_data() -> list:
    """Load seed data from JSON file."""
    seed_file = Path(__file__).parent / "seed_icd10_data.json"
    
    if not seed_file.exists():
        print(f"❌ Seed file not found: {seed_file}")
        sys.exit(1)
    
    with open(seed_file, "r") as f:
        data = json.load(f)
    
    return data.get("documents", [])


async def check_existing_data(rag_service: RAGService) -> int:
    """Check how many ICD-10 documents already exist."""
    stats = await rag_service.get_corpus_stats("icd10")
    return stats.get("data", {}).get("document_count", 0)


async def seed_icd10(force: bool = False, check_only: bool = False):
    """Main seeding function.
    
    Args:
        force: If True, delete and re-seed without prompting
        check_only: If True, just check existing data and exit
    """
    print("=" * 60)
    print("🏥 ICD-10 RAG Data Seeding Script")
    print("=" * 60)
    
    # Initialize database connection
    print("\n📦 Initializing database connection...")
    await init_connection_manager()
    cm = get_connection_manager()
    
    # Load seed data
    print("📄 Loading seed data...")
    documents = await load_seed_data()
    print(f"   Found {len(documents)} ICD-10 codes to ingest")
    
    async with cm.session_context() as session:
        # Create DAO and service
        rag_dao = RAGDocumentsDao(session)
        rag_service = RAGService(rag_dao=rag_dao)
        
        # Check existing data
        existing_count = await check_existing_data(rag_service)
        
        if check_only:
            print(f"\n📊 Existing ICD-10 documents: {existing_count}")
            if existing_count > 0:
                print("   ✅ RAG database is seeded and ready")
            else:
                print("   ⚠️  RAG database is empty - run without --check to seed")
            return
        
        if existing_count > 0:
            print(f"\n⚠️  Found {existing_count} existing ICD-10 documents")
            
            if force:
                print("   --force flag set, deleting existing documents...")
                await rag_service.delete_corpus("icd10")
                print("   ✅ Deleted existing documents")
            else:
                try:
                    response = input("   Do you want to delete and re-seed? (y/N): ").strip().lower()
                    if response == 'y':
                        print("   Deleting existing documents...")
                        await rag_service.delete_corpus("icd10")
                        print("   ✅ Deleted existing documents")
                    else:
                        print("   Skipping seed. Use --force to override.")
                        return
                except EOFError:
                    print("   Non-interactive mode detected. Use --force to re-seed.")
                    print("   ✅ Existing data is intact")
                    return
        
        # Ingest documents
        print(f"\n🔄 Ingesting {len(documents)} ICD-10 codes...")
        print("   (This may take a few minutes due to embedding generation)")
        print()
        
        try:
            result = await rag_service.ingest_icd10(documents=documents)
            
            print(f"\n✅ Successfully ingested {result.get('documents_ingested', 0)} documents!")
            
            if result.get("errors"):
                print(f"\n⚠️  Encountered {len(result['errors'])} errors:")
                for error in result["errors"][:5]:  # Show first 5 errors
                    print(f"   - {error.get('code')}: {error.get('error')}")
                if len(result["errors"]) > 5:
                    print(f"   ... and {len(result['errors']) - 5} more")
            
        except Exception as e:
            print(f"\n❌ Error during ingestion: {e}")
            raise
    
    # Verify ingestion
    async with cm.session_context() as session:
        rag_dao = RAGDocumentsDao(session)
        rag_service = RAGService(rag_dao=rag_dao)
        
        final_count = await check_existing_data(rag_service)
        print(f"\n📊 Final document count: {final_count}")
        
        # Test a sample search
        print("\n🔍 Testing semantic search...")
        test_queries = [
            "chest pain and difficulty breathing",
            "fever and cough",
            "stomach pain and nausea",
        ]
        
        for query in test_queries:
            results = await rag_service.search(query, corpus_type="icd10", top_k=3)
            codes = results.get("data", [])
            if codes:
                top_code = codes[0]
                print(f"   '{query}' → {top_code['metadata'].get('code')} "
                      f"({top_code['similarity']:.2f})")
            else:
                print(f"   '{query}' → No results")
    
    print("\n" + "=" * 60)
    print("✅ ICD-10 seeding complete!")
    print("=" * 60)


async def main(force: bool = False, check_only: bool = False):
    """Entry point with error handling."""
    try:
        await seed_icd10(force=force, check_only=check_only)
    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed ICD-10 codes into pgvector for RAG"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-seed without prompting"
    )
    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="Just check existing data and exit"
    )
    args = parser.parse_args()
    
    # Check for OpenAI API key (not needed for --check)
    if not args.check and not os.environ.get("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("   Please set it before running this script.")
        print("   Example: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    asyncio.run(main(force=args.force, check_only=args.check))

