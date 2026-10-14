<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $pdo = getConnection();

    $total       = $pdo->query("SELECT COUNT(id_equipo) FROM equipos WHERE en_taller = 0 AND en_papelera = 0")->fetchColumn();
    $en_taller   = $pdo->query("SELECT COUNT(id_equipo) FROM equipos WHERE en_taller = 1")->fetchColumn();
    $movimientos = $pdo->query("SELECT COUNT(identificador) FROM vista_movimientos WHERE origen COLLATE utf8mb4_unicode_ci = 'equipo' AND YEAR(fecha) = YEAR(NOW())")->fetchColumn();
    $dados_baja  = $pdo->query("SELECT COUNT(id_equipo) FROM equipos WHERE en_papelera = 1")->fetchColumn();

    sendSuccess([
        "total_equipos" => (int)$total,
        "en_taller"     => (int)$en_taller,
        "movimientos"   => (int)$movimientos,
        "dados_baja"    => (int)$dados_baja,
    ]);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | estadisticas_resumen | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("DEBUG: " . $e->getMessage(), 500);
}