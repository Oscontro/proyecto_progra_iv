<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $pdo = getConnection();

    $sql = "SELECT 
                e.id_equipo,
                e.numero_serie,
                t.tipo,
                mo.modelo_equipo AS modelo,
                es.escala,
                e.estado,
                MAX(YEAR(pa.fecha_eliminacion)) AS anio_baja,
                COUNT(ti.id_ingreso) AS incidencias
            FROM equipos e
            JOIN modelos mo ON mo.id_modelo = e.modelo
            JOIN tipos t   ON t.id_tipo   = e.tipo
            JOIN escalas es ON es.id_escala = e.escala
            LEFT JOIN papelera pa ON pa.id_equipo = e.id_equipo
            LEFT JOIN taller_ingresos ti ON ti.id_equipo = e.id_equipo
            GROUP BY 
                e.id_equipo,
                e.numero_serie,
                t.tipo,
                mo.modelo_equipo,
                es.escala,
                e.estado;";

    $stmt= $pdo->prepare($sql);
    $stmt->execute();
    $equipo = $stmt->fetchAll();

    echo json_encode($equipo, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | estadistica_equipos | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("Error al obtener las estadísticas de equipos", 500);
}