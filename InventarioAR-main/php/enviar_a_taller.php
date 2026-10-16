<?php
require_once 'historial_comun.php';    // trae auth.php: requireAuth y getJsonInput
$user = requireAuth();      // ← la identidad sale de acá, verificada contra el token

// Nota: NO repetimos header('Content-Type: application/json').
// Ya lo pone config.php al incluirse. Repetirlo no rompe, pero es ruido.

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

// Estado de taller con el que entra un equipo recién enviado.
const ESTADO_NO_INGRESADO = 7;

// Declaramos afuera del try para que el catch pueda loguear el id aunque
// la excepción ocurra antes de asignarlo.
$id_equipo = null;

try {
    $datos = getJsonInput();   // el helper ya hace el json_decode y valida que sea array

    if (!$datos) {
        sendError('No se recibieron datos válidos', 400);
    }

    $id_equipo     = filter_var($datos['id_equipo'] ?? null, FILTER_VALIDATE_INT);
    $id_taller     = filter_var($datos['id_taller'] ?? null, FILTER_VALIDATE_INT);
    $observaciones = trim((string)($datos['observaciones'] ?? ''));
    // id_usuario YA NO se lee del cliente: viene del token ($user['id']).

    if (!$id_equipo || !$id_taller) {
        sendError('Faltan parámetros obligatorios', 400);
    }

    $pdo = getConnection();

    // ── Validaciones: antes solo las hacía (o no) el cliente ──
    // Un equipo que ya está en taller generaría una segunda recepción.
    $stmt = $pdo->prepare("SELECT en_papelera, en_taller FROM equipos WHERE id_equipo = ?");
    $stmt->execute([$id_equipo]);
    $equipo = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$equipo) {
        sendError('No se encontró el equipo', 404);
    }
    if ($equipo['en_papelera']) {
        sendError('El equipo está en la papelera', 409);
    }
    if ($equipo['en_taller']) {
        sendError('El equipo ya está en taller', 409);
    }
    $stmt = $pdo->prepare("SELECT 1 FROM talleres WHERE id_taller = ?");
    $stmt->execute([$id_taller]);
    if (!$stmt->fetchColumn()) {
        sendError('El taller elegido no existe', 400);
    }

    // ── Transacción: todas las escrituras son una sola operación lógica ──
    $pdo->beginTransaction();

    // Antes era el procedimiento sp_enviar_equipo_taller_v4 (el hosting no
    // permite procedimientos). El usuario sale de la sesión, no del JSON.
    $antes = filaEquipo($pdo, $id_equipo);
    $pdo->prepare("UPDATE equipos SET en_taller = TRUE, usuario_modificacion = ? WHERE id_equipo = ?")
        ->execute([$user['id'], $id_equipo]);
    registrarCambiosEquipo($pdo, $antes, $id_equipo, $user['id']);
    $pdo->prepare("INSERT INTO taller_recepcion (id_equipo, id_taller, usuario_modificacion) VALUES (?, ?, ?)")
        ->execute([$id_equipo, $id_taller, $user['id']]);
    // observaciones_equipos.texto_observacion es NOT NULL: sin texto va vacío.
    $pdo->prepare("INSERT INTO observaciones_equipos (id_equipo, usuario_observacion, texto_observacion) VALUES (?, ?, ?)")
        ->execute([$id_equipo, $user['id'], $observaciones]);
    $pdo->prepare("INSERT INTO observaciones_taller (id_equipo, usuario_observacion, observacion) VALUES (?, ?, ?)")
        ->execute([$id_equipo, $user['id'], $observaciones]);

    // Registrar el nuevo estado del equipo ("No ingresado").
    $pdo->prepare("INSERT INTO equipo_estado (id_equipo, id_estado) VALUES (?, ?)")
        ->execute([$id_equipo, ESTADO_NO_INGRESADO]);

    $pdo->commit();   // ← recién acá se confirman ambas escrituras

    sendSuccess(['enviado' => true], 'Se envió el equipo a taller correctamente');

} catch (Throwable $e) {
    // Si había una transacción abierta, la deshacemos.
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    // El detalle real va al log, para vos. Al cliente le llega algo genérico.
    $linea = date('Y-m-d H:i:s') . " | enviar_a_taller | id_equipo=" . ($id_equipo ?: 'N/A')
           . " | usuario=" . $user['id'] . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);

    sendError(API_DEBUG ? $e->getMessage() : 'No se pudo enviar el equipo a taller. Intente nuevamente.', 500);
}
