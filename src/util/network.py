import os
import fcntl
import struct
import socket

import requests

# https://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-from-a-nic-network-interface-controller-in-python
def get_local_ip():
    ret = []
    for ifname in os.listdir("/sys/class/net"):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            ip = socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15].encode("utf-8"))
            )[20:24])
            ret.append((ip, ifname))
        except Exception as e:
            print("{}: {}".format(ifname, e))
    return ret

def get_wan_ip():
    """ Get WAN IP address. Uses http request."""
    with open(os.path.dirname(os.path.abspath(__file__)) + "/../../data/servers.txt", "r") as f:
        for server in f.read().strip().split("\n"):
            try:
                # Add timeout to prevent indefinite blocking
                # requests library will handle redirects and raise TooManyRedirects if needed
                res = requests.get(server, timeout=5)
                if res.status_code == 200:
                    return res.text.strip()
            except requests.exceptions.TooManyRedirects:
                print(f"TooManyRedirects for server: {server}, trying next...")
                continue
            except requests.exceptions.Timeout:
                print(f"Timeout for server: {server}, trying next...")
                continue
            except requests.exceptions.RequestException as e:
                print(f"Error fetching from {server}: {e}, trying next...")
                continue
    return "0.0.0.0"

if __name__ == "__main__":
    print(get_local_ip(), get_wan_ip())