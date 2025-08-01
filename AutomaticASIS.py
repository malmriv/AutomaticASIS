import os
import zipfile
import xml.etree.ElementTree as ET
import csv
import re
import shutil

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

def read_manifest(manifest_path):
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError("MANIFEST.MF not found.")
    
    manifest_data = {'IflowID': None, 'Version': None}
    current_key = None
    current_value = ''

    with open(manifest_path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith(' '):  # Continuation of previous line
                current_value += line[1:]
            elif ':' in line:
                if current_key == 'Origin-Bundle-SymbolicName':
                    manifest_data['IflowID'] = current_value
                elif current_key == 'Bundle-Version':
                    manifest_data['Version'] = current_value
                current_key, current_value = line.split(':', 1)
                current_key = current_key.strip()
                current_value = current_value.strip()
        # Final line
        if current_key == 'Origin-Bundle-SymbolicName':
            manifest_data['IflowID'] = current_value
        elif current_key == 'Bundle-Version':
            manifest_data['Version'] = current_value

    return manifest_data

def extract_message_flows(iflw_path, iflow_name, parameters, manifest_info):
    tree = ET.parse(iflw_path)
    root = tree.getroot()
    results = []

    for elem in root.iter():
        if strip_namespace(elem.tag) == "messageFlow":
            message_data = {
                'Iflow': iflow_name,
                'IflowID': manifest_info.get('IflowID'),
                'Version': manifest_info.get('Version'),
                'ComponentType': None,
                'TransportProtocol': None,
                'Direction': None,
                'AdapterName': None,
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

                    message_data['ComponentType'] = properties.get('ComponentType')
                    message_data['Direction'] = properties.get('direction')
                    message_data['AdapterName'] = properties.get('Name')
                    message_data['TransportProtocol'] = properties.get('TransportProtocol')

                    ctype = message_data['ComponentType']
                    direction = message_data['Direction']
                    if isinstance(ADDRESS_KEYS_BY_TYPE.get(ctype), dict):
                        possible_keys = ADDRESS_KEYS_BY_TYPE[ctype].get(direction, [])
                    else:
                        possible_keys = ADDRESS_KEYS_BY_TYPE.get(ctype, [])

                    address = None
                    for k in possible_keys:
                        if k in properties:
                            address = properties[k]
                            break

                    if not address:
                        for key, val in properties.items():
                            if val and 'url' in key.lower():
                                address = val
                                break

                    def substitute_param(match):
                        param_key = match.group(1).strip()
                        if param_key in parameters:
                            message_data['Parametrized'] = True
                            return parameters[param_key]
                        else:
                            message_data['Parametrized'] = True
                            return match.group(0)

                    if address:
                        address = re.sub(r'{{(.*?)}}', substitute_param, address)

                    message_data['Address'] = address

            if message_data['ComponentType']:
                results.append(message_data)

    return results

def save_to_csv(data, output_path='automatic_asis.csv'):
    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(
            file,
            fieldnames=['Iflow', 'IflowID', 'Version', 'ComponentType', 'TransportProtocol', 'Direction', 'AdapterName', 'Address', 'Parametrized']
        )
        writer.writeheader()
        writer.writerows(data)

def main():
    input_dir = '.'
    temp_dir = os.path.join(input_dir, 'temp')
    output_csv = 'automatic_asis.csv'
    all_flows = []

    os.makedirs(temp_dir, exist_ok=True)
    zip_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.zip')]

    if not zip_files:
        print("❌ No zip files found in the directory.")
        return

    try:
        for zip_file in zip_files:
            zip_path = os.path.join(input_dir, zip_file)
            try:
                unzip_path = unzip_file(zip_path, temp_dir)
                iflw_file = find_iflw_file(unzip_path)
                iflow_name = os.path.splitext(os.path.basename(iflw_file))[0]
                parameters = load_parameters(unzip_path)
                manifest_path = os.path.join(unzip_path, 'META-INF', 'MANIFEST.MF')
                manifest_info = read_manifest(manifest_path)
                flows = extract_message_flows(iflw_file, iflow_name, parameters, manifest_info)
                all_flows.extend(flows)
                print(f"✅ Processed '{zip_file}' with {len(flows)} adapters.")
            except Exception as e:
                print(f"❌ Error processing '{zip_file}': {e}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print("🧹 Temporary files cleaned up.")

    if all_flows:
        save_to_csv(all_flows, output_csv)
        print(f"✅ Saved a total of {len(all_flows)} adapters from {len(zip_files)} zip(s) into '{output_csv}'.")
    else:
        print("❌ No adapters found to save.")

if __name__ == '__main__':
    main()
