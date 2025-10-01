# Uses the pfsense API to get information from the firewall

import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
import yaml
import traceback
from datetime import datetime


class PfSenseAPI:
    def __init__(self, host, api_key) -> None:
        self.host = host
        self.base_url = f"https://{host}/api/v2"
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": api_key})
        # I have this set to false due to certificate issues
        # If to be used in production this line should be removed
        self.session.verify = False


def process_interfaces_data(interfaces_data):
    """Process interface data from API response"""
    interfaces_info = {}

    for interface in interfaces_data["data"]:
        interface_id = interface["id"]
        interfaces_info[interface_id] = {
            "id": interface_id,
            "description": interface["descr"],
            "ipv4_address": interface["ipaddr"],
            "subnet": interface["subnet"],
            "physical_interface": interface["if"],
            "enabled": interface["enable"],
            "ipv4_type": interface["typev4"],
            "gateway": interface["gateway"],
            "block_private_networks": interface["blockpriv"],
            "block_bogon_networks": interface["blockbogons"],
        }

    return interfaces_info


def process_dhcp_data(dhcp_data):
    """Process DHCP data from API response"""
    dhcp_info = {}

    for dhcp_config in dhcp_data["data"]:
        interface_id = dhcp_config["id"]
        dhcp_info[interface_id] = {
            "enabled": dhcp_config["enable"],
            "range_from": dhcp_config["range_from"],
            "range_to": dhcp_config["range_to"],
            "dns_servers": dhcp_config["dnsserver"],
            "gateway": dhcp_config["gateway"],
            "domain": dhcp_config["domain"],
            "default_lease_time": dhcp_config["defaultleasetime"],
            "max_lease_time": dhcp_config["maxleasetime"],
            "static_arp": dhcp_config["staticarp"],
            "deny_unknown": dhcp_config["denyunknown"],
        }

    return dhcp_info


def write_network_config_yaml(network_report, directory):
    """Write network configuration data to YAML file"""
    try:
        os.makedirs(directory, exist_ok=True)
        output_file = os.path.join(directory, "network_config.yaml")

        with open(output_file, "w") as f:
            yaml.dump(
                network_report,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
            )

        print(f"Network configuration written to {output_file}")

    except Exception as e:
        print(f"Error generating network configuration: {e}")
        traceback.print_exc()


def generate_interfaces_config(pfsense: PfSenseAPI, directory):
    """Generates a YAML file describing the configuration of all interfaces on the pfsense router"""

    interfaces_request_url = pfsense.base_url + "/interfaces/"
    address_pool_request_url = pfsense.base_url + "/services/dhcp_servers/"

    try:
        interfaces_response = pfsense.session.get(interfaces_request_url)
        interfaces_response.raise_for_status()

        address_pool_response = pfsense.session.get(address_pool_request_url)
        address_pool_response.raise_for_status()
    except Exception as e:
        print(f"Error making API requests: {e}")
        traceback.print_exc()
        return

    interfaces_data = interfaces_response.json()
    dhcp_data = address_pool_response.json()

    interfaces_info = process_interfaces_data(interfaces_data)
    dhcp_info = process_dhcp_data(dhcp_data)

    network_config = {}
    for interface_id in interfaces_info:
        network_config[interface_id] = {
            "interface_info": interfaces_info[interface_id],
            "dhcp_config": dhcp_info.get(
                interface_id,
                {
                    "enabled": False,
                    "range_from": None,
                    "range_to": None,
                    "dns_servers": [],
                    "gateway": None,
                },
            ),
        }

    network_report = {
        "generated_at": datetime.now().isoformat(),
        "pfsense_host": pfsense.host,
        "network_configuration": network_config,
    }

    write_network_config_yaml(network_report, directory)


def main():
    input("Is tailscale running and connected? Press any key to continue...")

    load_dotenv()
    try:
        pfsense = PfSenseAPI(os.getenv("PFSENSE_HOST"), os.getenv("PFSENSE_KEY"))
    except Exception as e:
        print(f"Error connecting to pfSense: {e}")
        return

    # Get project root and set path to infrastructure/network directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    network_dir = os.path.join(project_root, "infrastructure", "network")

    generate_interfaces_config(pfsense, network_dir)


if __name__ == "__main__":
    main()
