import os
import yaml
from datetime import datetime
from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import requests


def ram_usage():
    """Shows how much RAM is being expended divided by VM"""


def usage_per_disk():
    """Shows the usage across all of the disks divided by VM"""


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

    generate_disk_usage(
        proxmox, os.getenv("PROXMOX_NODE"), "../../infrastructure/storage"
    )


if __name__ == "__main__":
    main()
