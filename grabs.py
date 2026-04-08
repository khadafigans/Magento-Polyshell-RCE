## AS USUAL THE GRABBER

import shodan
import threading
import queue
import os
import re
import time
import socket
import random
import sys
import datetime
from colorama import init, Fore, Style

try:
    import socks
except ImportError:
    socks = None

SHODAN_API_KEY = "SHODAN_API_KEY"  # <-- Put your Shodan API key here

init(autoreset=True)
LIME = Fore.LIGHTGREEN_EX

banner = f"""{LIME}{Style.BRIGHT}
╔════════════════════════════════════════════════════════╗
║                                                        ║
║            Magento Grabber By Bob Marley               ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
{Style.RESET_ALL}"""
print(banner)

proxy_list = []
proxy_lock = threading.Lock()

def is_ip(address):
    return re.match(r"^\d{1,3}(\.\d{1,3}){3}$", address) is not None

def is_staging_or_cloud_domain(hostname):
    """Filter out staging, development, and cloud hosting domains"""
    if not hostname:
        return True
    
    hostname_lower = hostname.lower()
    
    # Cloud hosting and server providers (COMPLETE BLOCK - DO NOT SAVE)
    cloud_providers = [
        # AWS
        'amazonaws.com',
        'cloudfront.net',
        'elasticbeanstalk.com',
        'aws.amazon.com',
        'awsglobalaccelerator.com',
        'amplifyapp.com',
        'execute-api.amazonaws.com',
        'lambda-url.amazonaws.com',
        'cloudfront-dns.com',
        'awsapps.com',
        'awsstatic.com',
        's3.amazonaws.com',
        'compute.amazonaws.com',
        'elb.amazonaws.com',
        'rds.amazonaws.com',
        
        # Azure
        'azurewebsites.net',
        'azure.com',
        'cloudapp.net',
        'cloudapp.azure.com',
        'azurefd.net',
        'azureedge.net',
        'trafficmanager.net',
        'blob.core.windows.net',
        
        # Google Cloud
        'googleusercontent.com',
        'appspot.com',
        'cloudfunctions.net',
        'web.app',
        'firebaseapp.com',
        
        # Popular hosting providers
        'herokuapp.com',
        'herokussl.com',
        'digitaloceanspaces.com',
        'vercel.app',
        'netlify.app',
        'pages.dev',
        'railway.app',
        'fly.dev',
        'render.com',
        'onrender.com',
        'repl.co',
        'glitch.me',
        'surge.sh',
        'now.sh',
        
        # CDN providers
        'cloudflare.com',
        'cloudflare.net',
        'fastly.net',
        'akamai.net',
        'akamaiedge.net',
        'akamaihd.net',
        'edgecastcdn.net',
        'netdna-cdn.com',
        'netdna-ssl.com',
        'cdn77.org',
        'stackpathdns.com',
        'cloudinary.com',
        'imgix.net',
        
        # Server/VPS/Hosting providers from user's list + common European providers
        'your-server.de',
        'hypernode.io',
        'linodeusercontent.com',
        'linode.com',
        'vultrusercontent.com',
        'vultr.com',
        'secureserver.net',
        'contaboserver.net',
        'upcloud.host',
        'onlinehome-server.info',
        'ovh.net',
        'ovh.ca',
        'ovh.com',
        'ovh.us',
        'ovh.ie',
        'ovh.es',
        'ovh.de',
        'ovhcloud.com',
        'combell.com',
        'combell.net',
        'maxcluster.net',
        'name-servers.gr',
        'vshosting.cz',
        'nucleus.be',
        'aspirationcloud.com',
        'hosty.lt',
        'happysrv.de',
        'pbiaas.com',
        'dvpne.com',
        'bitcoinwebhosting.net',
        'phdns10.es',
        'agk-group.gr',
        't-ipconnect.de',
        'exetel.com.au',
        'jetrails.io',
        'dedipower.net',
        'ukfast.net',
        'myfcloud.com',
        'akoova.cloud',
        'konekti.xyz',
        'ha.rs',
        'bio-based.eu',
        'pop.de',
        'magentohotel.dk',
        'your-printq.com',
        'svijetvode.com',
        'semat.be',
        'antratek.com',
        'logops.xyz',
        'zen.co.uk',
        'stone-is.net',
        'ebyserver.co.uk',
        'dodlabs.com',
        'stok.ly',
        'devbox.site',
        '2play.com',
        
        # Additional common hosting providers
        'webhosting.com',
        'hostinger.com',
        'bluehost.com',
        'godaddy.com',
        'namecheap.com',
        'siteground.com',
        'hostgator.com',
        'dreamhost.com',
        'ionos.com',
        '1and1.com',
        'hosteurope.de',
        'strato.de',
        'hetzner.com',
        'hetzner.de',
        'transip.nl',
        'transip.eu',
        'aruba.it',
        'ovh.it',
        'infomaniak.com',
        'server4you.de',
        'server4you.net',
        'mittwald.de',
        'scaleway.com',
        'digitalocean.com',
        'rackspace.com',
        'cloudways.com',
        'wpengine.com',
        'kinsta.com',
        'pantheon.io',
        'acquia.com',
        'platform.sh',
    ]
    
    # Check if hostname ends with any cloud provider domain
    for provider in cloud_providers:
        if hostname_lower.endswith(provider):
            return True
    
    # Check if hostname contains cloud/hosting provider anywhere
    # (e.g., static.45.167.217.95.clients.your-server.de)
    for provider in cloud_providers:
        if provider in hostname_lower:
            return True
    
    # Filter out IP-based hostnames (e.g., ip-94-23-90.eu, ip-51-195-133.eu)
    if hostname_lower.startswith('ip-') and '-' in hostname_lower:
        return True
    
    # Filter out server/client subdomains
    server_patterns = [
        '.clients.',
        '.server.',
        '.srv.',
        '.host.',
        '.vps.',
        '.dedicated.',
        'static.',
        'dyn.',
        'dynamic.',
        '.cloud.',
        '.compute.',
    ]
    
    for pattern in server_patterns:
        if pattern in hostname_lower:
            return True
    
    # Filter domains with hosting keywords in the domain name
    hosting_keywords = [
        'cloud',
        'server',
        'host',
        'vps',
        'dedicated',
        'webhosting',
        'hosting',
        'jetrails',
        'hypernode',
        'devbox',
        'cloudlab',
        'fcloud',
        '-demo',
        'testsite',
    ]
    
    # Extract just the domain name (before TLD)
    parts = hostname_lower.split('.')
    if len(parts) >= 2:
        domain_name = parts[-2]  # Get the part before TLD
        for keyword in hosting_keywords:
            if keyword in domain_name:
                return True
    
    # Staging/dev/test subdomains
    staging_keywords = [
        'staging.',
        'stage.',
        'stg.',
        'dev.',
        'development.',
        'test.',
        'testing.',
        'qa.',
        'uat.',
        'demo.',
        'sandbox.',
        'temp.',
        'temporary.',
        'preview.',
        'preprod.',
        'pre-prod.',
        'beta.',
        'alpha.',
        'canary.',
        'internal.',
        'local.',
        'localhost',
    ]
    
    # Check if hostname starts with staging keywords
    for keyword in staging_keywords:
        if hostname_lower.startswith(keyword):
            return True
    
    # Check for staging keywords in subdomain
    parts = hostname_lower.split('.')
    if len(parts) > 2:  # Has subdomain
        subdomain = parts[0]
        for keyword in ['staging', 'stage', 'stg', 'dev', 'development', 'test', 'testing', 'qa', 'uat', 'demo', 'sandbox', 'temp', 'preview', 'preprod', 'beta', 'alpha', 'canary']:
            if keyword in subdomain:
                return True
    
    return False

def is_valid_root_domain(domain):
    """Check if domain is a valid root domain (not just TLD combinations)"""
    if not domain:
        return False
    
    domain_lower = domain.lower()
    
    # Block TLD-only domains (e.g., eu.com, com.ua, co.in, ne.jp)
    invalid_tld_combos = [
        'eu.com', 'com.ua', 'co.in', 'ne.jp', 'net.vn', 'com.my',
        'co.eu', 'net.ua', 'org.ua', 'com.vn', 'co.jp', 'or.jp',
        'ac.jp', 'go.jp', 'com.cn', 'net.cn', 'org.cn', 'gov.cn',
        'co.kr', 'ne.kr', 'or.kr', 'com.tw', 'net.tw', 'org.tw',
        'com.sg', 'net.sg', 'org.sg', 'com.hk', 'net.hk', 'org.hk',
        'iq.pl', 'nrf.eu', 'as30961.net', 'eu.org', 'us.com',
        'rkd.nl', 'nka.pt', 'hous.it', 'corab.eu',
    ]
    
    if domain_lower in invalid_tld_combos:
        return False
    
    # Extract domain name and TLD
    parts = domain.split('.')
    if len(parts) < 2:
        return False
    
    domain_name = parts[0]
    
    # Domain name should be at least 3 chars for most valid domains
    # (exceptions for very well-known 2-char brands are rare)
    if len(domain_name) < 3:
        return False
    
    # Domain name should not be just numbers
    if domain_name.isdigit():
        return False
    
    # Block domains that start with numbers followed by few chars (e.g., 2play.com)
    if domain_name[0].isdigit() and len(domain_name) <= 5:
        return False
    
    return True

def extract_root_domain(hostname):
    """
    Extract root domain from subdomain (e.g., shop.example.com -> example.com)
    Returns None if it's a hosting provider domain or invalid TLD combo
    """
    if not hostname:
        return None
    
    # First check if this is a hosting provider domain - BLOCK IT
    if is_staging_or_cloud_domain(hostname):
        return None
    
    parts = hostname.split('.')
    
    # Handle special TLDs (co.uk, com.au, etc.)
    special_tlds = [
        'co.uk', 'co.jp', 'co.kr', 'co.id', 'co.th', 'co.nz', 'co.za',
        'com.au', 'com.br', 'com.cn', 'com.mx', 'com.ar', 'com.sg',
        'net.au', 'org.uk', 'gov.uk', 'ac.uk', 'edu.au', 'net.cn',
        'org.cn', 'gov.cn', 'edu.cn', 'ac.cn'
    ]
    
    # Check for special TLDs
    if len(parts) >= 3:
        potential_tld = '.'.join(parts[-2:])
        if potential_tld in special_tlds:
            # Return domain.special_tld (e.g., example.co.uk)
            if len(parts) >= 3:
                root = '.'.join(parts[-3:])
                # Double-check root is not a hosting provider and is valid
                if is_staging_or_cloud_domain(root) or not is_valid_root_domain(root):
                    return None
                return root
    
    # Standard TLD (e.g., .com, .net, .org)
    if len(parts) >= 2:
        root = '.'.join(parts[-2:])
        # Double-check root is not a hosting provider and is valid
        if is_staging_or_cloud_domain(root) or not is_valid_root_domain(root):
            return None
        return root
    
    return None

MAGENTO_QUERIES = [
    '"Magento" port:80',
    '"Magento" port:443',
    '"Magento/2" port:80',
    '"Magento/2" port:443',
    'http.html:"Magento"',
    'http.html:"Magento/2"',
    'http.html:"mage/cookies.js"',
    'http.html:"skin/frontend/default"',
    'http.html:"Mage.Cookies"',
    'http.component:"Magento"',
    'http.title:"Magento"',
    '"X-Magento-Cache-Control"',
    'http.header:"X-Magento-Cache-Control"',
    'http.header:"X-Magento-Tags"',
    'http.html:"/static/version"',
    'http.html:"require.js"',
    'http.html:"js/mage/"',
    'http.html:"static/_requirejs"',
    'http.html:"Magento_"',
    'http.html:"vendor/magento"',
    '"Magento Commerce"',
    '"Adobe Commerce"',
    'http.html:"checkout/cart"',
    'http.html:"customer/account"',
    'http.html:"catalogsearch/result"',
    'http.html:"/pub/static/"',
    'http.html:"/pub/media/"',
    'http.html:"var/view_preprocessed"',
    '"Magento" "RequireJS"',
    'http.html:"Magento_Ui/js"',
    'http.html:"Magento_Theme"',
    'http.html:"adminhtml"',
    '"Magento/2.4"',
    '"Magento/2.3"',
    '"Magento/2.2"',
    'http.html:"mage/requirejs/mixins"',
    'http.html:"mage/requirejs/text"',
    '"Magento" "php"',
    'http.html:"/customer/address_file/upload"',
    '"Magento" port:8080',
    '"Magento" port:8443'
]

def get_random_proxy():
    with proxy_lock:
        if not proxy_list:
            return None
        proxy = random.choice(proxy_list)
        if not proxy.startswith("socks5://") and not proxy.startswith("http://") and not proxy.startswith("https://"):
            proxy = "socks5://" + proxy
        return proxy

def remove_bad_proxy(bad_proxy):
    with proxy_lock:
        for i, proxy in enumerate(proxy_list):
            if proxy == bad_proxy or (not proxy.startswith("socks5://") and "socks5://" + proxy == bad_proxy):
                del proxy_list[i]
                break

def setup_proxy_for_request(proxy_url):
    os.environ['HTTP_PROXY'] = proxy_url
    os.environ['HTTPS_PROXY'] = proxy_url
    os.environ['SHODAN_PROXY'] = proxy_url

def ask_proxy():
    global proxy_list
    use_proxy = input(f"{Fore.YELLOW}With Proxy or No Proxy (1=Yes, 2=No): {Style.RESET_ALL}").strip()
    if use_proxy == "1":
        if not socks:
            print(f"{Fore.RED}PySocks is required for proxy support. Install with: pip install pysocks requests[socks]{Style.RESET_ALL}")
            sys.exit(1)
        proxy_file = input(f"{Fore.YELLOW}Enter the path to your Proxy List (e.g, proxy.txt): {Style.RESET_ALL}").strip()
        try:
            with open(proxy_file, "r") as f:
                proxy_list = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"{Fore.RED}Failed to read proxy list: {e}{Style.RESET_ALL}")
            sys.exit(1)
        if not proxy_list:
            print(f"{Fore.RED}Proxy list is empty!{Style.RESET_ALL}")
            sys.exit(1)
        print(f"{Fore.LIGHTGREEN_EX}Proxy list loaded with {len(proxy_list)} proxies.{Style.RESET_ALL}")
    else:
        print(f"{Fore.LIGHTGREEN_EX}Proxy not used.{Style.RESET_ALL}")

def generate_date_ranges(start_date, end_date, delta_days=30):
    ranges = []
    current_start = start_date
    while current_start < end_date:
        current_end = current_start + datetime.timedelta(days=delta_days)
        if current_end > end_date:
            current_end = end_date
        ranges.append((current_start.strftime("%Y-%m-%d"), current_end.strftime("%Y-%m-%d")))
        current_start = current_end + datetime.timedelta(days=1)
    return ranges

def shodan_search_worker(api_key, query, page_queue, result_set, lock, total, progress, host_output_path, ip_output_path):
    while True:
        try:
            page = page_queue.get_nowait()
        except queue.Empty:
            break
        attempt = 0
        while attempt < 10:
            proxy_url = get_random_proxy()
            if proxy_url:
                setup_proxy_for_request(proxy_url)
            api = shodan.Shodan(api_key)
            try:
                results = api.search(query, page=page)
                with lock:
                    matches = results.get('matches', [])
                    print(f"\n{Fore.MAGENTA}Fetched page {page} with {len(matches)} matches for query: {query}{Style.RESET_ALL}")
                    for match in matches:
                        hostnames = match.get('hostnames', [])
                        ip = match.get('ip_str', None)
                        if hostnames:
                            for hostname in hostnames:
                                if not is_ip(hostname):
                                    # Extract root domain (filters staging/cloud inside)
                                    root_domain = extract_root_domain(hostname)
                                    
                                    if not root_domain:
                                        # Filtered out - hosting/staging/cloud domain
                                        print(f"{Fore.RED}✗ BLOCKED: {hostname}{Style.RESET_ALL}")
                                        continue
                                    
                                    if root_domain not in result_set:
                                        result_set.add(root_domain)
                                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        if hostname != root_domain:
                                            print(f"{Fore.GREEN}✓ SAVED: {root_domain} (from {hostname}){Style.RESET_ALL}")
                                        else:
                                            print(f"{Fore.GREEN}✓ SAVED: {root_domain}{Style.RESET_ALL}")
                                        with open(host_output_path, "a", encoding='utf-8') as f:
                                            f.write(root_domain + "\n")
                                    else:
                                        print(f"{Fore.CYAN}• DUPLICATE: {root_domain} (already saved){Style.RESET_ALL}")
                        elif ip and ip not in result_set:
                            result_set.add(ip)
                            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            print(f"{Fore.GREEN}✓ SAVED IP: {ip}{Style.RESET_ALL}")
                            with open(ip_output_path, "a", encoding='utf-8') as f:
                                f.write(ip + "\n")
                    progress[0] = len(result_set)
                    percent = int((progress[0] / total) * 100)
                    bar = ('#' * (percent // 2)).ljust(50)
                    print(f"\r{Fore.CYAN}Progress: [{bar}] {percent}% ({progress[0]}/{total}){Style.RESET_ALL}", end="")
                break
            except Exception as e:
                attempt += 1
                time.sleep(2)
        page_queue.task_done()
        time.sleep(1)

def grab_domains():
    import math

    while True:
        try:
            total_num = int(input(f"{Fore.YELLOW}Enter the total number of sites to grab (10-1000000): {Style.RESET_ALL}"))
            if 10 <= total_num <= 1000000:
                break
            else:
                print(f"{Fore.RED}Please enter a number between 10 and 1,000,000.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")

    extra_filter = input(f"{Fore.YELLOW}Enter any extra filters (e.g., hostname:.id) or press Enter to skip: {Style.RESET_ALL}").strip()

    # Define date range for splitting queries (last 3 years)
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365*3)  # 3 years ago

    date_ranges = generate_date_ranges(start_date, end_date, delta_days=30)  # monthly ranges

    country_input = input(f"{Fore.YELLOW}Enter country codes separated by commas (e.g., US,JP,DE) or press Enter to skip: {Style.RESET_ALL}").strip()
    country_list = [c.strip().upper() for c in country_input.split(",") if c.strip()] if country_input else []

    print(f"{Fore.YELLOW}Shodan API allows 1 request per second. Thread count set to 1 for compliance.{Style.RESET_ALL}")
    num_threads = 1

    MAX_PAGES = 100  # max pages per query (1000 results)

    # If no countries are specified, treat it as a global search (no country filter)
    if not country_list:
        country_list = [None]
        per_country_quota = total_num
    else:
        # Split the quota among countries
        per_country_quota = total_num // len(country_list)
        remainder = total_num % len(country_list)

    try:
        for idx, country in enumerate(country_list):
            this_country_quota = per_country_quota + (1 if idx < remainder else 0) if country_list != [None] else per_country_quota
            if this_country_quota == 0:
                continue

            print(f"{Fore.LIGHTGREEN_EX}Starting search for Magento/Magento 2.x sites in {country if country else 'ALL'} (quota: {this_country_quota})...{Style.RESET_ALL}")

            result_dir = f"ResultGrab/{country if country else 'ALL'}"
            os.makedirs(result_dir, exist_ok=True)
            now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            host_output_path = os.path.join(result_dir, f"ResultHost_{now_str}.txt")
            ip_output_path = os.path.join(result_dir, f"ResultIP_{now_str}.txt")


            open(host_output_path, "w").close()
            open(ip_output_path, "w").close()

            result_set = set()
            lock = threading.Lock()
            progress = [0]

            for date_start, date_end in date_ranges:
                if len(result_set) >= this_country_quota:
                    break

                for query_base in MAGENTO_QUERIES:
                    if len(result_set) >= this_country_quota:
                        break

                    query = query_base
                    if country:
                        query += f' country:{country}'
                    if extra_filter:
                        query += f' {extra_filter}'

                    pages_needed = min(math.ceil((this_country_quota - len(result_set)) / 100), MAX_PAGES)
                    page_numbers = list(range(1, pages_needed + 1))

                    print(f"{Fore.CYAN}DEBUG: Query: {query}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}DEBUG: Pages to query: {page_numbers}{Style.RESET_ALL}")

                    page_queue = queue.Queue()
                    for p in page_numbers:
                        page_queue.put(p)

                    threads = []
                    for _ in range(num_threads):
                        t = threading.Thread(
                            target=shodan_search_worker,
                            args=(
                                SHODAN_API_KEY, query, page_queue, result_set, lock,
                                this_country_quota, progress, host_output_path, ip_output_path
                            )
                        )
                        t.start()
                        threads.append(t)

                    for t in threads:
                        t.join()

                    if len(result_set) >= this_country_quota:
                        break

            print(f"\n{Fore.LIGHTGREEN_EX}Search complete for {country if country else 'ALL'}. Total results collected: {len(result_set)}{Style.RESET_ALL}")
            print(f"{Fore.LIGHTGREEN_EX}Saved hostnames to {host_output_path}{Style.RESET_ALL}")
            print(f"{Fore.LIGHTGREEN_EX}Saved IPs to {ip_output_path}{Style.RESET_ALL}")

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user! Exiting...{Style.RESET_ALL}")
        sys.exit(0)

def domain_to_ip():
    filename = input(f"{Fore.YELLOW}Enter the filename containing domains (one per line): {Style.RESET_ALL}").strip()
    result_dir = "ResultDomainToIP"
    os.makedirs(result_dir, exist_ok=True)
    now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    output_file = os.path.join(result_dir, f"DomainToIP_{now_str}.txt")

    if not os.path.isfile(filename):
        print(f"{Fore.RED}File not found: {filename}{Style.RESET_ALL}")
        return
    with open(filename, "r") as f, open(output_file, "w") as out:
        for line in f:
            domain = line.strip()
            if not domain:
                continue
            try:
                ip = socket.gethostbyname(domain)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{Fore.GREEN}{domain} -> {ip}{Style.RESET_ALL}")
                out.write(f"{ip}\n")
            except Exception as e:
                print(f"{Fore.RED}Failed to resolve {domain}: {e}{Style.RESET_ALL}")
    print(f"{Fore.LIGHTGREEN_EX}Results saved to {output_file}{Style.RESET_ALL}")

def reverse_ip_to_domain():
    filename = input(f"{Fore.YELLOW}Enter the filename containing IPs (one per line): {Style.RESET_ALL}").strip()
    result_dir = "ResultReverse"
    os.makedirs(result_dir, exist_ok=True)
    now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    output_file = os.path.join(result_dir, f"Resultreverse_{now_str}.txt")
    api = shodan.Shodan(SHODAN_API_KEY)
    if not os.path.isfile(filename):
        print(f"{Fore.RED}File not found: {filename}{Style.RESET_ALL}")
        return
    with open(filename, "r") as f, open(output_file, "w") as out:
        for line in f:
            ip = line.strip()
            if not ip:
                continue
            try:
                host_info = api.host(ip)
                hostnames = set(host_info.get("hostnames", []))
                domains = set(host_info.get("domains", []))
                all_domains = hostnames | domains
                if all_domains:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{Fore.GREEN}{ip} -> {len(all_domains)} domains/hostnames found{Style.RESET_ALL}")
                    for d in all_domains:
                        out.write(f"{d}\n")
                else:
                    print(f"{Fore.YELLOW}{ip} -> No domains/hostnames found{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Shodan error for {ip}: {e}{Style.RESET_ALL}")
    print(f"{Fore.LIGHTGREEN_EX}Results saved to {output_file}{Style.RESET_ALL}")

def main():
    ask_proxy()
    while True:
        print(f"{Fore.YELLOW}Choose between (1-3){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1. Grab Domain/Hostname{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}2. Reverse IP to Domain{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}3. Domain to IP{Style.RESET_ALL}")
        choice = input(f"{Fore.YELLOW}{Style.BRIGHT}Enter your choice (1, 2, or 3): {Style.RESET_ALL}")
        if choice == "1":
            grab_domains()
        elif choice == "2":
            reverse_ip_to_domain()
        elif choice == "3":
            domain_to_ip()
        else:
            print(f"{Fore.RED}Invalid choice. Please enter 1, 2, or 3.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
