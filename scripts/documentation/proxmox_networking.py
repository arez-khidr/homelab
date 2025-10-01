import os
import traceback
import yaml
from datetime import datetime
from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import requests


def filter_bridge_interfaces(network_data):
    """Filter network data to only include bridge and OVSBridge types, disable this if you want to get the physical connection ports!"""
    bridge_interfaces = []

    for interface in network_data:
        if interface["type"] in ["bridge", "OVSBridge"]:
            bridge_interfaces.append(interface)

    return bridge_interfaces


def process_bridge_data(bridge_interfaces):
    """Process bridge interface data into structured format"""
    bridges_config = {}

    for bridge in bridge_interfaces:
        bridge_name = bridge["iface"]
        bridges_config[bridge_name] = {
            "name": bridge_name,
            "type": bridge["type"],
            "priority": bridge["priority"],
            "active": bool(bridge["active"]),
            "cidr": bridge["cidr"] if "cidr" in bridge else None,
            "bridge_ports": bridge["bridge_ports"] if "bridge_ports" in bridge else "",
            "comments": bridge["comments"].strip()
            if "comments" in bridge and bridge["comments"]
            else None,
            "autostart": bool(bridge["autostart"]),
            "method": bridge["method"],
            "gateway": bridge["gateway"] if "gateway" in bridge else None,
        }

    return bridges_config


def write_bridge_config_yaml(bridge_report, directory):
    """Write bridge configuration data to YAML file"""
    try:
        os.makedirs(directory, exist_ok=True)
        output_file = os.path.join(directory, "virtual_bridges.yaml")

        with open(output_file, "w") as f:
            yaml.dump(
                bridge_report,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
            )

        print(f"Virtual bridges configuration written to {output_file}")

    except Exception as e:
        print(f"Error generating virtual bridges configuration: {e}")
        traceback.print_exc()


def generate_virtual_bridge_config(proxmox: ProxmoxAPI, nodename, directory):
    """Gets the configuration of the virtual bridges on the proxmox host"""
    try:
        network_info = proxmox.nodes(nodename).network.get()
    except Exception as e:
        print(f"Error getting network information: {e}")
        traceback.print_exc()
        return

    bridge_interfaces = filter_bridge_interfaces(network_info)
    bridges_config = process_bridge_data(bridge_interfaces)

    bridge_report = {
        "generated_at": datetime.now().isoformat(),
        "proxmox_node": nodename,
        "virtual_bridges": bridges_config,
    }

    write_bridge_config_yaml(bridge_report, directory)


def main():
    load_dotenv()
    try:
        proxmox = ProxmoxAPI(
            os.getenv("PROXMOX_HOST"),
            user=os.getenv("PROXMOX_USER"),
            password=os.getenv("PROXMOX_PASSWORD"),
            verify_ssl=False,
        )
    except Exception as e:
        print(f"Error access proxmox server {e}")
        return

    # Get project root and set path to infrastructure/network directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    network_dir = os.path.join(project_root, "infrastructure", "network")

    generate_virtual_bridge_config(proxmox, os.getenv("PROXMOX_NODE"), network_dir)


if __name__ == "__main__":
    main()
