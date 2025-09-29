import os
import yaml
from datetime import datetime
from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import requests
# Using the Proxmoxer API. This script should be called and ran whenever a new vm is added.
# Automatically adds and removes VMs that have been changed


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
            if ":" in storage_info:
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
        )

    print(f"VM inventory written to {output_file}")


def generate_vm_inventory(proxmox: ProxmoxAPI, nodename, directory):
    """
    Gets VM information to display inventory

    Args:
        proxmox - A ProxmoxAPI Instance
        node - The name of the proxmox node that is being indexed (ex. pve)
        directory - Where the outputted YAML file should be written
    """

    if not nodename:
        raise ValueError("Node name was not passed in")

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
            # Extract networking and disk information using helper functions
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

        # Write to YAML file
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

    generate_vm_inventory(
        proxmox, os.getenv("PROXMOX_NODE"), "../../infrastructure/compute"
    )


if __name__ == "__main__":
    main()
