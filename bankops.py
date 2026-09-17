"""Terminal demonstration of the Phase 1 banking service."""

import argparse
import json

from backend.banking.service import BankingDataError, get_transaction


def main() -> None:
    parser = argparse.ArgumentParser(description="Look up a synthetic banking transaction.")
    parser.add_argument("transaction_id", nargs="?", default="TXN001")
    args = parser.parse_args()
    try:
        transaction = get_transaction(args.transaction_id)
    except BankingDataError as error:
        parser.exit(2, f"Banking data error: {error}\n")
    if transaction is None:
        parser.exit(1, f"Transaction not found: {args.transaction_id}\n")

    print("SYNTHETIC DATA ONLY")
    print(json.dumps(transaction, indent=2))
    whole, minor = divmod(transaction["amount_minor"], 100)
    print(f"Amount: {transaction['currency']} {whole:,d}.{minor:02d}")
    if transaction["status"] == "PROCESSING":
        print("Processing status alone does not explain a delay or confirm beneficiary receipt.")


if __name__ == "__main__":
    main()
