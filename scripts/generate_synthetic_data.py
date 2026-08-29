import argparse
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.synthetic.dataset_generator import SyntheticDataGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic transaction dataset")
    parser.add_argument("--count", type=int, default=10000, help="Number of synthetic transactions")
    parser.add_argument("--output", type=str, default="data/processed/synthetic_transactions.json", help="Output JSON path")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    print(f"Generating {args.count} synthetic transactions...")
    txns = SyntheticDataGenerator.generate_transactions(count=args.count)

    # Convert datetime to isoformat
    serialized = []
    for t in txns:
        item = dict(t)
        if hasattr(item["created_at"], "isoformat"):
            item["created_at"] = item["created_at"].isoformat()
        serialized.append(item)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(serialized, f, indent=2)

    print(f"Dataset generated successfully at {args.output} ({len(serialized)} records).")


if __name__ == "__main__":
    main()
