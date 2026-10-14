<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $pdo = getConnection();

    $sql = "SELECT e.id_equipo,
                   e.numero_serie,
                   t.tipo,
                   mo.modelo_equipo AS modelo,
                   CASE es.escala
                       WHEN 'AEP' THEN 'Aeroparque'
                       WHEN 'EZE' THEN 'Ezeiza'
                       ELSE es.escala
                   END AS en_stock
            FROM equipos e
            JOIN modelos mo ON mo.id_modelo = e.modelo
            JOIN tipos t    ON t.id_tipo   = e.tipo
            JOIN escalas es ON es.id_escala = e.escala
            WHERE e.estado = 'En stock'
              AND e.sector = 'Taller de radio'
            ORDER BY t.tipo, mo.modelo_equipo";

    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    $equipos = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($equipos, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | en_stock | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("Error al obtener el stock", 500);
}