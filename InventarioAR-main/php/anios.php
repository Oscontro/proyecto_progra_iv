<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $pdo = getConnection();

    // Años distintos en los que hubo ingresos a taller (incidencias).
    // Ajustá la tabla/columna si "incidencias" sale de otro lado.
    $sql = "SELECT DISTINCT YEAR(fecha_ingreso) AS anio
            FROM taller_ingresos
            WHERE fecha_ingreso IS NOT NULL
            ORDER BY anio DESC";

    $stmt = $pdo->query($sql);
    $anios = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($anios, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | anios | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("Error al obtener los años", 500);
}