# 🔍 Automatic AS-IS Iflow extractor

This Python script extracts and documents integration flow metadata from zipped SAP Integration Suite iflow files. It supports address resolution for various adapter types and automatically substitutes parameterized values (e.g., `{{c4c_address}}`) using the included `parameters.prop` file.

![Example of the script working and resulting file imported into Excel](https://github.com/malmriv/malmriv.github.io/blob/master/images/ScreenshotASIS.png?raw=true)

---

## Features

- Automatically unzips multiple `.zip` files containing iflows  
- Locates and parses the `.iflw` file  
- Extracts metadata for each message flow:  
  - component type (e.g. SOAP, HTTPS, JMS, SFTP...)
  - direction  (Sender/Receiver)
  - name  
  - transport protocol (e.g. HTTPS, SFTP...)  
  - address (e.g. https://mycrm.company.com/api/v1)
- Supports parameter resolution using `parameters.prop`  
- Flags whether a parameter was resolved (`parametrized` = true/false)  
- Supports direction-aware address keys (e.g., JMS inbound/outbound)  

---

## Usage

In Windows:
1. Place the `.zip` file(s) containing your iflow in the same directory as the Python script and the `RunExtractor.bat` batch file.
2. Run the `.bat` file.
3. The script will run and a comma-separated value (`.csv`) file will appear.

More generally, without using the `.bat` file, the script can be run normally from the console. In that case (for example, under a Linux distribution, or in a macOS computer):
1. Place the `.zip` file(s) containing your iflow in the same directory as the script.
2. Navigate to that directory in a terminal (`cd (...)/dir`)
3. Run the script with Python 3 (`python AutomaticASIS.py`).  
4. The script will unzip the package, extract message flow data, resolve parameters, and save the output to `automatic_asis.csv`.  
---

## Output

The script generates a CSV file `automatic_asis.csv` with the following columns:

## example output

| Iflow                                                             | ComponentType | Direction | Name                       | TransportProtocol | Address                                                                            | Parametrized |
|-------------------------------------------------------------------|---------------|-----------|----------------------------|-------------------|------------------------------------------------------------------------------------|--------------|
| Replicate Business Partner Relationship to SAP Customer Data Cloud | ProcessDirect | Receiver  | ProcessDirect_updateContact | Not Applicable    | /internal-dev/cdc/updateCustomer                                                   | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | SOAP          | Receiver  | SOAPC4C_confirmation       | HTTP              | https://myxxx.crm.ondemand.com/sap/bc/srt/scs/sap/businesspartnerrelationshipre1 | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | ProcessDirect | Receiver  | ProcessDirect              | Not Applicable    | /internal-dev/replicateContactToCDC                                                | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | ProcessDirect | Receiver  | ProcessDirect              | Not Applicable    | /internal-dev/createRelationCDC                                                    | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | ProcessDirect | Receiver  | ProcessDirect_after_error  | Not Applicable    | /internal-dev/createRelationCDC                                                    | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | ProcessDirect | Receiver  | ProcessDirect              | Not Applicable    | /internal-dev/setRelationCDC                                                       | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | HCIOData      | Receiver  | OData_Account              | HTTP              | https://myxxx.crm.ondemand.com/sap/c4c/odata/v1/c4codataapi                     | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | HCIOData      | Receiver  | OData_IndCustomer          | HTTP              | https://myxxx.crm.ondemand.com/sap/c4c/odata/v1/c4codataapi                     | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | HCIOData      | Receiver  | OData_Contact              | HTTP              | https://myxxx.crm.ondemand.com/sap/c4c/odata/v1/c4codataapi                     | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | ProcessDirect | Receiver  | ProcessDirect              | Not Applicable    | /internal-dev/delRelationCDC                                                       | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | JMS           | Receiver  | JMS                        | Not Applicable    | HANA_replicateDelBPRelationship_dev                                                | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | SOAP          | Sender    | SOAP                       | HTTP              | /C4C-dev/CDC/BusinessPartnerRelationshipReplicationSelfInitiatedOut                | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | JMS           | Receiver  | JMS                        | Not Applicable    | Emarsys_replicateBPRelationship_dev                                                | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | JMS           | Receiver  | JMS                        | Not Applicable    | Emarsys_replicateBPRelationship_dev                                                | True         |
| Replicate Business Partner Relationship to SAP Customer Data Cloud | HCIOData      | Receiver  | OData                      | HTTP              | https://myxxx.crm.ondemand.com/sap/c4c/odata/v1/c4codataapi/                    | True         |

---

## Parameter substitution

- Parameters are detected in the address using `{{param_name}}` syntax.  
- The script loads parameters from the `parameters.prop` file inside the unzipped folder.  
- If a parameter is found, it replaces it in the address and sets `parametrized` to true.  
- If a parameter is missing, it leaves the placeholder as is but still marks `parametrized` true.  

---

## Supported component types and address keys

The script supports common SAP CPI adapter component types with their expected address property keys:

| Component type | Direction-specific address keys                    |
|----------------|---------------------------------------------------|
| HTTPS          | urlPath                                           |
| HTTP           | httpAddressWithoutQuery                           |
| SFTP           | host                                              |
| JMS            | sender: QueueName_inbound<br>receiver: QueueName_outbound |
| ProcessDirect  | address                                           |
| HCIOData       | address                                           |
| SOAP           | address                                           |

---

## Requirements

- Python 3.x  
- Standard libraries only (`os`, `zipfile`, `xml.etree.ElementTree`, `csv`, `re`)  

---

## Author

Created by Manuel Almagro Rivas.
