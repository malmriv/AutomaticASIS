import os
import zipfile
import xml.etree.ElementTree as ET
import csv

# Known ComponentTypes and the property keys to extract for Address
ADDRESS_KEYS_BY_TYPE = {
    'HTTPS': ['urlPath'],
    'HTTP': ['httpAddressWithoutQuery'],
    'SFTP': ['host'],
    'JMS': ['QueueName_inbound'],
    'ProcessDirect': ['address']
}

def unzip_file(zip_dir):
    for file in os.listdir(zip_dir):
        if file.lower().endswith('.zip'):
            zip_path = os.path.join(zip_dir, file)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extract_path = os.path.join(zip_dir, 'unzipped')
                zip_ref.extractall(extract_path)
                return extract_path
    raise FileNotFoundError("No zip file found in the directory.")

def find_iflw_file(root_dir):
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.iflw'):
                return os.path.join(root, file)
    raise FileNotFoundError("No .iflw file found after unzipping.")

def strip_namespace(tag):
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

def extract_message_flows(iflw_path):
    tree = ET.parse(iflw_path)
    root = tree.getroot()
    results = []

    for elem in root.iter():
        if strip_namespace(elem.tag) == "messageFlow":
            message_data = {
                'ComponentType': None,
                'Direction': None,
                'Name': None,
                'TransportProtocol': None,
                'Address': None
            }

            for child in elem:
                if strip_namespace(child.tag) == "extensionElements":
                    properties = {}
                    for prop in child.iter():
                        if strip_namespace(prop.tag) == "property":
                            key = value = None
                            for kv in prop:
                                tag = strip_namespace(kv.tag)
                                if tag == "key":
                                    key = kv.text
                                elif tag == "value":
                                    value = kv.text
                            if key:
                                properties[key] = value

                    # Extract known fields
                    message_data['ComponentType'] = properties.get('ComponentType')
                    message_data['Direction'] = properties.get('direction')
                    message_data['Name'] = properties.get('Name')
                    message_data['TransportProtocol'] = properties.get('TransportProtocol')

                    # Extract Address based on ComponentType
                    ctype = message_data['ComponentType']
                    possible_keys = ADDRESS_KEYS_BY_TYPE.get(ctype, [])
                    for k in possible_keys:
                        if k in properties:
                            message_data['Address'] = properties[k]
                            break

                    # Safe fallback: only look for keys that look like address fields
                    if not message_data['Address']:
                        for key, val in properties.items():
                            if val and 'url' in key.lower():
                                message_data['Address'] = val
                                break

            if message_data['ComponentType']:  # Skip empty or malformed entries
                results.append(message_data)

    return results

def save_to_csv(data, output_path='extracted_channels.csv'):
    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['ComponentType', 'Direction', 'Name', 'TransportProtocol', 'Address'])
        writer.writeheader()
        writer.writerows(data)

def main():
    input_dir = '.'  # Current working directory
    try:
        unzip_path = unzip_file(input_dir)
        iflw_file = find_iflw_file(unzip_path)
        flows = extract_message_flows(iflw_file)
        save_to_csv(flows)
        print(f"✅ Extracted {len(flows)} channels. Saved to 'extracted_channels.csv'.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
