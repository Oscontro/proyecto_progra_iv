<?php
// Resetea la clave de un usuario a una temporal aleatoria (se devuelve UNA
// vez en "clave_temporal"), obliga a cambiarla, quita el bloqueo por
// intentos fallidos. Las sesiones abiertas con la clave anterior dejan de
// valer (sesion.php compara la huella de la contraseña).
require_once 'usuarios_comun.php';
$user = requireAdmin();

$legajo = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }
    $legajo = $datos['legajo'] ?? null;

    $pdo = getConnection();
    $actual = usuarioPorLegajo($pdo, $legajo);
    if ((int)$actual['id_usuario'] === (int)$user['id']) {
        sendError("Para tu propia cuenta usá \"Cambiar contraseña\"", 409);
    }

    $clave = claveTemporal();
    $pdo->prepare(
        "UPDATE usuarios
            SET password_hash = ?, debe_cambiar_clave = 1, intentos_fallidos = 0, bloqueado_hasta = NULL
          WHERE id_usuario = ?"
    )->execute([password_hash($clave, PASSWORD_DEFAULT), $actual['id_usuario']]);

    sendSuccess(['legajo' => $actual['legajo'], 'clave_temporal' => $clave], "Contraseña reseteada.");

} catch (Throwable $e) {
    registrarError('resetear_clave', $user, "legajo=" . ($legajo ?? 'N/A') . " | " . $e->getMessage());
    sendError(API_DEBUG ? $e->getMessage() : "Error al resetear la contraseña del usuario.", 500);
}
