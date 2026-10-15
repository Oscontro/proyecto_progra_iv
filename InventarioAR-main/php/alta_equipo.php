<?php
// Alta de un equipo con su programación de canales (opcional).
//
// Entrada: { equipo: {...}, frecuencias: { canales: [...] },
//            crear_nuevos?: bool, solo_validar?: bool }
//
// Valores de catálogo (tipo, marca, modelo, escala) que no existen:
//   - La web manda crear_nuevos = false: se responde 409 CATALOGO_NUEVO con
//     la lista "nuevos"; el usuario confirma y se reenvía con true.
//   - El cliente de escritorio no manda la clave: se crean como antes
//     (compatibilidad hasta retirar el escritorio en la fase 4).
// solo_validar = true valida todo y devuelve "nuevos" sin guardar nada
// (lo usa la importación desde Excel para revisar el archivo antes).
require_once 'equipos_comun.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$numero_serie = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $equipo       = (array)($datos['equipo'] ?? []);
    $programacion = (array)($datos['frecuencias'] ?? []);
    $numero_serie = $equipo['numero_serie'] ?? null;
    $crearNuevos  = array_key_exists('crear_nuevos', $datos) ? (bool)$datos['crear_nuevos'] : true;
    $soloValidar  = !empty($datos['solo_validar']);

    $pdo = getConnection();
    $resultado = altaEquipo($pdo, $user, $equipo, $programacion, $crearNuevos, $soloValidar);

    sendSuccess($resultado, $soloValidar ? "Datos válidos" : "Equipo guardado exitosamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | alta_equipo | serie=" . ($numero_serie ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : "No se pudo guardar el equipo. Intente nuevamente.", 500);
}
