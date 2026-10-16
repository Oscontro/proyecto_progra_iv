<?php
// Modificación de los datos de catálogo de un repuesto (N° de parte, nombre, modelos).
//
// El stock por taller solo se toca si llegan stock_aep / stock_eze (lo manda el
// cliente de escritorio, que reescribe el stock desde el formulario). El cliente
// web no los manda: el stock se cambia con los movimientos o el ajuste forzado,
// así una edición de nombre no pisa movimientos hechos mientras tanto.
require_once 'repuestos_comun.php';
$user = requireAuth();

$id_repuesto = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $numero_parte = trim((string)($datos['numero_parte'] ?? ''));
    $nombre       = trim((string)($datos['nombre'] ?? ''));
    $modelos      = $datos['modelos'] ?? [];

    $pdo = getConnection();
    $id_repuesto = exigirRepuesto($pdo, $datos['id_repuesto'] ?? null);

    if ($numero_parte === '' || $nombre === '') {
        sendError("Faltan el número de parte o el nombre", 400);
    }
    if (!is_array($modelos) || !$modelos) {
        sendError("Vinculá al menos un modelo de equipo al repuesto", 400);
    }

    // Validar todo antes de escribir nada.
    $ids_modelos = [];
    $stmt_modelo = $pdo->prepare("SELECT COUNT(*) FROM modelos WHERE id_modelo = ?");
    foreach ($modelos as $id_modelo) {
        $id_modelo = leerEntero($id_modelo, 'El modelo', 1);
        $stmt_modelo->execute([$id_modelo]);
        if ($stmt_modelo->fetchColumn() == 0) {
            sendError("No existe el modelo $id_modelo", 400);
        }
        $ids_modelos[$id_modelo] = true;
    }

    $stocks = null;
    if (array_key_exists('stock_aep', $datos) || array_key_exists('stock_eze', $datos)) {
        $stocks = [
            [idTaller($pdo, 'Aeroparque'), leerEntero($datos['stock_aep'] ?? 0, 'El stock de Aeroparque', 0)],
            [idTaller($pdo, 'Ezeiza'),     leerEntero($datos['stock_eze'] ?? 0, 'El stock de Ezeiza', 0)],
        ];
    }

    $stmt_dup = $pdo->prepare("SELECT COUNT(*) FROM repuestos WHERE numero_parte = ? AND id_repuesto != ?");
    $stmt_dup->execute([$numero_parte, $id_repuesto]);
    if ($stmt_dup->fetchColumn() > 0) {
        sendError("Ya existe otro repuesto con el número de parte $numero_parte", 409);
    }

    $pdo->beginTransaction();
    $pdo->prepare("UPDATE repuestos SET numero_parte = ?, nombre = ? WHERE id_repuesto = ?")
        ->execute([$numero_parte, $nombre, $id_repuesto]);

    $pdo->prepare("DELETE FROM modelo_repuesto WHERE id_repuesto = ?")->execute([$id_repuesto]);
    $stmt = $pdo->prepare("INSERT INTO modelo_repuesto (id_repuesto, id_modelo) VALUES (?, ?)");
    foreach (array_keys($ids_modelos) as $id_modelo) {
        $stmt->execute([$id_repuesto, $id_modelo]);
    }

    if ($stocks !== null) {
        $stmt = $pdo->prepare(
            "INSERT INTO repuesto_stock (id_repuesto, id_taller, stock_actual, fuera_servicio, fecha_ingreso)
             VALUES (?, ?, ?, 0, NOW())
             ON DUPLICATE KEY UPDATE stock_actual = VALUES(stock_actual)");
        foreach ($stocks as [$id_taller, $stock]) {
            $stmt->execute([$id_repuesto, $id_taller, $stock]);
        }
    }
    recalcularStockRepuesto($pdo, $id_repuesto);
    $pdo->commit();

    sendSuccess(['id_repuesto' => $id_repuesto], "Repuesto modificado correctamente");

} catch (Throwable $e) {
    fallaRepuesto($e, 'modificar_repuesto', $id_repuesto, $user, "No se pudo modificar el repuesto. Intente nuevamente.");
}
