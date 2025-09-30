import os
import traceback
import yaml
from datetime import datetime
from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import requests


def extract_disk_info(config):
    """Extract basic disk information from VM config - handles different storage types"""
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
                    size_str = part.split("=")[1]
                    if size_str.endswith("G"):
                        disk_info["size_gb"] = int(size_str[:-1])
                    elif size_str.endswith("M"):
                        disk_info["size_gb"] = round(int(size_str[:-1]) / 1024, 2)
                    else:
                        disk_info["size_gb"] = 0

            disks.append(disk_info)
    return disks


def process_vm_allocations(proxmox, nodename, storage_allocations):
    """Goes through all the vms, and generates a total of how much each VM has allocated to each storage"""
    vms = proxmox.cluster.resources.get(type="vm")
    if not vms:
        raise ValueError("No VMs were obtained")

    for vm in vms:
        if vm["template"] == 1:
            continue

        vmid = vm["vmid"]
        vm_name = vm["name"]
        config = proxmox.nodes(nodename).qemu(vmid).config.get()

        if not config:
            print(f"VM Config for {vmid} not obtained")
            continue

        disks = extract_disk_info(config)

        for disk in disks:
            if "storage" in disk and "size_gb" in disk:
                storage_name = disk["storage"]
                allocated_gb = disk["size_gb"]

                print(
                    f"Processing VM {vm_name} - Storage: {storage_name}, Size: {allocated_gb}GB"
                )

                existing_vm = None
                for vm_entry in storage_allocations[storage_name]["vms"]:
                    if vm_entry["vmid"] == vmid:
                        existing_vm = vm_entry
                        break

                if existing_vm:
                    existing_vm["allocated_gb"] += allocated_gb
                else:
                    storage_allocations[storage_name]["vms"].append(
                        {
                            "vm_name": vm_name,
                            "vmid": vmid,
                            "allocated_gb": allocated_gb,
                        }
                    )

                storage_allocations[storage_name]["allocated_to_vms_gb"] += allocated_gb


def vm_ram_allocation(proxmox: ProxmoxAPI, nodename, directory):
    """Shows the RAM allocation across all VMs"""
    try:
        vms = proxmox.cluster.resources.get(type="vm")
        if not vms:
            raise ValueError("No VMs were obtained")

        ram_allocations = {"total_allocated_gb": 0, "vms": []}

        for vm in vms:
            if vm["template"] == 1:
                continue

            vmid = vm["vmid"]
            vm_name = vm["name"]
            config = proxmox.nodes(nodename).qemu(vmid).config.get()

            if not config:
                print(f"VM Config for {vmid} not obtained")
                continue

            allocated_ram_mb = config["memory"]
            allocated_ram_gb = round(float(allocated_ram_mb) / 1024, 2)

            vm_ram_data = {
                "vm_name": vm_name,
                "vmid": vmid,
                "allocated_gb": allocated_ram_gb,
            }

            ram_allocations["vms"].append(vm_ram_data)
            ram_allocations["total_allocated_gb"] += allocated_ram_gb

        ram_allocations["total_allocated_gb"] = round(
            ram_allocations["total_allocated_gb"], 2
        )

        ram_report = {
            "generated_at": datetime.now().isoformat(),
            "node": nodename,
            "ram_allocations": ram_allocations,
        }

        os.makedirs(directory, exist_ok=True)
        output_file = os.path.join(directory, "vm_ram_allocations.yaml")

        with open(output_file, "w") as f:
            yaml.dump(
                ram_report,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
            )

        print(f"VM RAM allocation report written to {output_file}")

    except Exception as e:
        print(f"Error generating VM RAM allocation report: {e}")
        traceback.print_exc()


def vm_disk_allocation(proxmox: ProxmoxAPI, nodename, directory):
    """Shows the usage across all of the disks divided by VM"""
    try:
        storage_list = proxmox.nodes(nodename).storage.get()
        if not storage_list:
            raise ValueError("No storages found")

        storage_allocations = {}
        for storage in storage_list:
            storage_name = storage["storage"]
            total_bytes = storage["total"]
            used_bytes = storage["used"]
            avail_bytes = storage["avail"]

            storage_allocations[storage_name] = {
                "total_gb": round(total_bytes / (1024**3), 2),
                "used_gb": round(used_bytes / (1024**3), 2),
                "available_gb": round(avail_bytes / (1024**3), 2),
                "allocated_to_vms_gb": 0,
                "vms": [],
            }

        # process the allocations for eahc of the individual VMS
        process_vm_allocations(proxmox, nodename, storage_allocations)

        # Combine into one large dictionary to be written to the YAMLfile
        allocation_report = {
            "generated_at": datetime.now().isoformat(),
            "node": nodename,
            "storage_allocations": storage_allocations,
        }

        os.makedirs(directory, exist_ok=True)
        output_file = os.path.join(directory, "vm_disk_allocations.yaml")

        with open(output_file, "w") as f:
            yaml.dump(
                allocation_report,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
            )

        print(f"VM disk allocation report written to {output_file}")

    except Exception as e:
        print(f"Error generating VM disk allocation report: {e}")


def generate_disk_usage(proxmox: ProxmoxAPI, nodename, directory):
    try:
        storage_list = proxmox.nodes(nodename).storage.get()

        if not storage_list:
            raise ValueError("No storages were obtained")

        storage_report = {
            "generated_at": datetime.now().isoformat(),
            "node": nodename,
            "storage_details": [],
        }

        for storage in storage_list:
            storage_name = storage["storage"]

            total_bytes = storage["total"] if "total" in storage else 0
            used_bytes = storage["used"] if "used" in storage else 0
            avail_bytes = storage["avail"] if "avail" in storage else 0

            storage_info = {
                "name": storage_name if storage_name else "Unknown",
                "type": storage["type"] if storage["type"] else "Unknown",
                "enabled": True if storage["enabled"] == 1 else False,
                "content": storage["content"].split(",")
                if storage["content"]
                else "Unassigned",
                "total_gb": round(total_bytes / (1024**3), 2),
                "used_gb": round(used_bytes / (1024**3), 2),
                "available_gb": round(avail_bytes / (1024**3), 2),
                "usage_percent": round((used_bytes / total_bytes) * 100, 2),
            }

            storage_report["storage_details"].append(storage_info)

        os.makedirs(directory, exist_ok=True)
        output_file = os.path.join(directory, "storage_usage.yaml")

        with open(output_file, "w") as f:
            yaml.dump(
                storage_report, f, default_flow_style=False, sort_keys=False, indent=2
            )

        print(f"Storage usage report written to {output_file}")

    except Exception as e:
        print(f"Error generating disk usage report: {e}")


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

    # Get project root and set path to infrastructure/storage directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    storage_dir = os.path.join(project_root, "infrastructure", "storage")
    compute_dir = os.path.join(project_root, "infrastructure", "compute")

    generate_disk_usage(proxmox, os.getenv("PROXMOX_NODE"), storage_dir)
    vm_disk_allocation(proxmox, os.getenv("PROXMOX_NODE"), storage_dir)
    vm_ram_allocation(proxmox, os.getenv("PROXMOX_NODE"), compute_dir)


if __name__ == "__main__":
    main()
