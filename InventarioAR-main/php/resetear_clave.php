<?php
date_default_timezone_set("America/Argentina/Buenos_Aires");
require_once 'auth.php';    // trae conexion.php y config.php; requireAuth y getJsonInput
$user = requireAdmin();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$legajo = null;

try{
    $datos = getJsonInput();

    if (!$datos) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $legajo     = $datos["legajo"] ?? null;

    $clave_generica = '1234';
    $password_hash = password_hash($clave_generica, PASSWORD_DEFAULT);
    $debe_cambiar_clave = 1;

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    $stmt_reset_clave = $pdo->prepare("UPDATE usuarios SET password_hash = ?, debe_cambiar_clave = ? WHERE legajo = ?");
    $stmt_reset_clave->execute([$password_hash, $debe_cambiar_clave, $legajo]);

    sendSuccess("Contraseña del usuario reseteada exitosamente.", 200);

} catch (PDOException $e) {
    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | resetear_clave | legajo =" . ($legajo ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("Error al resetear la contraseña del usuario.", 500);
}