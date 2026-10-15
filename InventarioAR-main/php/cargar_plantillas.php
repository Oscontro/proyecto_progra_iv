<?php
require_once 'auth.php';    // trae conexion.php y config.php; requireAuth y getJsonInput
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $nombre_config = trim($_GET['nombre_config'] ?? '');
    if ($nombre_config === '') {
        sendError('No se recibieron datos', 400);
    }

    $pdo = getConnection();

    // Cada equipo programado con una plantilla tiene su propia cabecera con
    // ese nombre. Se toma la más reciente: juntar todas mezclaría (y
    // repetiría) los canales de varias programaciones.
    $sql = "SELECT
                pc.nombre_plantilla,
                pc.cantidad_canales,
                cd.numero_canal,
                cd.frecuencia_tx,
                cd.frecuencia_rx,
                cd.codificacion,
                cd.codigo_squelch
            FROM programacion_canales pc
            LEFT JOIN canales_detalle cd ON cd.id_programacion = pc.id_programacion
            WHERE pc.id_programacion = (SELECT MAX(id_programacion) FROM programacion_canales WHERE nombre_plantilla = ?)
            ORDER BY cd.numero_canal";

    $stmt = $pdo->prepare($sql);
    $stmt->execute([$nombre_config]);

    $array_canales    = [];
    $cantidad_canales = 0;
    $encontrada       = false;   // ¿la plantilla existe, aunque no tenga canales?

    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $encontrada = true;
        $cantidad_canales = $row['cantidad_canales'];
        if ($row['numero_canal'] !== null) {
            $array_canales[] = [
                'nombre_config'  => $row['nombre_plantilla'],
                'numero_canal'   => (int)$row['numero_canal'],
                'frecuencia_tx'  => $row['frecuencia_tx'],
                'frecuencia_rx'  => $row['frecuencia_rx'],
                'codificacion'   => $row['codificacion'],
                'codigo_squelch' => $row['codigo_squelch'],
            ];
        }
    }

    // Distinguir "no existe" de "existe pero está vacía".
    if (!$encontrada) {
        sendError("No se encontró la plantilla '$nombre_config'", 404);
    }

    echo json_encode([
        "cantidad_canales" => (int)$cantidad_canales,
        "canales"          => $array_canales,
    ], JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | cargar_plantillas | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : 'Error al procesar los datos', 500);
}
