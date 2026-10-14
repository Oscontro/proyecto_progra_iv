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

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    $stmt_eliminar_usuario = $pdo->prepare("DELETE FROM usuarios WHERE legajo = ?");
    $stmt_eliminar_usuario->execute([$legajo]);

    sendSuccess("Usuario eliminado exitosamente.", 200);

} catch (PDOException $e) {
    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | eliminar_usuario | legajo =" . ($legajo ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("Error al eliminar el usuario.", 500);
}