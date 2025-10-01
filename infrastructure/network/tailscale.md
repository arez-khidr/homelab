# Tailscale  

The pfsense instance inside of this Proxmox machine does run tailscale. This is in order to be able to connect the internal homelab network with my macbook externally for documentation and other scripting reasons. 

A few notes on the configuration of tailscale for this purpose:

- The 10.10.1.0/24 subnet is to be broadcasted from tailscale. Make sure this is accepted on the tailscale admin panel. This makes it such that we can access the pfsense admin page as if we were on the 10.10.1.0/24 subnet, by going to the http://10.10.1.254 url. 
- For requesting with the pfsense API, as of the time of writing (October 1, 2025) calling with curl requires the -L flag to handle redirects. Or be sure to call any endpoint with a "/" at the end. This is not needed for the python requests library as redirects are handled automatically. 


