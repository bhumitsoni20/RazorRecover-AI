import sqlite3

def clean():
    conn = sqlite3.connect("razorrecover.db")
    cur = conn.cursor()
    cur.execute(
        "UPDATE recovery_actions SET external_reference = NULL WHERE transaction_id != 'txn_high_value' AND external_reference = 'https://rzp.io/rzp/nSoef4uz'"
    )
    conn.commit()
    print("Updated rows:", cur.rowcount)
    conn.close()

if __name__ == "__main__":
    clean()
