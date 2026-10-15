<?php
// Activa o desactiva un usuario. "activo" es el estado NUEVO (true/false;
// también se acepta "activar"/"desactivar").
require_once 'usuarios_comun.php';
$user = requireAdmin();

$legajo = null;

try {
    $datos = getJsonInput();
    if (!$datos || !array_key_exists('activo', $datos)) {
        sendError("Faltan datos", 400);
    }
    $legajo = $datos['legajo'] ?? null;
    $activo = leerBooleano($datos['activo']);

    $pdo = getConnection();
    $actual = usuarioPorLegajo($pdo, $legajo);
    // Activar nunca quita acceso; desactivar a un administrador sí.
    controlarAccesoAdmin($pdo, $actual, $user, $activo === 1 || !$actual['es_administrador'], 'desactivar');
    if (!$activo && (int)$actual['id_usuario'] === (int)$user['id']) {
        sendError("No podés desactivar tu propio usuario", 409);
    }

    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);
    $pdo->prepare("UPDATE usuarios SET activo = ? WHERE id_usuario = ?")->execute([$activo, $actual['id_usuario']]);
    if (!$activo) {
        cerrarSesiones($pdo, (int)$actual['id_usuario']);
    }

    sendSuccess(['activo' => (bool)$activo], $activo ? "Usuario activado." : "Usuario desactivado.");

} catch (Throwable $e) {
    registrarError('toggle_activo', $user, "legajo=" . ($legajo ?? 'N/A') . " | " . $e->getMessage());
    sendError(API_DEBUG ? $e->getMessage() : "Error al actualizar el estado del usuario.", 500);
}
