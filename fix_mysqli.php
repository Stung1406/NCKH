<?php
$iniPath = 'C:\\xampp\\php\\php.ini';
$content = file_get_contents($iniPath);

// Restore example comment
$content = str_replace(
    "; For example:\n;\nextension=mysqli\n;",
    "; For example:\n;\n;   extension=mysqli\n;",
    $content
);
$content = str_replace(
    "; For example:\r\n;\r\nextension=mysqli\r\n;",
    "; For example:\r\n;\r\n;   extension=mysqli\r\n;",
    $content
);

file_put_contents($iniPath, $content);
