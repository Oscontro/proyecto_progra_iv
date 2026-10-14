<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

function emptyToNull($value) {
    return ($value === '' || $value === null) ? null : $value;
}

// Declaradas afuera del try para que el catch pueda usarlas
// aunque la excepción salte antes de armarlas.
$id_equipo = null;
$registro  = null;

try {
    $datos = getJsonInput();
    if (!$datos || !is_array($datos)) {
        sendError("No se recibieron datos", 400);
    }

    $id_ingreso          = $datos['id_ingreso'] ?? null;
    $numero_guia         = $datos['numero_guia'] ?? null;
    $detalle_tareas      = emptyToNull($datos['detalle_tareas'] ?? null);
    $detalle_otros       = emptyToNull($datos['detalle_otros'] ?? null);
    $texto_email_informe = $datos['texto_email_informe'] ?? null;
    $repuestos           = $datos['elementos_repuestos'] ?? [];
    $tareas              = $datos['elementos_tareas'] ?? [];
    $id_equipo           = $datos['id_equipo'] ?? null;
    $id_estado           = $datos['id_estado'] ?? null;
    // usuario_egreso NO se lee del cliente: sale del token ($user['id']).

    // ── Lista blanca de repuestos ──
    $repuestos_permitidos = [
        'repuesto_potenciometro', 'repuesto_carcaza', 'repuesto_switch_ptt',
        'repuesto_plastico_ptt', 'repuesto_goma_ptt', 'repuesto_display',
        'repuesto_parlante', 'repuesto_microfono', 'repuesto_antena',
        'repuesto_bateria', 'repuesto_clip_cintura', 'repuesto_conector_rf',
        'repuesto_otros',
    ];

    $repuestos_convertidos = [];
    foreach ($repuestos as $nombre_columna) {
        if (in_array($nombre_columna, $repuestos_permitidos, true)) {
            $repuestos_convertidos[$nombre_columna] = 1;
        }
    }

    // ── Lista blanca de tareas ──
    $tareas_permitidas = [
        'tarea_soldadura_smd', 'tarea_verificacion_rf',
        'tarea_reprogramacion', 'tarea_otros',
    ];

    $tareas_convertidas = [];
    foreach ($tareas as $nombre_columna) {
        if (in_array($nombre_columna, $tareas_permitidas, true)) {
            $tareas_convertidas[$nombre_columna] = 1;
        }
    }

    // Armar el registro a insertar.
    $registro = [
        'id_ingreso'              => $id_ingreso,
        'usuario_egreso'          => $user['id'],   // ← del token
        'numero_guia'             => $numero_guia,
        'detalle_otros_tareas'    => $detalle_tareas,
        'detalle_otros_repuestos' => $detalle_otros,
        'texto_email_informe'     => $texto_email_informe,
        ...$tareas_convertidas,
        ...$repuestos_convertidos,
    ];

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);

    $pdo->beginTransaction();
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);
    // Cambio de estado. El usuario sale del token.
    $stmt_estado = $pdo->prepare("CALL sp_egreso_cambio_estado(?, ?, ?)");
    $stmt_estado->execute([$id_equipo, $user['id'], $id_estado]);
    $stmt_estado->closeCursor();

    // VALORES con placeholders; NOMBRES ya filtrados por la lista blanca.
    $columnas     = implode(', ', array_keys($registro));
    $placeholders = implode(', ', array_fill(0, count($registro), '?'));

    $sql = "INSERT INTO taller_egresos ($columnas) VALUES ($placeholders)";
    $stmt = $pdo->prepare($sql);
    $stmt->execute(array_values($registro));

    //INSERT TEXTO CORREO
    $sql_texto_auto = "INSERT INTO historial_equipos (id_equipo, usuario_evento, tipo_evento, observaciones) VALUES (?, ?, ?, ?)";
    $stmt_texto_auto = $pdo->prepare($sql_texto_auto);
    $stmt_texto_auto->execute([$id_equipo, $user["id"], 'TEXTO AUTOMATICO', $texto_email_informe]);

    $pdo->commit();

    sendSuccess(['enviado' => true], "Se egresó el equipo del taller correctamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | egreso_taller | id_equipo=" . ($id_equipo ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    // DEBUG temporal — sacar cuando esté estable:
    @file_put_contents($archivo_log, "DEBUG: " . json_encode($registro) . PHP_EOL, FILE_APPEND);

    sendError("DEBUG: " . $e->getMessage(), 500);
}