<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();

    $numero_serie = $_GET['numero_serie'] ?? '';

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
            LEFT JOIN equipos e ON e.id_equipo = pr.id_equipo
            WHERE e.numero_serie = :numero_serie";

    $stmt = $pdo->prepare($sql);
    $stmt->execute(['numero_serie' => $numero_serie]);

    $array_canales   = [];
    $cantidad_canales = 0;
    $encontrada      = false;   // ¿la plantilla existe, aunque no tenga canales?

    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $encontrada = true;
        $cantidad_canales = $row['cantidad_canales'];

        if ($row['numero_canal'] !== null) {
            $array_canales[] = [
                'nombre_config'  => $row['nombre_plantilla'],
                'numero_canal'   => $row['numero_canal'],
                'frecuencia_tx'  => $row['frecuencia_tx'],
                'frecuencia_rx'  => $row['frecuencia_rx'],
                'codificacion'   => $row['codificacion'],
                'codigo_squelch' => $row['codigo_squelch'],
            ];
        }
    }

    // Distinguir "no existe" de "existe pero está vacía".
    if (!$encontrada) {
        sendError("No se encontró plantilla para el equipo: '$numero_serie'", 404);
    }

    echo json_encode([
        "cantidad_canales" => (int)$cantidad_canales,
        "canales"          => $array_canales,
    ]);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id_usuario']
           . " | cargar_progamacion | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError('Error al procesar los datos', 500);
}