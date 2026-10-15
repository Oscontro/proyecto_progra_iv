<?php
// Fuera de servicio: en_uso (general) -> fuera_servicio (taller).
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

    $stmt = $pdo->prepare("SELECT en_uso FROM repuestos WHERE id_repuesto = ? FOR UPDATE");
    $stmt->execute([$id_repuesto]);
    $en_uso = (int)$stmt->fetchColumn();

    if ($en_uso < $cantidad) {
        $pdo->rollBack();
        sendError("Repuestos en uso insuficientes (en uso: $en_uso, pedido: $cantidad)", 400);
    }

    // Antes, si el taller no tenía fila de stock, se restaba de "en uso"
    // pero no se sumaba en ningún lado: las unidades se perdían.
    asegurarFilaStock($pdo, $id_repuesto, $id_taller);
    $pdo->prepare("UPDATE repuestos SET en_uso = en_uso - ? WHERE id_repuesto = ?")
        ->execute([$cantidad, $id_repuesto]);
    $pdo->prepare(
        "UPDATE repuesto_stock SET fuera_servicio = fuera_servicio + ?
          WHERE id_repuesto = ? AND id_taller = ?"
    )->execute([$cantidad, $id_repuesto, $id_taller]);
    $pdo->commit();

    sendSuccess(['id_repuesto' => $id_repuesto], "Repuesto puesto fuera de servicio correctamente");

} catch (Throwable $e) {
    fallaRepuesto($e, 'fuera_servicio', $id_repuesto, $user, "No se pudo aplicar el cambio. Intente nuevamente.");
}
