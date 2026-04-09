#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Magento CMS Detection Scanner
Identify Magento installations from domain lists
BOB MARLEY LABS
"""

import os
import sys
import random
import urllib3
import requests
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Configure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== COLORS ====================
R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
B = "\033[94m"
M = "\033[95m"
C = "\033[96m"
W = "\033[97m"
RST = "\033[0m"

BANNER = f"""{C}
███╗   ███╗ █████╗  ██████╗ ███████╗███╗   ██╗████████╗ ██████╗ 
████╗ ████║██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔═══██╗
██╔████╔██║███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██║   ██║
██║╚██╔╝██║██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██║   ██║
██║ ╚═╝ ██║██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ╚██████╔╝
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ 
{RST}
           {Y}CMS Detection Scanner{RST} | {G}Magento Identification{RST}
"""

# ==================== CONFIG ====================
THREADS = 50
TIMEOUT = 8

# Create timestamped output directory
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = f"Result-CMS_{timestamp}"

# Thread-safe output
print_lock = Lock()

def safe_print(msg):
    """Thread-safe printing"""
    with print_lock:
        print(msg, flush=True)

# ==================== UTILITIES ====================
def ensure_output_dir():
    """Create output directory if not exists"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def normalize_url(url):
    """Normalize URL to include http/https"""
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        return f"https://{url}"
    return url

def get_bypass_headers():
    """403 bypass headers"""
    return {
        'X-Forwarded-For': '127.0.0.1',
        'X-Originating-IP': '127.0.0.1',
        'X-Remote-IP': '127.0.0.1',
        'X-Remote-Addr': '127.0.0.1',
        'X-Client-IP': '127.0.0.1',
        'X-Host': '127.0.0.1',
        'X-Forwarded-Host': '127.0.0.1',
        'X-Real-IP': '127.0.0.1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

def read_domains(file_path):
    """Read domains from file"""
    try:
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    domains = [normalize_url(line.strip()) for line in f if line.strip()]
                return domains
            except UnicodeDecodeError:
                continue
        return []
    except Exception as e:
        safe_print(f"{R}[ERROR]{RST} Reading file: {e}")
        return []

# ==================== MAGENTO DETECTION ====================
def detect_magento(url):
    """
    Detect if site is running Magento - STRICT VERIFICATION
    Returns: (is_magento, version, confidence, indicators, status)
    """
    try:
        headers = get_bypass_headers()
        session = requests.Session()
        session.max_redirects = 3
        
        is_magento = False
        version = "Unknown"
        confidence = 0
        indicators = []
        status = "LIVE"
        
        # CRITICAL: Check if site is alive first
        try:
            alive_check = session.get(url, headers=headers, timeout=8, verify=False, allow_redirects=True)
            if alive_check.status_code >= 500:
                return (False, "Unknown", 0, [], "DEAD (5xx)")
            elif alive_check.status_code == 404:
                return (False, "Unknown", 0, [], "DEAD (404)")
            elif alive_check.status_code in [0, 503]:
                return (False, "Unknown", 0, [], "DOWN")
        except requests.exceptions.Timeout:
            return (False, "Unknown", 0, [], "TIMEOUT")
        except requests.exceptions.ConnectionError:
            return (False, "Unknown", 0, [], "CONNECTION FAILED")
        except Exception as e:
            return (False, "Unknown", 0, [], f"ERROR: {str(e)[:30]}")
        
        # VERIFICATION PHASE 1: Check CRITICAL Magento paths (must match at least ONE)
        critical_paths = [
            ('/pub/static/version', True, 50),
            ('/static/version', True, 50),
            ('/pub/media/customer_address/', False, 45),  # CVE target - VERY specific
            ('/media/catalog/product/', False, 40),
            ('/checkout/cart/', False, 35),
            ('/customer/account/login/', False, 35),
        ]
        
        path_verified = False
        for path, read_content, points in critical_paths:
            try:
                r = session.get(f"{url}{path}", headers=headers, timeout=5, verify=False, allow_redirects=True)
                
                # Strict path verification
                if r.status_code == 200:
                    # For version files, must contain version number
                    if 'version' in path:
                        version_match = re.search(r'(\d+\.\d+\.\d+)', r.text)
                        if version_match:
                            version = version_match.group(1)
                            confidence += points + 30
                            indicators.append(f"Version file: {version}")
                            path_verified = True
                            break
                    else:
                        confidence += points
                        indicators.append(f"Path: {path}")
                        path_verified = True
                        
                elif r.status_code == 403:
                    # 403 is good for customer_address (means CVE path exists but forbidden)
                    if 'customer_address' in path or 'checkout' in path:
                        confidence += points - 10
                        indicators.append(f"Path (403): {path}")
                        path_verified = True
            except:
                continue
        
        # VERIFICATION PHASE 2: Homepage MUST have Magento signatures
        homepage_verified = False
        try:
            r = session.get(url, headers=headers, timeout=7, verify=False, allow_redirects=True)
            
            if r.status_code == 200:
                content = r.text.lower()
                content_raw = r.text
                
                # STRICT: Must have MULTIPLE Magento signatures (not just one)
                magento_sigs = {
                    'mage/cookies': 0,
                    'requirejs-config': 0,
                    'mage/requirejs/mixins': 0,
                    'var/view_preprocessed': 0,
                    'x_magento_init': 0,
                    'checkout/sidebar': 0,
                    'mage/translate': 0,
                    'customer/account': 0,
                    'catalogsearch/result': 0,
                }
                
                sig_matches = 0
                for sig in magento_sigs.keys():
                    if sig in content:
                        sig_matches += 1
                        indicators.append(f"Sig: {sig}")
                
                # MUST have at least 2 signatures
                if sig_matches >= 2:
                    confidence += sig_matches * 15
                    homepage_verified = True
                elif sig_matches == 1:
                    confidence += 10
                
                # Check for X-Magento headers (STRONGEST proof)
                magento_headers = ['x-magento-cache-control', 'x-magento-cache-debug', 'x-magento-tags', 'x-magento-vary']
                header_found = False
                for header in magento_headers:
                    if header in r.headers:
                        confidence += 50
                        indicators.append(f"Header: {header}")
                        homepage_verified = True
                        header_found = True
                        break
                
                # STRICT: Check for Magento copyright/powered by
                if 'magento' in content and ('powered by' in content or 'copyright' in content):
                    confidence += 20
                    indicators.append("Powered by Magento")
                    homepage_verified = True
                
                # Version from HTML (bonus)
                if version == "Unknown":
                    version_patterns = [
                        r'magento[/\s]+v?(\d+\.\d+\.\d+)',
                        r'version["\']?\s*[:=]\s*["\']?(\d+\.\d+\.\d+)',
                        r'mage-version["\']?\s*[:=]\s*["\']?(\d+\.\d+)',
                    ]
                    
                    for pattern in version_patterns:
                        match = re.search(pattern, content)
                        if match:
                            version = match.group(1)
                            confidence += 15
                            indicators.append(f"Version: {version}")
                            break
        except:
            pass
        
        # VERIFICATION PHASE 3: robots.txt verification (supplementary)
        try:
            r = session.get(f"{url}/robots.txt", headers=headers, timeout=4, verify=False)
            if r.status_code == 200:
                content = r.text.lower()
                # STRICT: Must have multiple Magento-specific paths
                magento_paths = ['/pub/media/', '/media/catalog/', '/customer/account/', '/checkout/cart/', '/catalogsearch/']
                robot_matches = sum(1 for p in magento_paths if p in content)
                
                if robot_matches >= 2:
                    confidence += 25
                    indicators.append(f"robots.txt: {robot_matches} Magento paths")
        except:
            pass
        
        # STRICT DECISION: Must pass BOTH path verification AND homepage verification
        # OR have very high confidence from one source
        if (path_verified and homepage_verified) or confidence >= 80:
            is_magento = True
        elif confidence < 50:
            is_magento = False
        else:
            # Medium confidence - needs more indicators
            if len(indicators) >= 3:
                is_magento = True
            else:
                is_magento = False
        
        return (is_magento, version, confidence, indicators, status)
        
    except Exception as e:
        return (False, "Unknown", 0, [f"Error: {str(e)[:50]}"], "ERROR")

# ==================== SCANNER ====================
def scan_domains(domains):
    """Scan domains for Magento"""
    safe_print(f"\n{C}[*]{RST} Scanning {len(domains)} domains with {THREADS} threads...")
    safe_print(f"{C}[*]{RST} Detecting Magento installations...\n")
    
    magento_sites = []
    completed = 0
    
    # Prepare output files
    ensure_output_dir()
    magento_file = os.path.join(OUTPUT_DIR, "Magento_Sites.txt")
    detailed_file = os.path.join(OUTPUT_DIR, "Magento_Detailed.txt")
    non_magento_file = os.path.join(OUTPUT_DIR, "Non_Magento.txt")
    
    def scan_single(url):
        nonlocal completed
        is_magento, version, confidence, indicators, status = detect_magento(url)
        completed += 1
        
        if completed % 50 == 0:
            safe_print(f"{Y}[PROGRESS]{RST} {completed}/{len(domains)} scanned, {len(magento_sites)} Magento found...")
        
        # Handle dead/error sites
        if status != "LIVE":
            safe_print(f"{R}[DEAD]{RST} {url} - {status}")
            with print_lock:
                with open(non_magento_file, 'a', encoding='utf-8') as f:
                    f.write(f"{url} # {status}\n")
            return None
        
        if is_magento:
            # Show detailed info in CLI
            safe_print(f"{G}[MAGENTO]{RST} {url}")
            safe_print(f"{C}  Version: {version} | Confidence: {confidence}% | Indicators: {len(indicators)}{RST}")
            
            # Save immediately
            with print_lock:
                # Simple list
                with open(magento_file, 'a', encoding='utf-8') as f:
                    f.write(f"{url}\n")
                
                # Detailed info
                with open(detailed_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"URL: {url}\n")
                    f.write(f"Version: {version}\n")
                    f.write(f"Confidence: {confidence}%\n")
                    f.write(f"Indicators:\n")
                    for ind in indicators:
                        f.write(f"  - {ind}\n")
                    f.write(f"{'='*80}\n")
            
            return {'url': url, 'version': version, 'confidence': confidence}
        else:
            safe_print(f"{R}[NOT MAGENTO]{RST} {url} - Confidence: {confidence}%")
            # Save non-magento
            with print_lock:
                with open(non_magento_file, 'a', encoding='utf-8') as f:
                    f.write(f"{url}\n")
        
        return None
    
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(scan_single, url) for url in domains]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                magento_sites.append(result)
    
    safe_print(f"\n{G}[+]{RST} Scan complete!")
    safe_print(f"{G}[+]{RST} Found {len(magento_sites)}/{len(domains)} Magento sites")
    safe_print(f"{G}[+]{RST} Results saved:")
    safe_print(f"{G}    - {magento_file}{RST}")
    safe_print(f"{G}    - {detailed_file}{RST}")
    safe_print(f"{G}    - {non_magento_file}{RST}\n")
    
    # Summary by version
    if magento_sites:
        safe_print(f"{C}[SUMMARY BY VERSION]{RST}")
        versions = {}
        for site in magento_sites:
            v = site['version']
            versions[v] = versions.get(v, 0) + 1
        
        for version, count in sorted(versions.items(), key=lambda x: x[1], reverse=True):
            safe_print(f"{Y}  {version}: {count} sites{RST}")
    
    return magento_sites

# ==================== MENU ====================
def show_menu():
    """Display main menu"""
    print(BANNER)
    print(f"{G}[1]{RST} Scan domains for Magento CMS")
    print(f"{R}[0]{RST} Exit\n")

def main():
    """Main function"""
    global THREADS
    
    while True:
        show_menu()
        
        choice = input(f"{C}[?]{RST} Select option: ").strip()
        
        if choice == '0':
            safe_print(f"\n{Y}[*]{RST} Exiting...\n")
            break
        
        if choice != '1':
            safe_print(f"{R}[!]{RST} Invalid option\n")
            continue
        
        # Get domain file
        domain_file = input(f"{C}[?]{RST} Domain list file path: ").strip()
        
        if not os.path.exists(domain_file):
            safe_print(f"{R}[!]{RST} File not found: {domain_file}\n")
            continue
        
        # Get threads
        thread_input = input(f"{C}[?]{RST} Threads (default {THREADS}): ").strip()
        if thread_input:
            try:
                THREADS = int(thread_input)
            except:
                safe_print(f"{R}[!]{RST} Invalid thread count, using {THREADS}\n")
        
        # Read domains
        domains = read_domains(domain_file)
        if not domains:
            safe_print(f"{R}[!]{RST} No valid domains found\n")
            continue
        
        safe_print(f"{G}[+]{RST} Loaded {len(domains)} domains\n")
        
        # Execute scan
        scan_domains(domains)
        
        input(f"\n{Y}Press Enter to continue...{RST}")
        print("\n" * 2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        safe_print(f"\n\n{Y}[!]{RST} Interrupted by user\n")
        sys.exit(0)
    except Exception as e:
        safe_print(f"\n{R}[ERROR]{RST} {e}\n")
        sys.exit(1)
