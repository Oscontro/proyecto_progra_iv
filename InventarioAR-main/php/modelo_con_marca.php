<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $pdo = getConnection();

    // Trae cada modelo con el nombre de su marca (join simple).
    // Ajustá los nombres de tabla/columna si difieren de los tuyos.
    $sql = "SELECT m.id_modelo, ma.marca, m.modelo_equipo
            FROM modelos m
            JOIN marcas ma ON ma.id_marca = m.marca
            ORDER BY ma.marca, m.modelo_equipo";

    $modelos = $pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($modelos, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | modelos_con_marca | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("DEBUG: " . $e->getMessage(), 500);
}