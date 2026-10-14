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

    $id_repuesto   = $datos['id_repuesto'] ?? null;
    $taller        = $datos['taller'] ?? null;
    $agregar_stock = $datos['cantidad'] ?? null;

    if (!$id_repuesto) {
        sendError("Falta id_repuesto", 400);
    }

    $pdo = getConnection();

    // El repuesto tiene que existir.
    $stmt_existe = $pdo->prepare("SELECT COUNT(*) FROM repuestos WHERE id_repuesto = ?");
    $stmt_existe->execute([$id_repuesto]);
    if ($stmt_existe->fetchColumn() == 0) {
        sendError("No se encontró el repuesto con id_repuesto = $id_repuesto", 404);
    }

    $pdo->beginTransaction();

    $stmt_id_taller = $pdo->prepare("SELECT id_taller FROM talleres WHERE taller = ?");
    $stmt_stock_existe = $pdo->prepare(
        "SELECT COUNT(*) FROM repuesto_stock WHERE id_repuesto = ? AND id_taller = ?"
    );
    $stmt_update_stock = $pdo->prepare(
        "UPDATE repuesto_stock SET stock_actual = stock_actual + ? WHERE id_repuesto = ? AND id_taller = ?"
    );
    $stmt_insert_stock = $pdo->prepare(
        "INSERT INTO repuesto_stock (id_repuesto, id_taller, stock_actual, fecha_ingreso)
         VALUES (?, ?, ?, NOW())"
    );

    $stmt_id_taller->execute([$taller]);
    $id_taller = $stmt_id_taller->fetchColumn();

    if ($id_taller === false) {
        throw new RuntimeException("Taller no encontrado: $nombre_taller");
    }

    $stmt_stock_existe->execute([$id_repuesto, $id_taller]);
    if ($stmt_stock_existe->fetchColumn() > 0) {
        $stmt_update_stock->execute([$agregar_stock, $id_repuesto, $id_taller]);
    } else {
        $stmt_insert_stock->execute([$id_repuesto, $id_taller, $agregar_stock]);
    }

    $pdo->commit();

    sendSuccess(['id_repuesto' => (int)$id_repuesto], "Stock ingresado correctamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | ingreso_repuesto | id_repuesto =" . ($id_repuesto ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("No se pudo modificar el repuesto. Intente nuevamente.", 500);
}