# Cybersecurity Homelab

## Overview

This homelab is a Cybersecurity homelab designed to experiment with various different tools, projects and more. 
Here you can find information about my homelab configuration, specific projects, as well as other documentation, scripts and more! 

## Architecture
If you would like to replicate the physical infrastructure of the server my homelab runs on, read the following blog post on my website: [Building a Server for a Homelab](https://arezkhidr.com/2025/04/03/building-a-server-for-a-homelab/) 

## Network Topology

![Network Diagram](architecture/server_network_diagram.png)

## Directory Structure

- **`/architecture`** - Contains architecture diagrams, network topology diagrams, and high-level design documentation
- **`/infrastructure`** - Automated infrastructure documentation and configuration files
- **`/scripts`** - Automation scripts for infrastructure management and documentation generation
- **`/services`** - Individual service configurations organized by VLAN and service type
- **More to come!**

### Documentation Generation
The homelab includes automated scripts for generating infrastructure documentation:

- **VM Inventory**: Automatically catalogs all VMs with their configurations, network settings, and resource allocations
- **Storage Monitoring**: Tracks disk usage, storage allocations, and capacity planning
- **Network Documentation**: Documents pfSense configurations, VLANs, and network topology
- **Bridge Configuration**: Proxmox virtual bridge and network interface documentation
- **More to come**!

For detailed information about my self-documenting homelab approach, read: [Creating a Self-Documenting Homelab](https://arezkhidr.com/2025/10/01/creating-a-self-documenting-homelab/)

### Environment Variables
The scripts have been designed to run independently of eachother. 

The following is required for set up and running the scripts: 

- **Module Requirements** Install all of the required modules by running pip install -r requirements.txt.
- **Environment Variables** Create a .env file containing the following environment variables:
  - `PROXMOX_HOST` - IP address or hostname of your Proxmox VE server
  - `PROXMOX_USER` - Username for Proxmox API access (e.g., root@pam)
  - `PROXMOX_PASSWORD` - Password for Proxmox API authentication
  - `PROXMOX_NODE` - Name of the Proxmox node to query (e.g., pve)
  - `PFSENSE_HOST` - IP address or hostname of your pfSense firewall
  - `PFSENSE_KEY` - API key for pfSense REST API access
- **File output paths** - You may have to modify the directory path inside of each of the scripts depending on your own setup.


