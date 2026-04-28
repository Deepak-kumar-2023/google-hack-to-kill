"""
FairGuard AI — Startup Script
Generates sample data and starts the FastAPI backend server.
"""

import os
import sys
import subprocess


def main():
    root = os.path.dirname(os.path.abspath(__file__))

    # Generate sample data if missing
    data_path = os.path.join(root, "data", "sample_hiring_data.csv")
    if not os.path.exists(data_path):
        print("📊 Generating sample hiring dataset...")
        sys.path.insert(0, root)
        from backend.sample_data import generate_hiring_dataset
        generate_hiring_dataset(output_path=data_path)
        print("✅ Sample data generated!")

    print()
    print("=" * 60)
    print("  🛡️  FairGuard AI — Responsible AI Bias Detection")
    print("=" * 60)
    print()
    print("  📍 Dashboard:    http://localhost:8000")
    print("  📍 Landing Page: http://localhost:8000/landing")
    print("  📍 API Docs:     http://localhost:8000/docs")
    print()
    print("  Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    # Start uvicorn
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
