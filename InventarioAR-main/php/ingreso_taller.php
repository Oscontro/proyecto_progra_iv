<?php
require_once 'historial_comun.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

function emptyToNull($value) {
    return ($value === '' || $value === null) ? null : $value;
}

// Declaradas afuera del try para que el catch pueda loguearlas
// aunque la excepción salte antes de armarlas.
$id_equipo = null;
$registro  = null;

try {
    $pdo = getConnection();
    $datos = getJsonInput();
    if (!$datos || !is_array($datos)) {
        sendError("No se recibieron datos", 400);
    }

    $id_equipo     = $datos['id_equipo'] ?? null;
    $estado        = $datos['estado'] ?? null;
    $nro_sd        = emptyToNull($datos['nro_sd'] ?? null);
    $elementos     = $datos['elementos'] ?? [];   // [] evita que el foreach falle si no viene
    $detalle_otros = $datos['detalle_otros'] ?? null;
    $id_recepcion  = $datos['id_recepcion'] ?? null;
    $id_estado     = $datos['id_estado'] ?? null;
    $id_taller     = $datos['id_taller'] ?? null;
    // id_usuario NO se lee del cliente: sale del token ($user['id']).

    // ── Lista blanca de columnas que el cliente puede activar ──
    // Los nombres de columna NO se pueden parametrizar con '?', van pegados
    // al SQL. Por eso validamos contra una lista fija: nada que no esté acá
    // llega a la consulta. Ajustá los nombres a los reales de tu tabla.
    $columnas_permitidas = [
        'componente_equipo',
        'componente_antena',
        'componente_cargador',
        'componente_bateria',
        'componente_fuente',
        'componente_cables',
        'componente_otros'
    ];

    $elementos_convertidos = [];
    foreach ((array)$elementos as $nombre_columna) {
        if (in_array($nombre_columna, $columnas_permitidas, true)) {
            $elementos_convertidos[$nombre_columna] = 1;
        }
        // Cualquier nombre fuera de la lista se ignora en silencio.
    }

    // ── Validaciones (antes solo las hacía el cliente) ──
    if (!$id_equipo || !$id_estado || !$id_taller) {
        sendError("Faltan datos del equipo", 400);
    }
    if (!$elementos_convertidos) {
        sendError("Debe seleccionar al menos un elemento", 400);
    }
    // Solo se ingresa un equipo enviado a taller que todavía figure como
    // "No ingresado" (7). Evita registrar dos ingresos del mismo equipo.
    $stmt = $pdo->prepare(
        "SELECT ee.id_estado, e.en_taller
           FROM equipo_estado ee JOIN equipos e ON e.id_equipo = ee.id_equipo
          WHERE ee.id = ? AND ee.id_equipo = ?");
    $stmt->execute([$id_estado, $id_equipo]);
    $actual = $stmt->fetch();
    if (!$actual || !$actual['en_taller']) {
        sendError("El equipo no está enviado a taller", 409);
    }
    if ((int)$actual['id_estado'] !== 7) {
        sendError("El equipo ya fue ingresado al taller", 409);
    }

    // Armar el registro. Estas claves fijas más las validadas de arriba.
    $registro = [
        'id_recepcion'              => $id_recepcion,
        'id_equipo'                 => $id_equipo,
        'taller'                    => $id_taller,
        'numero_ticket_sd'          => $nro_sd,
        'usuario_ingreso'           => $user['id'],   // ← del token
        'detalle_otros_componentes' => $detalle_otros,
        ...$elementos_convertidos,
    ];

    $pdo->beginTransaction();

    // "No ingresado" (7) -> "Ingresado" (3). Antes era el procedimiento
    // sp_ingresar_taller (el hosting no permite procedimientos).
    $pdo->prepare("UPDATE equipo_estado SET id_estado = 3 WHERE id = ? AND id_estado = 7")
        ->execute([$id_estado]);

    // Los VALORES van con placeholders (seguro). Los NOMBRES de columna
    // ya pasaron por la lista blanca, así que es seguro interpolarlos.
    $columnas     = implode(', ', array_keys($registro));
    $placeholders = implode(', ', array_fill(0, count($registro), '?'));

    $sql = "INSERT INTO taller_ingresos ($columnas) VALUES ($placeholders)";
    $stmt = $pdo->prepare($sql);
    $stmt->execute(array_values($registro));

    $stmt = $pdo->prepare("SELECT taller FROM talleres WHERE id_taller = ?");
    $stmt->execute([$id_taller]);
    registrarHistorialEquipo($pdo, (int)$id_equipo, $user['id'], 'INGRESO_TALLER',
        'Equipo ingresado a ' . $stmt->fetchColumn() . ($nro_sd !== null ? " - Ticket SD: $nro_sd" : ''));

    $pdo->commit();

    sendSuccess(['enviado' => true], "Se envió equipo a taller correctamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | ingreso_taller | id_equipo=" . ($id_equipo ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . " | datos=" . json_encode($registro) . PHP_EOL, FILE_APPEND);

    sendError(API_DEBUG ? $e->getMessage() : "No se pudo registrar el ingreso a taller", 500);
}