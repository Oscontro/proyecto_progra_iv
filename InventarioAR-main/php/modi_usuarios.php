<?php
// Modificación de usuario (el legajo identifica la cuenta y no se cambia).
require_once 'usuarios_comun.php';
$user = requireAdmin();

$legajo = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }
    $u = datosUsuario($datos);
    $legajo = $u['legajo'];

    $pdo = getConnection();
    $actual = usuarioPorLegajo($pdo, $legajo);
    controlarDuplicados($pdo, $u['legajo'], $u['username'], (int)$actual['id_usuario']);
    controlarAccesoAdmin($pdo, $actual, $user, $u['es_administrador'] && $u['activo'],
                         'quitarle el perfil de administrador o desactivar');

    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);
    $pdo->prepare(
        "UPDATE usuarios
            SET username = ?, nombre = ?, apellido = ?, email = ?, es_administrador = ?, activo = ?
          WHERE id_usuario = ?"
    )->execute([$u['username'], $u['nombre'], $u['apellido'], $u['email'],
                $u['es_administrador'], $u['activo'], $actual['id_usuario']]);
    if (!$u['activo']) {
        cerrarSesiones($pdo, (int)$actual['id_usuario']);
    }

    sendSuccess(['legajo' => $legajo], "Usuario actualizado exitosamente.");

} catch (Throwable $e) {
    registrarError('modificar_usuario', $user, "legajo=" . ($legajo ?? 'N/A') . " | " . $e->getMessage());
    sendError(API_DEBUG ? $e->getMessage() : "No se pudo modificar el usuario.", 500);
}
