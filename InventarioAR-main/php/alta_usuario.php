<?php
// Alta de usuario. La clave temporal es aleatoria y se devuelve UNA vez en
// "clave_temporal" para que el administrador se la pase al usuario, que la
// debe cambiar en su primer ingreso (debe_cambiar_clave = 1).
require_once 'usuarios_comun.php';
$user = requireAdmin();

$username = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }
    $u = datosUsuario($datos);
    $username = $u['username'];

    $pdo = getConnection();
    controlarDuplicados($pdo, $u['legajo'], $u['username']);

    $clave = claveTemporal();
    $pdo->prepare(
        "INSERT INTO usuarios
            (legajo, username, nombre, apellido, email, password_hash,
             es_administrador, debe_cambiar_clave, activo, creado_por)
         VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)"
    )->execute([$u['legajo'], $u['username'], $u['nombre'], $u['apellido'], $u['email'],
                password_hash($clave, PASSWORD_DEFAULT), $u['es_administrador'], $u['activo'], $user['id']]);

    sendSuccess(['legajo' => $u['legajo'], 'clave_temporal' => $clave], "Usuario creado exitosamente.");

} catch (Throwable $e) {
    registrarError('crear_usuario', $user, "username=" . ($username ?? 'N/A') . " | " . $e->getMessage());
    sendError(API_DEBUG ? $e->getMessage() : "No se pudo crear el usuario.", 500);
}
