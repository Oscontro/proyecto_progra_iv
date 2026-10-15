<?php
// Reparación: fuera_servicio (taller) -> stock_actual (taller).
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
    $taller      = $datos['taller'] ?? null;
    $id_taller   = idTaller($pdo, $taller);
    $cantidad    = leerEntero($datos['cantidad'] ?? null, 'La cantidad', 1);

    $pdo->beginTransaction();

    $stmt = $pdo->prepare(
        "SELECT fuera_servicio FROM repuesto_stock
          WHERE id_repuesto = ? AND id_taller = ? FOR UPDATE");
    $stmt->execute([$id_repuesto, $id_taller]);
    $fuera_servicio = (int)$stmt->fetchColumn();   // sin fila = 0

    if ($fuera_servicio < $cantidad) {
        $pdo->rollBack();
        sendError("Repuestos fuera de servicio insuficientes en $taller (disponible: $fuera_servicio, pedido: $cantidad)", 400);
    }

    $pdo->prepare(
        "UPDATE repuesto_stock
            SET fuera_servicio = fuera_servicio - ?,
                stock_actual = stock_actual + ?,
                fecha_ingreso = NOW()
          WHERE id_repuesto = ? AND id_taller = ?"
    )->execute([$cantidad, $cantidad, $id_repuesto, $id_taller]);
    $pdo->commit();

    sendSuccess(['id_repuesto' => $id_repuesto], "Repuesto agregado a stock correctamente");

} catch (Throwable $e) {
    fallaRepuesto($e, 'reparar_repuesto', $id_repuesto, $user, "No se pudo registrar la reparación. Intente nuevamente.");
}
