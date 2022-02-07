import socket
import requests
from threading import Thread 
import queue
import ping3
from progress.bar import FillingSquaresBar
from getmac import get_mac_address
import sys
import netifaces
from subprocess import Popen, PIPE, STDOUT
import re
import json



# GET MAC VENDOR
def get_mac_details(mac_address):
      
    url = "https://macvendors.co/api/vendorname/"
    response = requests.get(url+mac_address)
    if response.status_code != 200:
        return(mac_address)
    return response.content.decode()

# GET INFORMATIONS
def gethostname(address, q, hostnames, nb):
    host_name = ""
    host_port = ""
    host_mac = get_mac_address(ip=address)
    if (host_mac != None):
        host_vendor = get_mac_details(host_mac)
        res = ping3.ping(address, timeout=5)
        if (res != None):
            hostping = 1
            try:
                host_name = socket.gethostbyaddr(address)
            except socket.herror:
                cmd=f"dig +time=5 +tries=3 +short -x {address} @224.0.0.251 -p 5353"
                output = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
                result = re.search('b\'(.*).local.', str(output.stdout.read()))
                try:
                    host_name = result.group(1)
                except:
                    host_name = None

            # PORTS        
            host_port = None
            #print (host_port)
            ports = (80,443,22,21,25,389,5000,5001,3389,3390)
            allports = ""
            for port in ports:
                #print(port)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((str(address),port))
                if result == 0:
                    if (allports == ""):
                        allports = f"{port}"
                    else:
                        allports = f"{allports} {port}"
                    host_port = allports
        else:
            hostping = 1
        
        hostnames[address] = {"nb": nb, "online": hostping, "open_port": host_port, "mac_address": host_mac, "vendor": host_vendor, "hostname": host_name}
    else:
        hostping = 0
        host_name = None
        host_port = None
        host_mac = None
        host_vendor = None
    q.put(hostnames)    
 



# CONFIG AND ARGS

cidr = ""
arg_json = 0
if len(sys.argv) > 1:
    if (sys.argv[1] == "--json"):
        arg_json = 1
    else:
        cidr = sys.argv[1]
if (cidr == ""):
    gws=netifaces.gateways()
    gateway = gws['default'][netifaces.AF_INET][0]
    cidr = gateway.rpartition('.')[0]
if (arg_json == 0):
    print (f"\nScanning {cidr}.0/24 ...\nYour gateway : {gateway}")

total = 0
q = queue.Queue()
threads = []

hostnames = {}


for ping in range(1,255):
        address = str(cidr) + "." + str(ping)
        #print(address)
        t = Thread(target=gethostname, args=(address,q, hostnames, ping))
        threads.append(t)

for t in threads:
    t.start()

if (arg_json == 0):
    with FillingSquaresBar('Processing', max=254) as bar:        
        for t in threads:
            t.join()
            bar.next()
else:        
    for t in threads:
        t.join()

hostnames = q.get()
sorted_dict = {}
sorted_dict = sorted(hostnames.items(), key = lambda x: x[1]['nb'])
test = dict(sorted_dict)

if (arg_json == 1):
    json_result = json.dumps(test, indent = 4)
    print (json_result)
    exit()
print("")
print ("{:<15} {:<20} {:<30} {:<15}".format('IP','HOSTNAME','MAC','PORTS'))


for address, data in test.items():
    host_mac = ""
    if data.get('mac_address') != None:
        total = total+1
        if data.get('vendor') != None:
            host_mac = str(data.get('vendor'))
        else:
            host_mac = str(data.get('mac_address'))
        if data.get('online') == 1:
            #if data[2] != None:
            #    address = address + "(" + data[1] + ")"
            if data.get('open_port') !Ò= None:
                host_ports = str(data.get('open_port'))
            else:
                host_ports = ""
            if data.get('hostname') != None:
                host_name = str(data.get('hostname'))
            else:
                host_name = ""
            print("-----------------------------------------------------------------------------------")
            print("{:<15} {:<20} {:<30} {:<15}".format(address,host_name,host_mac,host_ports))
            #print(f" 🟢 {address} is Up ! {host_name} {host_mac} {host_ports}")
        else:
            print(f" 🔴 {address} is Up ! {host_mac}")
    
    
    
        

print(f"\n Total : {total}")
