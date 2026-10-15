<?php
// Ingreso de unidades al stock de un taller: + stock_actual (taller).
require_once 'repuestos_comun.php';
$user = requireAuth();

$id_repuesto = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $pdo = getConnection();
    $id_repuesto = exigirRepuesto($pdo, $datos['id_repuesto'] ?? null);
    $id_taller   = idTaller($pdo, $datos['taller'] ?? null);
    $cantidad    = leerEntero($datos['cantidad'] ?? null, 'La cantidad', 1);

    $pdo->beginTransaction();
    asegurarFilaStock($pdo, $id_repuesto, $id_taller);
    $pdo->prepare(
        "UPDATE repuesto_stock SET stock_actual = stock_actual + ?, fecha_ingreso = NOW()
          WHERE id_repuesto = ? AND id_taller = ?"
    )->execute([$cantidad, $id_repuesto, $id_taller]);
    $pdo->commit();

    sendSuccess(['id_repuesto' => $id_repuesto], "Stock ingresado correctamente");

} catch (Throwable $e) {
    fallaRepuesto($e, 'ingreso_repuesto', $id_repuesto, $user, "No se pudo registrar el ingreso. Intente nuevamente.");
}
