<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';
$numero_parte = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $id_repuesto  = $datos['id_repuesto'] ?? null;
    $numero_parte = $datos['numero_parte'] ?? null;
    $nombre       = $datos['nombre'] ?? null;
    $modelos      = $datos['modelos'] ?? [];
    $stock_aep    = (int)($datos['stock_aep'] ?? 0);
    $stock_eze    = (int)($datos['stock_eze'] ?? 0);

    if (!$id_repuesto) {
        sendError("Falta id_repuesto", 400);
    }
    if (!$numero_parte || !$nombre) {
        sendError("Faltan numero_parte o nombre", 400);
    }

    $pdo = getConnection();

    // El repuesto tiene que existir.
    $stmt_existe = $pdo->prepare("SELECT COUNT(*) FROM repuestos WHERE id_repuesto = ?");
    $stmt_existe->execute([$id_repuesto]);
    if ($stmt_existe->fetchColumn() == 0) {
        sendError("No se encontró el repuesto con id_repuesto=$id_repuesto", 404);
    }

    $stmt_dup = $pdo->prepare(
        "SELECT COUNT(*) FROM repuestos WHERE numero_parte = ? AND id_repuesto != ?"
    );
    $stmt_dup->execute([$numero_parte, $id_repuesto]);
    if ($stmt_dup->fetchColumn() > 0) {
        sendError("Ya existe otro repuesto con el número de parte $numero_parte", 400);
    }

    $pdo->beginTransaction();

    $pdo->prepare(
        "UPDATE repuestos SET numero_parte = ?, nombre = ? WHERE id_repuesto = ?"
    )->execute([$numero_parte, $nombre, $id_repuesto]);


    $pdo->prepare("DELETE FROM modelo_repuesto WHERE id_repuesto = ?")
        ->execute([$id_repuesto]);

    if (!empty($modelos)) {
        $stmt_modelo = $pdo->prepare(
            "INSERT INTO modelo_repuesto (id_repuesto, id_modelo) VALUES (?, ?)"
        );
        foreach ($modelos as $id_modelo) {
            $stmt_modelo->execute([$id_repuesto, (int)$id_modelo]);
        }
    }

    $stock_por_taller = [
        "Aeroparque" => $stock_aep,
        "Ezeiza"     => $stock_eze,
    ];

    $stmt_id_taller = $pdo->prepare("SELECT id_taller FROM talleres WHERE taller = ?");
    $stmt_stock_existe = $pdo->prepare(
        "SELECT COUNT(*) FROM repuesto_stock WHERE id_repuesto = ? AND id_taller = ?"
    );
    $stmt_update_stock = $pdo->prepare(
        "UPDATE repuesto_stock SET stock_actual = ? WHERE id_repuesto = ? AND id_taller = ?"
    );
    $stmt_insert_stock = $pdo->prepare(
        "INSERT INTO repuesto_stock (id_repuesto, id_taller, stock_actual, fuera_servicio, fecha_ingreso)
         VALUES (?, ?, ?, 0, NOW())"
    );

    foreach ($stock_por_taller as $nombre_taller => $cantidad) {
        $stmt_id_taller->execute([$nombre_taller]);
        $id_taller = $stmt_id_taller->fetchColumn();

        if ($id_taller === false) {
            throw new RuntimeException("Taller no encontrado: $nombre_taller");
        }

        $stmt_stock_existe->execute([$id_repuesto, $id_taller]);
        if ($stmt_stock_existe->fetchColumn() > 0) {
            $stmt_update_stock->execute([$cantidad, $id_repuesto, $id_taller]);
        } else {
            $stmt_insert_stock->execute([$id_repuesto, $id_taller, $cantidad]);
        }
    }

    $pdo->commit();

    sendSuccess(['id_repuesto' => (int)$id_repuesto], "Repuesto modificado correctamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | modificar_repuesto | numero_parte=" . ($numero_parte ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("No se pudo modificar el repuesto. Intente nuevamente.", 500);
}