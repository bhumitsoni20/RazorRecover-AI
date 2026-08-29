import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from data.seed.seed_runner import seed_database


def main():
    parser = argparse.ArgumentParser(description="Seed RazorRecover AI database")
    parser.add_argument("--sample-size", type=int, default=200, help="Number of synthetic transactions to generate")
    args = parser.parse_args()

    print(f"Starting seed process (sample size: {args.sample_size})...")
    asyncio.run(seed_database(sample_size=args.sample_size))
    print("Database seeding completed.")


if __name__ == "__main__":
    main()
