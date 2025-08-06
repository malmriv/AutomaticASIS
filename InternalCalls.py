import csv
import os

def normalize_address(address):
    if not address:
        return ''
    return address.strip().rstrip('/').lower()

def process_csv_file(file_path):
    rows = []

    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)

        # Ensure UID is the first column
        if headers[0] != "UID":
            raise ValueError("Expected first column to be 'UID'.")

        # Add new columns if not already present
        if "CallsIflow" not in headers:
            headers.append("CallsIflow")
        if "IsCalledByIflow" not in headers:
            headers.append("IsCalledByIflow")

        for row in reader:
            # Extend row if new columns not present
            while len(row) < len(headers):
                row.append("")
            rows.append(row)

    # Index helpers
    idx_uid = headers.index("UID")
    idx_type = headers.index("AdapterType")
    idx_dir = headers.index("AdapterDirection")
    idx_addr = headers.index("AdapterAddress")
    idx_calls = headers.index("CallsIflow")
    idx_called_by = headers.index("IsCalledByIflow")

    # Step 1: Build mapping of address → receiver UIDs
    receiver_map = {}
    for row in rows:
        if row[idx_type] == "ProcessDirect" and row[idx_dir] == "Receiver":
            addr = normalize_address(row[idx_addr])
            if addr:
                receiver_map[addr] = row[idx_uid]

    # Step 2: Match senders to receivers by address
    for row in rows:
        if row[idx_type] == "ProcessDirect" and row[idx_dir] == "Sender":
            addr = normalize_address(row[idx_addr])
            if addr in receiver_map:
                sender_uid = row[idx_uid]
                receiver_uid = receiver_map[addr]

                # Find receiver row and update IsCalledByIflow
                for r in rows:
                    if r[idx_uid] == receiver_uid:
                        if r[idx_called_by]:
                            r[idx_called_by] += f", {sender_uid}"
                        else:
                            r[idx_called_by] = sender_uid
                        break

                # Update sender row with CallsIflow
                if row[idx_calls]:
                    row[idx_calls] += f", {receiver_uid}"
                else:
                    row[idx_calls] = receiver_uid

    # Write back to a new CSV
    output_file = os.path.splitext(file_path)[0] + "_with_links.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"✅ Processed: {file_path} → {output_file}")

def main():
    current_dir = os.getcwd()
    for filename in os.listdir(current_dir):
        if filename.lower().endswith('.csv'):
            process_csv_file(os.path.join(current_dir, filename))

if __name__ == "__main__":
    main()
