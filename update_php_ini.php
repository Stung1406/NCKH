<?php
$iniPath = 'C:\\xampp\\php\\php.ini';
$backupPath = 'C:\\xampp\\php\\php.ini.bak';

if (!file_exists($iniPath)) {
    echo "php.ini not found at $iniPath\n";
    exit(1);
}

if (!file_exists($backupPath)) {
    copy($iniPath, $backupPath);
    echo "Created backup at $backupPath\n";
}

$content = file_get_contents($iniPath);

// 1. Uncomment and set extension_dir
// Look for ;extension_dir = "ext"
$content = preg_replace('/^;\s*extension_dir\s*=\s*"ext"/m', 'extension_dir = "C:\\xampp\\php\\ext"', $content);

// 2. Extensions to enable
$extensions = [
    'bz2',
    'curl',
    'fileinfo',
    'gd',
    'intl',
    'mbstring',
    'exif',
    'mysqli',
    'openssl',
    'pdo_mysql',
    'pdo_sqlite',
    'sodium',
    'sqlite3',
    'zip',
];

foreach ($extensions as $ext) {
    // Replace ;extension=ext with extension=ext
    $pattern = '/^;\s*extension\s*=\s*' . preg_quote($ext, '/') . '\b/m';
    $content = preg_replace($pattern, 'extension=' . $ext, $content);
}

// 3. Update common limits for Laravel & phpMyAdmin
$limits = [
    '/^upload_max_filesize\s*=\s*.*$/m' => 'upload_max_filesize = 64M',
    '/^post_max_size\s*=\s*.*$/m' => 'post_max_size = 64M',
    '/^memory_limit\s*=\s*.*$/m' => 'memory_limit = 512M',
    '/^max_execution_time\s*=\s*.*$/m' => 'max_execution_time = 120',
];

foreach ($limits as $pattern => $replacement) {
    $content = preg_replace($pattern, $replacement, $content);
}

file_put_contents($iniPath, $content);
echo "Successfully updated $iniPath\n";
