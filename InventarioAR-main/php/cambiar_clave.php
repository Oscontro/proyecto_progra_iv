<?php
require_once 'auth.php';
$user = requireAuth(true);   // el usuario ya se logueó (con su clave temporal o la actual)

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $input = getJsonInput();
    $actual = $input['clave_actual'] ?? '';
    $nueva  = $input['nueva_clave'] ?? '';

    // Validaciones de la clave nueva.
    if ($nueva === '') {
        sendError('Falta la nueva contraseña', 400);
    }
    if (strlen($nueva) < 8) {
        sendError('La contraseña debe tener al menos 8 caracteres', 400);
    }

    $pdo = getConnection();

    // Traemos el hash actual del usuario (identificado por el TOKEN, no por el cliente).
    $stmt = $pdo->prepare("SELECT password_hash, debe_cambiar_clave FROM usuarios WHERE id_usuario = ?");
    $stmt->execute([$user['id']]);
    $fila = $stmt->fetch();

    if (!$fila) {
        sendError('Usuario no encontrado', 404);
    }

    // Verificamos la clave ACTUAL antes de permitir el cambio.
    // (Aunque esté logueado, confirmar la clave vigente evita que, si alguien
    //  dejó la sesión abierta, un tercero le cambie la contraseña.)
    if (!password_verify($actual, $fila['password_hash'])) {
        sendError('La contraseña actual es incorrecta', 401);
    }

    // Evitamos que repita la misma clave.
    if (password_verify($nueva, $fila['password_hash'])) {
        sendError('La nueva contraseña debe ser distinta de la actual', 400);
    }

    // Guardamos la nueva y apagamos el flag de "debe cambiar".
    $hash = password_hash($nueva, PASSWORD_DEFAULT);
    $pdo->prepare(
        "UPDATE usuarios SET password_hash = ?, debe_cambiar_clave = 0 WHERE id_usuario = ?"
    )->execute([$hash, $user['id']]);

    sendSuccess(['cambiada' => true], 'Contraseña actualizada correctamente');

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | cambiar_clave | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError('No se pudo cambiar la contraseña. Intente nuevamente.', 500);
}