<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';
$numero_serie = null;

/**
 * Busca el id de un valor de catálogo. Si no existe, lo crea.
 * Devuelve SIEMPRE un único id (o lanza una excepción clara si algo
 * está mal), en vez de depender de una subconsulta anidada opaca.
 */
function resolverIdCatalogo(PDO $pdo, string $tabla, string $columnaId,
                            string $columnaValor, string $valor): int {
    $stmt = $pdo->prepare("SELECT $columnaId FROM $tabla WHERE $columnaValor = ?");
    $stmt->execute([$valor]);
    $filas = $stmt->fetchAll(PDO::FETCH_COLUMN);

    if (count($filas) > 1) {
        throw new RuntimeException(
            "Hay más de un registro en '$tabla' con $columnaValor = '$valor' (ids: " .
            implode(',', $filas) . "). Hay que limpiar los duplicados."
        );
    }
    if (count($filas) === 1) {
        return (int)$filas[0];
    }

    // No existe: lo creamos.
    $pdo->prepare("INSERT INTO $tabla ($columnaValor) VALUES (?)")->execute([$valor]);
    return (int)$pdo->lastInsertId();
}

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $equipo      = $datos['equipo'] ?? [];
    $programacion = $datos['frecuencias'] ?? [];
    $frecuencias  = $programacion['canales'] ?? [];

    $tipo          = $equipo['tipo'] ?? null;
    $marca         = $equipo['marca'] ?? null;
    $modelo        = $equipo['modelo'] ?? null;
    $numero_serie  = $equipo['numero_serie'] ?? null;
    $escala        = $equipo['escala'] ?? null;
    $sector        = $equipo['sector'] ?? null;
    $estado        = $equipo['estado'] ?? null;
    $potencia      = $equipo['potencia'] ?? null;
    $nombre_config = !empty($equipo['nombre_plantilla']) ? $equipo['nombre_plantilla'] : null;
    $observaciones = $equipo['ult_observacion'] ?? null;

    if (!$numero_serie) {
        sendError("Falta el número de serie", 400);
    }

    $pdo = getConnection();
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    $stmt_check = $pdo->prepare("SELECT COUNT(*) FROM equipos WHERE numero_serie = ?");
    $stmt_check->execute([$numero_serie]);
    if ($stmt_check->fetchColumn() > 0) {
        sendError("Ya existe un equipo con el número de serie $numero_serie", 400);
    }

    $pdo->beginTransaction();

    // Resolvemos cada id de catálogo por separado. Si alguno tiene más de
    // una fila, la excepción lo va a decir explícitamente (tabla y valor),
    // en vez de un "Cardinality violation" genérico sobre todo el INSERT.
    $id_tipo   = resolverIdCatalogo($pdo, 'tipos', 'id_tipo', 'tipo', $tipo);
    $id_marca  = resolverIdCatalogo($pdo, 'marcas', 'id_marca', 'marca', $marca);
    $id_escala = resolverIdCatalogo($pdo, 'escalas', 'id_escala', 'escala', $escala);

    if ($potencia !== '') {
        $pdo->prepare("INSERT IGNORE INTO potencias (valor_potencia) VALUES (?)")
            ->execute([$potencia]);
    }

    // El modelo depende de la marca: buscamos por modelo Y marca juntos.
    $stmt_modelo = $pdo->prepare(
        "SELECT id_modelo FROM modelos WHERE modelo_equipo = ? AND marca = ?"
    );
    $stmt_modelo->execute([$modelo, $id_marca]);
    $filas_modelo = $stmt_modelo->fetchAll(PDO::FETCH_COLUMN);

    if (count($filas_modelo) > 1) {
        throw new RuntimeException(
            "Hay más de un modelo '$modelo' para la marca '$marca' (ids: " .
            implode(',', $filas_modelo) . "). Hay que limpiar los duplicados."
        );
    }
    if (count($filas_modelo) === 1) {
        $id_modelo = (int)$filas_modelo[0];
    } else {
        $pdo->prepare("INSERT INTO modelos (modelo_equipo, marca) VALUES (?, ?)")
            ->execute([$modelo, $id_marca]);
        $id_modelo = (int)$pdo->lastInsertId();
    }

    // Ahora el INSERT a equipos usa valores YA RESUELTOS. Sin subconsultas
    // anidadas: si esto falla, el error va a ser sobre ESTA sentencia sola.
    $stmt_equipo = $pdo->prepare(
        "INSERT INTO equipos
            (numero_serie, tipo, marca, modelo, escala, sector, estado, ult_observacion, valor_potencia, nombre_plantilla)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    );
    $stmt_equipo->execute([
        $numero_serie, $id_tipo, $id_marca, $id_modelo, $id_escala,
        $sector, $estado, $observaciones, $potencia, $nombre_config
    ]);

    $id_equipo = (int)$pdo->lastInsertId();

    // ── Programación de canales (opcional) ──
    if (!empty($frecuencias)) {
        $pdo->prepare(
            "INSERT INTO programacion_canales
                (id_equipo, cantidad_canales, nombre_plantilla, usuario_programacion)
             VALUES (?, ?, ?, ?)"
        )->execute([$id_equipo, count($frecuencias), $nombre_config, $user['id']]);

        $id_programacion = (int)$pdo->lastInsertId();

        $stmt_canales = $pdo->prepare(
            "INSERT INTO canales_detalle
                (id_programacion, numero_canal, frecuencia_tx, frecuencia_rx, codificacion, codigo_squelch)
             VALUES (?, ?, ?, ?, ?, ?)"
        );

        foreach ($frecuencias as $i => $canal) {
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
    }

    $pdo->commit();

    sendSuccess(['id_equipo' => $id_equipo], "Equipo guardado exitosamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | alta_equipo | serie=" . ($numero_serie ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);

    // Temporal: mostramos el detalle para terminar de diagnosticar.
    // Volver al mensaje genérico una vez confirmado que funciona.
    sendError("DEBUG: " . $e->getMessage(), 500);
}