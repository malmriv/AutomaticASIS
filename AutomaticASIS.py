import os
import zipfile
import xml.etree.ElementTree as ET
import csv
import re

# Direction-aware address key mapping
ADDRESS_KEYS_BY_TYPE = {
    'HTTPS': ['urlPath'],
    'HTTP': ['httpAddressWithoutQuery'],
    'SFTP': ['host'],
    'JMS': {
        'Sender': ['QueueName_inbound'],
        'Receiver': ['QueueName_outbound']
    },
    'ProcessDirect': ['address'],
    'HCIOData': ['address'],
    'SOAP': ['address']
}

def unzip_file(zip_path, extract_base_dir):
    if not os.path.isfile(zip_path):
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    base_name = os.path.splitext(os.path.basename(zip_path))[0]
    extract_path = os.path.join(extract_base_dir, base_name + '_unzipped')

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    return extract_path

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

def load_parameters(root_dir):
    param_file = None
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file == 'parameters.prop':
                param_file = os.path.join(root, file)
                break
    params = {}
    if not param_file:
        return params

    with open(param_file, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.replace('\\ ', ' ').strip()
                params[key] = value.strip()
    return params

def extract_message_flows(iflw_path, iflow_name, parameters):
    tree = ET.parse(iflw_path)
    root = tree.getroot()
    results = []

    for elem in root.iter():
        if strip_namespace(elem.tag) == "messageFlow":
            message_data = {
                'Iflow': iflow_name,
                'ComponentType': None,
                'Direction': None,
                'Name': None,
                'TransportProtocol': None,
                'Address': None,
                'Parametrized': False
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

                    # Determine possible address keys
                    ctype = message_data['ComponentType']
                    direction = message_data['Direction']
                    if isinstance(ADDRESS_KEYS_BY_TYPE.get(ctype), dict):
                        possible_keys = ADDRESS_KEYS_BY_TYPE[ctype].get(direction, [])
                    else:
                        possible_keys = ADDRESS_KEYS_BY_TYPE.get(ctype, [])

                    # Find address
                    address = None
                    for k in possible_keys:
                        if k in properties:
                            address = properties[k]
                            break

                    # Fallback for anything containing 'url'
                    if not address:
                        for key, val in properties.items():
                            if val and 'url' in key.lower():
                                address = val
                                break

                    # Substitute one or more parameters in the address
                    def substitute_param(match):
                        param_key = match.group(1).strip()
                        if param_key in parameters:
                            message_data['Parametrized'] = True
                            return parameters[param_key]
                        else:
                            message_data['Parametrized'] = True
                            return match.group(0)  # Keep original if unresolved

                    if address:
                        address = re.sub(r'{{(.*?)}}', substitute_param, address)

                    message_data['Address'] = address

            if message_data['ComponentType']:
                results.append(message_data)

    return results

def save_to_csv(data, output_path='message_flows.csv'):
    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(
            file,
            fieldnames=['Iflow', 'ComponentType', 'Direction', 'Name', 'TransportProtocol', 'Address', 'Parametrized']
        )
        writer.writeheader()
        writer.writerows(data)

def main():
    input_dir = '.'  # Current working directory
    output_csv = 'message_flows.csv'
    all_flows = []

    zip_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.zip')]
    if not zip_files:
        print("❌ No zip files found in the directory.")
        return

    for zip_file in zip_files:
        zip_path = os.path.join(input_dir, zip_file)
        try:
            unzip_path = unzip_file(zip_path, input_dir)
            iflw_file = find_iflw_file(unzip_path)
            iflow_name = os.path.splitext(os.path.basename(iflw_file))[0]
            parameters = load_parameters(unzip_path)
            flows = extract_message_flows(iflw_file, iflow_name, parameters)
            all_flows.extend(flows)
            print(f"✅ Processed '{zip_file}' with {len(flows)} adapters.")
        except Exception as e:
            print(f"❌ Error processing '{zip_file}': {e}")

    if all_flows:
        save_to_csv(all_flows, output_csv)
        print(f"✅ Saved a total of {len(all_flows)} adapters from {len(zip_files)} zip(s) into '{output_csv}'.")
    else:
        print("❌ No adapters found to save.")

if __name__ == '__main__':
    main()
