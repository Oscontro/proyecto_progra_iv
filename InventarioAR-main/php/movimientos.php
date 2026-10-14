<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $fecha_desde = $_GET['fecha_desde'] ?? null;
    $fecha_hasta = $_GET['fecha_hasta'] ?? null;

    if (!$fecha_desde || !$fecha_hasta) {
        sendError('Faltan las fechas', 400);
    }

    $fecha_desde_full = $fecha_desde . ' 00:00:00';
    $fecha_hasta_full = $fecha_hasta . ' 23:59:59';

    // Convertidos a entero: seguros para interpolar en el LIMIT.
    $limite = (int)($_GET['limite'] ?? 20);
    $offset = (int)($_GET['offset'] ?? 0);

    // Cotas de seguridad: evitamos que pidan tandas gigantes u offsets negativos.
    if ($limite < 1)   { $limite = 20; }
    if ($limite > 100) { $limite = 100; }
    if ($offset < 0)   { $offset = 0; }

    $pdo = getConnection();

    // Las fechas van con ? (texto del usuario). El LIMIT va interpolado
    // porque $offset y $limite ya son enteros forzados con (int).
    $sql = "SELECT origen, fecha, usuario, tipo_accion, identificador,
                   tipo, marca, modelo_equipo, detalle,
                   estado_anterior, estado_nuevo, observaciones
            FROM vista_movimientos
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC
            LIMIT $offset, $limite";

    $stmt = $pdo->prepare($sql);
    $stmt->execute([$fecha_desde_full, $fecha_hasta_full]);
    $movimientos = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($movimientos, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | movimientos | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError('Error al obtener movimientos', 500);
}