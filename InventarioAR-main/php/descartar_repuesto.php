<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';
$id_repuesto = null;
$taller = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $id_repuesto = $datos['id_repuesto'] ?? null;
    $taller      = $datos['taller'] ?? null;
    $cantidad    = (int)($datos['cantidad'] ?? 0);

    if (!$id_repuesto || !$taller) {
        sendError("Faltan id_repuesto o taller", 400);
    }
    if ($cantidad <= 0) {
        sendError("La cantidad tiene que ser mayor a 0", 400);
    }

    $pdo = getConnection();

    $stmt_existe = $pdo->prepare("SELECT COUNT(*) FROM repuestos WHERE id_repuesto = ?");
    $stmt_existe->execute([$id_repuesto]);
    if ($stmt_existe->fetchColumn() == 0) {
        sendError("No se encontró el repuesto con id_repuesto = $id_repuesto", 404);
    }

    $stmt_id_taller = $pdo->prepare("SELECT id_taller FROM talleres WHERE taller = ?");
    $stmt_id_taller->execute([$taller]);
    $id_taller = $stmt_id_taller->fetchColumn();

    if ($id_taller === false) {
        sendError("Taller no encontrado: $taller", 400);
    }

    $pdo->beginTransaction();

    $stmt_fuera_servicio = $pdo->prepare(
        "SELECT fuera_servicio FROM repuesto_stock
         WHERE id_repuesto = ? AND id_taller = ?
         FOR UPDATE"   // bloquea la fila hasta el commit, evita que dos
                        // pedidos simultáneos resten del mismo stock a la vez
    );
    $stmt_fuera_servicio->execute([$id_repuesto, $id_taller]);
    $stock_fuera_servicio = $stmt_fuera_servicio->fetchColumn();

    if ($stock_fuera_servicio === false) {
        $pdo->rollBack();
        sendError("No hay repuesos fuera de servicio.", 400);
    }

    // Validar ANTES de tocar nada.
    if ($stock_fuera_servicio < $cantidad) {
        $pdo->rollBack();
        sendError("Repuestos fuera de serivicio insuficientes. (disponible: $stock_fuera_servicio, pedido: $cantidad)", 400);
    }

    // Recién ahora, con la validación ya hecha, se modifica la base.
    $pdo->prepare(
        "UPDATE repuesto_stock SET fuera_servicio = fuera_servicio - ?
         WHERE id_repuesto = ? AND id_taller = ?"
    )->execute([$cantidad, $id_repuesto, $id_taller]);

    $fecha = date("Y-m-d H:i:s");

    $pdo->prepare(
        "UPDATE repuesto_stock SET baja_repuesto = COALESCE(baja_repuesto, 0) + ?, ultima_fecha_baja = ?
         WHERE id_repuesto = ? AND id_taller = ?"
    )->execute([$cantidad, $fecha, $id_repuesto, $id_taller]);

    $pdo->commit();

    sendSuccess(['id_repuesto' => (int)$id_repuesto], "Repuesto descartado correctamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | descartar_repuesto | id_repuesto = " . ($id_repuesto ?? 'N/A')
           . " | taller=" . ($taller ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("Error: " . $e->getMessage(), 500);
}