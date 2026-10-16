<?php
// Ajuste manual (forzado) de stock y fuera de servicio por taller, y de en uso.
// Espera: { id_repuesto, en_uso, talleres: { "<taller>": { stock, fuera_servicio } } }
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
    $en_uso      = leerEntero($datos['en_uso'] ?? null, 'En uso', 0);
    $talleres    = $datos['talleres'] ?? [];
    if (!is_array($talleres)) {
        sendError("Formato de talleres inválido", 400);
    }

    // Validar todo antes de escribir nada.
    $ajustes = [];
    foreach ($talleres as $nombre_taller => $info) {
        $ajustes[] = [
            idTaller($pdo, $nombre_taller),
            leerEntero($info['stock'] ?? null, "El stock de $nombre_taller", 0),
            leerEntero($info['fuera_servicio'] ?? null, "Fuera de servicio de $nombre_taller", 0),
        ];
    }

    $pdo->beginTransaction();
    $pdo->prepare("UPDATE repuestos SET en_uso = ? WHERE id_repuesto = ?")
        ->execute([$en_uso, $id_repuesto]);

    // fecha_ingreso la pone el servidor (NOW()); no se confía en el reloj del cliente.
    $stmt = $pdo->prepare(
        "INSERT INTO repuesto_stock (id_repuesto, id_taller, stock_actual, fuera_servicio, fecha_ingreso)
         VALUES (?, ?, ?, ?, NOW())
         ON DUPLICATE KEY UPDATE stock_actual = VALUES(stock_actual),
                                 fuera_servicio = VALUES(fuera_servicio),
                                 fecha_ingreso = NOW()");
    foreach ($ajustes as [$id_taller, $stock, $fuera_servicio]) {
        $stmt->execute([$id_repuesto, $id_taller, $stock, $fuera_servicio]);
    }
    recalcularStockRepuesto($pdo, $id_repuesto);
    $pdo->commit();

    sendSuccess(['id_repuesto' => $id_repuesto], "Repuesto actualizado correctamente");

} catch (Throwable $e) {
    fallaRepuesto($e, 'ajustar_stock', $id_repuesto, $user, "No se pudo ajustar el stock. Intente nuevamente.");
}
