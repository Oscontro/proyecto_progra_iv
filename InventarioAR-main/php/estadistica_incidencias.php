<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $pdo = getConnection();

    // Una fila por cada ingreso a taller, con el año, tipo y escala
    // del equipo. El agrupamiento (por año, por tipo) se hace en Python.
    $sql = "SELECT YEAR(ti.fecha_ingreso) AS anio,
                   t.tipo,
                   e.escala,
                   e.id_equipo
            FROM taller_ingresos ti
            JOIN equipos e ON e.id_equipo = ti.id_equipo
            JOIN tipos t   ON t.id_tipo   = e.tipo
            WHERE ti.fecha_ingreso IS NOT NULL
            ORDER BY anio DESC";

    $stmt = $pdo->query($sql);
    $incidencias = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($incidencias, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | incidencias_por_anio | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("Error al obtener las incidencias", 500);
}