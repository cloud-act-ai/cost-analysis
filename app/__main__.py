"""
FinOps360 Cost Analysis - Main Entry Point
Run with: python -m app
"""
import uvicorn
import os
import sys
import argparse


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="FinOps360 Cost Analysis Dashboard")
    parser.add_argument(
        "--port", type=int, default=8080, help="Port to run the server on (default: 8080)"
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--workers", type=int, default=None, 
        help="Number of worker processes (default: based on CPU count)"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    # Set default workers based on CPU count
    if args.workers is None:
        import multiprocessing
        args.workers = min(multiprocessing.cpu_count(), 4)  # Cap at 4 workers
    
    # Print information
    print(f"FinOps360 Cost Analysis Dashboard")
    print(f"----------------------------------")
    print(f"Starting server on http://{args.host}:{args.port}")
    print(f"Workers: {args.workers}")
    print(f"Auto-reload: {'Enabled' if args.reload else 'Disabled'}")
    print()
    
    # Run the server
    uvicorn.run(
        "app.core.app:app", 
        host=args.host,
        port=args.port,
        workers=1 if args.reload else args.workers,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
