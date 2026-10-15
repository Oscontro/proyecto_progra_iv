<?php
// Elimina un usuario. Si tiene registros que lo referencian (por ejemplo
// recepciones de taller) la base lo impide: se responde 409 sugiriendo
// desactivarlo, en lugar de un error genérico.
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
    controlarAccesoAdmin($pdo, $actual, $user, false, 'eliminar');

    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);
    try {
        $pdo->prepare("DELETE FROM usuarios WHERE id_usuario = ?")->execute([$actual['id_usuario']]);
    } catch (PDOException $e) {
        if (($e->errorInfo[1] ?? null) === 1451) {   // fila referenciada por una clave foránea
            sendError("El usuario tiene registros asociados (taller, observaciones…) y no se puede eliminar. Desactivalo en su lugar.", 409);
        }
        throw $e;
    }

    sendSuccess(['legajo' => $actual['legajo']], "Usuario eliminado.");

} catch (Throwable $e) {
    registrarError('eliminar_usuario', $user, "legajo=" . ($legajo ?? 'N/A') . " | " . $e->getMessage());
    sendError(API_DEBUG ? $e->getMessage() : "Error al eliminar el usuario.", 500);
}
