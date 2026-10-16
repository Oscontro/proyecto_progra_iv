<?php
// Activa o desactiva un usuario. "activo" es el estado NUEVO (true/false).
// Activar una cuenta pendiente (registrada desde la portada) la aprueba.
// Al desactivar, sus sesiones abiertas dejan de valer en el próximo pedido.
require_once 'usuarios_comun.php';
$user = requireAdmin();

$legajo = null;

try {
    $datos = getJsonInput();
    if (!$datos || !array_key_exists('activo', $datos)) {
        sendError("Faltan datos", 400);
    }
    $legajo = $datos['legajo'] ?? null;
    $activo = leerBooleano($datos['activo'], 'activo');

    $pdo = getConnection();
    $actual = usuarioPorLegajo($pdo, $legajo);
    // Activar nunca quita acceso; desactivar a un administrador sí.
    controlarAccesoAdmin($pdo, $actual, $user, $activo === 1 || !$actual['es_administrador'], 'desactivar');
    if (!$activo && (int)$actual['id_usuario'] === (int)$user['id']) {
        sendError("No podés desactivar tu propio usuario", 409);
    }

    // Activar una cuenta registrada desde la portada es aprobarla.
    $pdo->prepare("UPDATE usuarios SET activo = ?, pendiente_aprobacion = IF(? = 1, 0, pendiente_aprobacion) WHERE id_usuario = ?")
        ->execute([$activo, $activo, $actual['id_usuario']]);

    $mensaje = $activo ? ($actual['pendiente_aprobacion'] ? "Cuenta aprobada." : "Usuario activado.") : "Usuario desactivado.";
    sendSuccess(['activo' => (bool)$activo], $mensaje);

} catch (Throwable $e) {
    registrarError('toggle_activo', $user, "legajo=" . ($legajo ?? 'N/A') . " | " . $e->getMessage());
    sendError(API_DEBUG ? $e->getMessage() : "Error al actualizar el estado del usuario.", 500);
}
