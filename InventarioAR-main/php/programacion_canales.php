<?php
require_once 'auth.php';    // trae conexion.php y config.php; define requireAuth y getJsonInput
$user = requireAuth();      // identidad verificada desde el token

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError('No se recibieron datos', 400);
    }

    $cantidad_canales = $datos['cantidad_canales'] ?? 0;
    $canales          = $datos['canales'] ?? [];

    if (empty($canales)) {
        sendError('No hay canales para guardar', 400);
    }

    $nombre_config = $canales[0]['nombre_config'] ?? '';

    $pdo = getConnection();

    // ── Transacción ──────────────────────────────────────────────
    // Son 1 + N inserts que forman UNA sola programación. Si falla
    // cualquiera, no debe quedar una programación a medio guardar.
    $pdo->beginTransaction();

    // 1) La cabecera. Guardamos también quién la creó (del token).
    $stmt = $pdo->prepare(
        "INSERT INTO programacion_canales (cantidad_canales, nombre_plantilla, usuario_programacion)
         VALUES (?, ?, ?)"
    );
    $stmt->execute([$cantidad_canales, $nombre_config, $user['id']]);

    $id_programacion = $pdo->lastInsertId();

    // 2) El detalle. Preparamos UNA vez, ejecutamos N veces.
    $stmt_canales = $pdo->prepare(
        "INSERT INTO canales_detalle
            (id_programacion, numero_canal, frecuencia_tx, frecuencia_rx, codificacion, codigo_squelch)
         VALUES (?, ?, ?, ?, ?, ?)"
    );

    foreach ($canales as $i => $canal) {
        // Validamos que el canal traiga lo mínimo, para dar un error claro
        // en vez de que reviente el INSERT con un mensaje críptico.
        if (!isset($canal['numero_canal'])) {
            throw new RuntimeException("El canal en la posición $i no tiene numero_canal");
        }

        $stmt_canales->execute([
            $id_programacion,
            $canal['numero_canal'],
            $canal['frecuencia_tx']  ?? null,
            $canal['frecuencia_rx']  ?? null,
            $canal['codificacion']   ?? null,
            $canal['codigo_squelch'] ?? null,
        ]);
    }

    $pdo->commit();   // ← todo salió bien: confirmamos las N+1 filas juntas

    sendSuccess(['id_programacion' => (int)$id_programacion],
                'Programación guardada correctamente');

} catch (Throwable $e) {
    // Throwable atrapa tanto PDOException como el RuntimeException de arriba.
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();   // deshace la cabecera y los canales ya insertados
    }

    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | programacion_canales | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);

    sendError("Error al guardar programación: " . $e->getMessage(), 500);
}