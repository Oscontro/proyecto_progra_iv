<?php
date_default_timezone_set("America/Argentina/Buenos_Aires");
require_once 'auth.php';    // trae conexion.php y config.php; requireAuth y getJsonInput
$user = requireAdmin();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$legajo = null;
$username = null;
$nombre = null;
$apellido = null;
$email = null;
$perfil = null;
$activo = null;

try{
    $datos = getJsonInput();

    if (!$datos) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $legajo     = $datos["legajo"] ?? null;
    $username   = $datos["username"] ?? null;
    $nombre     = $datos["nombre"] ?? null;
    $apellido   = $datos["apellido"] ?? null;
    $email      = $datos["email"] ?? null;
    $perfil     = $datos["perfil"] ?? null;
    $activo     = $datos["activo"] ?? null;

    if ($perfil == "Administrador"){
        $es_administrador = 1;
    }
    else{
        $es_administrador = 0;
    }

    if($activo == True){
        $usuario_activo = 1;
    }
    else{
        $usuario_activo = 0;
    }

    // Al ser creacion de usuario es primer ingreso
    // Corresponde clave generica 1234
    // debe_cambiar_clave = 1

    $clave_generica = '1234';
    $password_hash = password_hash($clave_generica, PASSWORD_DEFAULT);
    $debe_cambiar_clave = 1;

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    $stmt_alta_usuario = $pdo->prepare("INSERT INTO usuarios
                                    (legajo,
                                     username,
                                     nombre,
                                     apellido,
                                     email,
                                     password_hash,
                                     es_administrador,
                                     debe_cambiar_clave,
                                     activo,
                                     fecha_creacion,
                                     creado_por)
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
    $stmt_alta_usuario->execute([
                            $legajo,
                            $username,
                            $nombre,
                            $apellido,
                            $email,
                            $password_hash,
                            $es_administrador,
                            $debe_cambiar_clave,
                            $usuario_activo,
                            date("Y-m-d H:i:s"),
                            $user['id']]);

    sendSuccess("Usuario creado exitosamente.", 200);

} catch (PDOException $e) {
    // Código de error 23000 = Violación de restricción de integridad (duplicado/clave foránea)
    if ($e->getCode() === '23000') {
        $mensajeError = $e->getMessage();

        // Evaluamos cuál de las claves únicas falló leyendo el mensaje del motor SQL
        if (str_contains($mensajeError, 'legajo') || str_contains($mensajeError, 'KEY_LEGAJO')) {
            sendError("El legajo '{$legajo}' ya se encuentra registrado en el sistema.", 400);
        } else if (str_contains($mensajeError, 'username') || str_contains($mensajeError, 'KEY_USERNAME')) {
            sendError("El nombre de usuario '{$username}' ya está en uso.", 400);
        } else {
            sendError("El legajo o el nombre de usuario ya existen en el sistema.", 400);
        }
    } else {
        // Error interno del servidor o de base de datos
        error_log("Error SQL: " . $e->getMessage()); // Registro para el desarrollador
        sendError("Ocurrió un error interno al procesar la solicitud.", 500);
    }
    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | crear_usuario | username =" . ($username ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
}
