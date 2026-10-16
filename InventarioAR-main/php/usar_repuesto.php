<?php
// Uso en equipo: stock_actual (taller) -> en_uso (general).
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

    // FOR UPDATE: bloquea la fila hasta el commit, así dos pedidos
    // simultáneos no restan del mismo stock a la vez.
    $stmt = $pdo->prepare(
        "SELECT stock_actual FROM repuesto_stock
          WHERE id_repuesto = ? AND id_taller = ? FOR UPDATE");
    $stmt->execute([$id_repuesto, $id_taller]);
    $disponible = (int)$stmt->fetchColumn();   // sin fila = 0

    if ($disponible < $cantidad) {
        $pdo->rollBack();
        sendError("Stock insuficiente en $taller (disponible: $disponible, pedido: $cantidad)", 400);
    }

    $pdo->prepare(
        "UPDATE repuesto_stock SET stock_actual = stock_actual - ?
          WHERE id_repuesto = ? AND id_taller = ?"
    )->execute([$cantidad, $id_repuesto, $id_taller]);
    $pdo->prepare("UPDATE repuestos SET en_uso = en_uso + ? WHERE id_repuesto = ?")
        ->execute([$cantidad, $id_repuesto]);
    recalcularStockRepuesto($pdo, $id_repuesto);
    $pdo->commit();

    sendSuccess(['id_repuesto' => $id_repuesto], "Stock puesto en uso correctamente");

} catch (Throwable $e) {
    fallaRepuesto($e, 'usar_repuesto', $id_repuesto, $user, "No se pudo aplicar el cambio. Intente nuevamente.");
}
