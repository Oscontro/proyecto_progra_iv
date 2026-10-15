<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$id_equipo = null;

try {
    $id_equipo    = $_GET['id_equipo'] ?? null;
    $id_recepcion = $_GET['id_recepcion'] ?? null;

    if (!$id_equipo || !$id_recepcion) {
        sendError("Faltan parámetros obligatorios", 400);
    }

    $pdo = getConnection();

    // Valor parametrizado con ? : viaja separado del SQL, sin riesgo de inyección.
    $sql = "SELECT * FROM vista_ingreso_taller WHERE id_recepcion = ?";
    $stmt = $pdo->prepare($sql);
    $stmt->execute([$id_recepcion]);

    $ingresos = $stmt->fetchAll();

    echo json_encode($ingresos, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | consulta_ingreso_taller"
           . " | id_equipo=" . ($id_equipo ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);

    sendError("No se pudieron obtener los datos. Intente nuevamente.", 500);
}