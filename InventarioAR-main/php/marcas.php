<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $id_tipo = $_GET['id_tipo'] ?? null;
    $pdo = getConnection();

    $sql = "SELECT DISTINCT ma.id_marca, ma.marca
            FROM marcas ma
            JOIN modelos mo ON mo.marca = ma.id_marca";

    $parametros = [];
    if (!empty($id_tipo)) {
        $sql .= " WHERE mo.tipo = ?";
        $parametros[] = $id_tipo;
    }

    $sql .= " ORDER BY ma.marca";

    // prepare + execute: así el ? se reemplaza de forma segura por el valor real.
    $stmt = $pdo->prepare($sql);
    $stmt->execute($parametros);
    $marcas = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($marcas, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | marcas | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("Error al obtener marcas", 500);
}