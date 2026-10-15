<?php
// Egreso de un equipo del taller: registra tareas y repuestos, descuenta el
// stock de los repuestos usados y deja el equipo "Reparado" fuera del taller.
//
// Repuestos usados (catálogo real, ver migración 2026-10-14):
//   repuestos_usados: [{ id_repuesto, cantidad }]  -> tienen que estar vinculados
//   al modelo del equipo; salen del stock del taller del ingreso y pasan a
//   "en uso" (igual que "Usar en equipo" de la pestaña Repuestos).
// Además se aceptan las columnas fijas elementos_repuestos (repuesto_otros +
// detalle_otros, y las genéricas por compatibilidad), que no tocan stock.
require_once 'repuestos_comun.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

function emptyToNull($value) {
    return ($value === '' || $value === null) ? null : $value;
}

// Columnas fijas de taller_egresos => texto para el historial.
const REPUESTOS_FIJOS = [
    'repuesto_potenciometro' => 'potenciometro', 'repuesto_carcaza' => 'carcaza',
    'repuesto_switch_ptt' => 'switch ptt', 'repuesto_plastico_ptt' => 'plastico ptt',
    'repuesto_goma_ptt' => 'goma ptt', 'repuesto_display' => 'display',
    'repuesto_parlante' => 'parlante', 'repuesto_microfono' => 'microfono',
    'repuesto_antena' => 'antena', 'repuesto_bateria' => 'bateria',
    'repuesto_clip_cintura' => 'clip cintura', 'repuesto_conector_rf' => 'conector rf',
    'repuesto_otros' => 'otros',
];
const TAREAS_PERMITIDAS = ['tarea_soldadura_smd', 'tarea_verificacion_rf', 'tarea_reprogramacion', 'tarea_otros'];

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
    $numero_guia         = emptyToNull($datos['numero_guia'] ?? null);
    $detalle_tareas      = emptyToNull($datos['detalle_tareas'] ?? null);
    $detalle_otros       = emptyToNull($datos['detalle_otros'] ?? null);
    $texto_email_informe = emptyToNull($datos['texto_email_informe'] ?? null);
    $id_equipo           = $datos['id_equipo'] ?? null;
    $id_estado           = $datos['id_estado'] ?? null;
    // usuario_egreso NO se lee del cliente: sale del token ($user['id']).

    // ── Listas blancas de columnas ──
    $repuestos_fijos = [];
    foreach ((array)($datos['elementos_repuestos'] ?? []) as $columna) {
        if (isset(REPUESTOS_FIJOS[$columna])) {
            $repuestos_fijos[$columna] = 1;
        }
    }
    $tareas = [];
    foreach ((array)($datos['elementos_tareas'] ?? []) as $columna) {
        if (in_array($columna, TAREAS_PERMITIDAS, true)) {
            $tareas[$columna] = 1;
        }
    }

    // ── Repuestos del catálogo usados (cantidad por repuesto) ──
    $usados = [];   // id_repuesto => cantidad
    foreach ((array)($datos['repuestos_usados'] ?? []) as $uso) {
        $id  = leerEntero($uso['id_repuesto'] ?? null, 'El repuesto', 1);
        $usados[$id] = ($usados[$id] ?? 0) + leerEntero($uso['cantidad'] ?? null, 'La cantidad de repuesto', 1);
    }

    // ── Validaciones de datos ──
    if (!$id_equipo || !$id_ingreso || !$id_estado) {
        sendError("Faltan datos del equipo", 400);
    }
    if (!$tareas) {
        sendError("Debe seleccionar al menos una tarea", 400);
    }
    if (isset($tareas['tarea_otros']) && $detalle_tareas === null) {
        sendError("Marcó 'Otros' en tareas pero no escribió el detalle", 400);
    }
    if (isset($repuestos_fijos['repuesto_otros']) && $detalle_otros === null) {
        sendError("Marcó 'Otros' en repuestos pero no escribió el detalle", 400);
    }

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);

    // El ingreso tiene que ser de este equipo, estar en taller y no estar egresado.
    $stmt = $pdo->prepare(
        "SELECT ti.egresado, ti.taller AS id_taller, t.taller, e.en_taller, e.modelo
           FROM taller_ingresos ti
           JOIN equipos e  ON e.id_equipo = ti.id_equipo
           JOIN talleres t ON t.id_taller = ti.taller
          WHERE ti.id_ingreso = ? AND ti.id_equipo = ?");
    $stmt->execute([$id_ingreso, $id_equipo]);
    $ingreso = $stmt->fetch();
    if (!$ingreso) {
        sendError("El equipo no tiene un ingreso a taller registrado", 409);
    }
    if (!$ingreso['en_taller'] || $ingreso['egresado']) {
        sendError("El equipo ya fue egresado del taller", 409);
    }
    $id_taller = (int)$ingreso['id_taller'];

    // Cada repuesto tiene que estar vinculado al modelo del equipo.
    $nombres = [];
    $stmt = $pdo->prepare(
        "SELECT r.nombre FROM modelo_repuesto mr JOIN repuestos r ON r.id_repuesto = mr.id_repuesto
          WHERE mr.id_repuesto = ? AND mr.id_modelo = ? LIMIT 1");
    foreach (array_keys($usados) as $id_repuesto) {
        $stmt->execute([$id_repuesto, $ingreso['modelo']]);
        $nombre = $stmt->fetchColumn();
        if ($nombre === false) {
            sendError("El repuesto $id_repuesto no está vinculado al modelo del equipo", 400);
        }
        $nombres[$id_repuesto] = $nombre;
    }

    $registro = [
        'id_ingreso'              => $id_ingreso,
        'usuario_egreso'          => $user['id'],   // ← del token
        'numero_guia'             => $numero_guia,
        'detalle_otros_tareas'    => $detalle_tareas,
        'detalle_otros_repuestos' => $detalle_otros,
        'texto_email_informe'     => $texto_email_informe,
        ...$tareas,
        ...$repuestos_fijos,
    ];

    $pdo->beginTransaction();
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    // Stock: se bloquean las filas y se valida TODO antes de modificar nada.
    $stmt = $pdo->prepare(
        "SELECT stock_actual FROM repuesto_stock WHERE id_repuesto = ? AND id_taller = ? FOR UPDATE");
    foreach ($usados as $id_repuesto => $cantidad) {
        $stmt->execute([$id_repuesto, $id_taller]);
        $disponible = (int)$stmt->fetchColumn();
        if ($disponible < $cantidad) {
            $pdo->rollBack();
            sendError("Stock insuficiente de \"{$nombres[$id_repuesto]}\" en {$ingreso['taller']} "
                    . "(disponible: $disponible, pedido: $cantidad)", 400);
        }
    }

    // Cambio de estado. El usuario sale del token.
    $stmt_estado = $pdo->prepare("CALL sp_egreso_cambio_estado(?, ?, ?)");
    $stmt_estado->execute([$id_equipo, $user['id'], $id_estado]);
    $stmt_estado->closeCursor();

    // VALORES con placeholders; NOMBRES ya filtrados por la lista blanca.
    $columnas     = implode(', ', array_keys($registro));
    $placeholders = implode(', ', array_fill(0, count($registro), '?'));
    $pdo->prepare("INSERT INTO taller_egresos ($columnas) VALUES ($placeholders)")
        ->execute(array_values($registro));
    $id_egreso = (int)$pdo->lastInsertId();

    // Repuestos del catálogo: stock del taller -> en uso, y registro del uso.
    $stmt_stock  = $pdo->prepare("UPDATE repuesto_stock SET stock_actual = stock_actual - ? WHERE id_repuesto = ? AND id_taller = ?");
    $stmt_en_uso = $pdo->prepare("UPDATE repuestos SET en_uso = en_uso + ? WHERE id_repuesto = ?");
    $stmt_uso    = $pdo->prepare(
        "INSERT INTO taller_egreso_repuestos (id_egreso, id_repuesto, nombre_repuesto, id_taller, cantidad)
         VALUES (?, ?, ?, ?, ?)");
    foreach ($usados as $id_repuesto => $cantidad) {
        $stmt_stock->execute([$cantidad, $id_repuesto, $id_taller]);
        $stmt_en_uso->execute([$cantidad, $id_repuesto]);
        $stmt_uso->execute([$id_egreso, $id_repuesto, $nombres[$id_repuesto], $id_taller, $cantidad]);
    }

    // Historial: repuestos utilizados (antes lo hacía un trigger con las columnas fijas).
    $detalle = [];
    foreach ($usados as $id_repuesto => $cantidad) {
        $detalle[] = "{$nombres[$id_repuesto]} x$cantidad";
    }
    foreach (array_keys($repuestos_fijos) as $columna) {
        $detalle[] = $columna === 'repuesto_otros' ? "otros: $detalle_otros" : REPUESTOS_FIJOS[$columna];
    }
    $stmt_historial = $pdo->prepare(
        "INSERT INTO historial_equipos (id_equipo, usuario_evento, tipo_evento, observaciones) VALUES (?, ?, ?, ?)");
    if ($detalle) {
        $stmt_historial->execute([$id_equipo, $user['id'], 'EGRESO_TALLER_REPUESTOS',
            "REPUESTOS UTILIZADOS ({$ingreso['taller']}): " . implode(', ', $detalle)]);
    }
    if ($texto_email_informe !== null) {
        $stmt_historial->execute([$id_equipo, $user['id'], 'TEXTO AUTOMATICO', $texto_email_informe]);
    }

    $pdo->commit();

    sendSuccess(['enviado' => true, 'id_egreso' => $id_egreso], "Se egresó el equipo del taller correctamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | egreso_taller | id_equipo=" . ($id_equipo ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . " | datos=" . json_encode($registro) . PHP_EOL, FILE_APPEND);

    sendError(API_DEBUG ? $e->getMessage() : "No se pudo registrar el egreso del taller", 500);
}
