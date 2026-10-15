<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $pdo = getConnection();

    $id_equipo = filter_var($_GET['id_equipo'] ?? null, FILTER_VALIDATE_INT);
    if (!$id_equipo) {
        sendError('Falta identificar el equipo (id_equipo)', 400);
    }

    // Si quedaron cabeceras duplicadas de versiones anteriores, vale la última.
    $sql = "SELECT
                pr.nombre_plantilla,
                pr.cantidad_canales,
                ca.numero_canal,
                ca.frecuencia_tx,
                ca.frecuencia_rx,
                ca.codificacion,
                ca.codigo_squelch
            FROM programacion_canales pr
            LEFT JOIN canales_detalle ca ON pr.id_programacion = ca.id_programacion
            WHERE pr.id_programacion = (SELECT MAX(id_programacion) FROM programacion_canales WHERE id_equipo = ?)
            ORDER BY ca.numero_canal";

    $stmt = $pdo->prepare($sql);
    $stmt->execute([$id_equipo]);

    $array_canales    = [];
    $cantidad_canales = 0;
    $nombre_plantilla = null;

    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $cantidad_canales = $row['cantidad_canales'];
        $nombre_plantilla = $row['nombre_plantilla'];
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

    // Un equipo sin programación no es un error: se devuelve vacía
    // (cantidad 0), y el cliente la muestra como "No configurado".
    echo json_encode([
        "cantidad_canales" => (int)$cantidad_canales,
        "nombre_plantilla" => $nombre_plantilla,
        "canales"          => $array_canales,
    ], JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | cargar_programacion | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : 'Error al procesar los datos', 500);
}
