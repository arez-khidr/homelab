import os
import oyaml as yaml
from datetime import datetime
from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import requests
# Using the Proxmoxer API. This script should be called and ran whenever a new vm is added.
# Automatically adds and removes VMs that have been changed

# VLAN to directory mapping
VLAN_MAPPING = {
    "10": "vlan-10-vuln",
    "20": "vlan-20-domain",
    "30": "vlan-30-containers",
    "default": "vlan-0-management",
}


def extract_network_info(config):
    """Extract networking information from VM config"""
    network_interfaces = []
    for key, value in config.items():
        if key.startswith("net"):
            interface_info = {"interface": key}

            # Parse network string (e.g., "virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,tag=100")
            parts = str(value).split(",")
            for part in parts:
                if "bridge=" in part:
                    interface_info["bridge"] = part.split("=")[1]
                elif "tag=" in part:
                    interface_info["vlan"] = part.split("=")[1]
                elif (
                    "=" in part
                    and not part.startswith("virtio")
                    and not part.startswith("e1000")
                ):
                    key_val = part.split("=")
                    if len(key_val) == 2:
                        interface_info[key_val[0]] = key_val[1]

            network_interfaces.append(interface_info)
    return network_interfaces


def extract_creation_data(config):
    """Extracts the creation date from config"""

    created_time = None
    if "meta" in config:
        meta = config["meta"]
        created_time = datetime.fromtimestamp(int(meta["creation-qemu"])).isoformat()

    return created_time


def extract_disk_info(config):
    """Extract basic disk information from VM config"""
    disks = []
    for key, value in config.items():
        if key.startswith(("scsi", "sata", "ide", "virtio")) and key != "virtio":
            disk_info = {"name": key}

            parts = str(value).split(",")
            storage_info = parts[0]

            if "file=" in storage_info:
                # Format: file=storage_name:disk_name
                file_part = storage_info.split("file=")[1]
                if ":" in file_part:
                    storage = file_part.split(":", 1)[0]
                    disk_info["storage"] = storage
            elif ":" in storage_info:
                # Format: storage_name:disk_name (LVM, ZFS, etc.)
                storage = storage_info.split(":", 1)[0]
                disk_info["storage"] = storage

            for part in parts[1:]:
                if "size=" in part:
                    disk_info["size"] = part.split("=")[1]

            disks.append(disk_info)
    return disks


def write_yaml_inventory(vm_inventory, directory):
    """Write VM inventory to YAML file"""
    if directory:
        os.makedirs(directory, exist_ok=True)
        output_file = os.path.join(directory, "vm_inventory.yaml")
    else:
        output_file = "vm_inventory.yaml"

    with open(output_file, "w") as f:
        yaml.dump(
            {"vms": vm_inventory, "generated_at": datetime.now().isoformat()},
            f,
            default_flow_style=False,
            indent=2,
            sort_keys=False,
        )

    print(f"VM inventory written to {output_file}")


def extract_vm_vlan(network_interfaces):
    """Extract VLAN tag from VM network interfaces"""
    vlan_tag = "default"  # Default VLAN
    if network_interfaces:
        for interface in network_interfaces:
            if "vlan" in interface:
                vlan_tag = interface["vlan"]
                break  # Use first VLAN found
    return vlan_tag


def generate_vlan_specific_inventory(vm_data, vlan_tag):
    """Writes the config file for a vm to a specific directory corresponding to its vlan"""
    # Map VLAN tag to directory name
    try:
        vlan_dir = VLAN_MAPPING[vlan_tag]
    except Exception as e:
        print(
            f"Issue for VLAN mapping, VLAN may need to be added to the VLAN_MAPPINNG dict{e}"
        )
        return

    # Get project root and set path to services directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    directory = os.path.join(project_root, "services", vlan_dir)

    os.makedirs(directory, exist_ok=True)

    vm_name = vm_data["name"].replace(" ", "_").replace("/", "_")
    output_file = os.path.join(directory, f"{vm_name}_config.yaml")

    with open(output_file, "w") as f:
        yaml.dump(vm_data, f, default_flow_style=False, sort_keys=False, indent=2)

    print(f"VM {vm_data['name']} written to {output_file}")


def generate_vm_inventory(proxmox: ProxmoxAPI, nodename, directory):
    """
    Gets VM information to display inventory

    Args:
        proxmox - A ProxmoxAPI Instance
        node - The name of the proxmox node that is being indexed (ex. pve)
        directory - Where the outputted YAML file should be written
    """

    try:
        vms = proxmox.cluster.resources.get(type="vm")
        if not vms:
            raise ValueError("No vms were obtained")

        vm_inventory = []

        for vm in vms:
            if vm["template"] == 1:
                continue

            vmid = vm["vmid"]
            config = proxmox.nodes(nodename).qemu(vmid).config.get()

            if not config:
                print(f"VM Config for {vmid} not obtained")
                continue
            network_interfaces = extract_network_info(config)
            disks = extract_disk_info(config)

            vm_data = {
                "vmid": vmid,
                "name": vm["name"],
                "memory_mb": config["memory"],
                "cores": config["cores"],
                "sockets": config["sockets"],
                "network_interfaces": network_interfaces,
                "disks": disks,
                "node": vm["node"],
            }

            vm_inventory.append(vm_data)

            # Generate VLAN specific file for config
            vlan_tag = extract_vm_vlan(network_interfaces)
            generate_vlan_specific_inventory(vm_data, vlan_tag)

        write_yaml_inventory(vm_inventory, directory)

    except Exception as e:
        print(f"error obtaining info {e}")


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

    # Get project root and set path to infrastructure/compute directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    compute_dir = os.path.join(project_root, "infrastructure", "compute")

    generate_vm_inventory(
        proxmox, os.getenv("PROXMOX_NODE"), compute_dir
    )


if __name__ == "__main__":
    main()
