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

    $stmt_stock_actual = $pdo->prepare(
        "SELECT stock_actual FROM repuesto_stock
         WHERE id_repuesto = ? AND id_taller = ?
         FOR UPDATE"   // bloquea la fila hasta el commit, evita que dos
                        // pedidos simultáneos resten del mismo stock a la vez
    );
    $stmt_stock_actual->execute([$id_repuesto, $id_taller]);
    $stock_actual = $stmt_stock_actual->fetchColumn();

    if ($stock_actual === false) {
        $pdo->rollBack();
        sendError("Este repuesto no tiene stock registrado en $taller", 400);
    }

    // Validar ANTES de tocar nada.
    if ($stock_actual < $cantidad) {
        $pdo->rollBack();
        sendError("Stock insuficiente en $taller (disponible: $stock_actual, pedido: $cantidad)", 400);
    }

    // Recién ahora, con la validación ya hecha, se modifica la base.
    $pdo->prepare(
        "UPDATE repuesto_stock SET stock_actual = stock_actual - ?
         WHERE id_repuesto = ? AND id_taller = ?"
    )->execute([$cantidad, $id_repuesto, $id_taller]);

    $pdo->prepare(
        "UPDATE repuestos SET en_uso = en_uso + ? WHERE id_repuesto = ?"
    )->execute([$cantidad, $id_repuesto]);

    $pdo->commit();

    sendSuccess(['id_repuesto' => (int)$id_repuesto], "Stock puesto en uso correctamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | ingreso_repuesto | id_repuesto=" . ($id_repuesto ?? 'N/A')
           . " | taller=" . ($taller ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("No se pudo aplicar el cambio. Intente nuevamente.", 500);
}