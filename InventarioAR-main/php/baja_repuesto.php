<?php
require_once 'auth.php';
$user = requireAdmin();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';
$id_repuesto = null;

try {
    $pdo = getConnection();

    $dato = getJsonInput();
    if (!$dato) {
        sendError("No se recibieron datos", 400);
    }

    $id_repuesto = $dato['id_repuesto'] ?? null;
    if (!$id_repuesto) {
        sendError("Falta id de repuesto", 400);
    }

    $stmt_existe = $pdo->prepare("SELECT COUNT(*) FROM repuestos WHERE id_repuesto = ?");
    $stmt_existe->execute([$id_repuesto]);
    if ($stmt_existe->fetchColumn() == 0) {
        sendError("No se encontró el repuesto con id_repuesto=$id_repuesto", 404);
    }


    $pdo->beginTransaction();

    // Orden: primero las tablas hijas, después el repuesto padre.
    $pdo->prepare("DELETE FROM repuesto_stock WHERE id_repuesto = ?")
        ->execute([$id_repuesto]);

    $pdo->prepare("DELETE FROM modelo_repuesto WHERE id_repuesto = ?")
        ->execute([$id_repuesto]);

    $pdo->prepare("DELETE FROM repuestos WHERE id_repuesto = ?")
        ->execute([$id_repuesto]);

    $pdo->commit();

    sendSuccess(['id_repuesto' => (int)$id_repuesto], "Repuesto eliminado correctamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | baja_repuesto | id_repuesto=" . ($id_repuesto ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("No se pudo eliminar el repuesto. Intente nuevamente.", 500);
}