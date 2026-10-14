<?php
date_default_timezone_set("America/Argentina/Buenos_Aires");
require_once 'auth.php';    // trae conexion.php y config.php; requireAuth y getJsonInput
$user = requireAdmin();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$legajo = null;
$activo = null;

try{
    $datos = getJsonInput();

    if (!$datos) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $legajo     = $datos["legajo"] ?? null;
    $activo     = $datos["activo"] ?? null;

    if($activo == "activar"){
        $usuario_activo = 1;
    }
    else{
        $usuario_activo = 0;
    }

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    $stmt_toggle_activo = $pdo->prepare("UPDATE usuarios SET activo = ? WHERE legajo = ?");
    $stmt_toggle_activo->execute([$usuario_activo, $legajo]);

    sendSuccess("Estado del usuario actualizado exitosamente.", 200);
    
} catch (PDOException $e) {
    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | crear_usuario | username =" . ($username ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("Error al actualizar el estado del usuario.", 500);
}