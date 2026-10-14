<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';
$numero_serie = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $tipo          = $datos['tipo'] ?? null;
    $marca         = $datos['marca'] ?? null;
    $modelo        = $datos['modelo'] ?? null;
    $numero_serie  = $datos['numero_serie'] ?? null;
    $escala        = $datos['escala'] ?? null;
    $sector        = $datos['sector'] ?? null;
    $estado        = $datos['estado'] ?? null;
    $observaciones = $datos['ult_observacion'] ?? null;

    // Normalizar número de serie
    if (is_numeric($numero_serie)) {
        $numero_serie = number_format((float)$numero_serie, 0, '', '');
    }
    $numero_serie = strtoupper(trim(preg_replace('/\s+/', '', $numero_serie)));

    if (empty($numero_serie)) {
        sendError("El número de serie no puede estar vacío", 400);
    }

    $pdo = getConnection();
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    // Verificar duplicado ANTES de abrir la transacción.
    $stmt_check = $pdo->prepare("SELECT COUNT(*) FROM equipos WHERE numero_serie = ?");
    $stmt_check->execute([$numero_serie]);
    if ($stmt_check->fetchColumn() > 0) {
        $linea = date('Y-m-d H:i:s') . " | DUPLICADO | $numero_serie";
        @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
        sendError("Duplicado: $numero_serie", 400);
    }

    // ── Todo el proceso en una transacción ──
    // Si algo falla, no queremos catálogos a medio poblar ni equipos sueltos.
    $pdo->beginTransaction();

    $pdo->exec("CREATE TEMPORARY TABLE IF NOT EXISTS temp_equipos (
        tipo VARCHAR(100), marca VARCHAR(100), modelo VARCHAR(150),
        numero_serie VARCHAR(255), escala VARCHAR(3), sector VARCHAR(100),
        estado VARCHAR(100), ult_observacion VARCHAR(255)
    )");

    $stmt = $pdo->prepare(
        "INSERT INTO temp_equipos
            (tipo, marca, modelo, numero_serie, escala, sector, estado, ult_observacion)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    );
    $stmt->execute([$tipo, $marca, $modelo, $numero_serie, $escala, $sector, $estado, $observaciones]);

    // Poblar catálogos con los valores nuevos.
    $pdo->exec("INSERT INTO tipos (tipo)
                SELECT DISTINCT tipo FROM temp_equipos
                WHERE tipo NOT IN (SELECT tipo FROM tipos)");

    $pdo->exec("INSERT INTO marcas (marca)
                SELECT DISTINCT marca FROM temp_equipos
                WHERE marca NOT IN (SELECT marca FROM marcas)");

    $pdo->exec("INSERT INTO modelos (modelo_equipo, marca)
                SELECT DISTINCT te.modelo, m.id_marca
                FROM temp_equipos te
                INNER JOIN marcas m ON m.marca = te.marca
                WHERE te.modelo NOT IN (SELECT modelo_equipo FROM modelos)");

    $pdo->exec("INSERT INTO escalas (escala)
                SELECT DISTINCT escala FROM temp_equipos
                WHERE escala NOT IN (SELECT escala FROM escalas)");

    // Insertar los equipos resolviendo los ids de catálogo.
    $pdo->exec("INSERT INTO equipos
                    (numero_serie, tipo, marca, modelo, escala, sector, estado, ult_observacion)
                SELECT
                    te.numero_serie,
                    (SELECT id_tipo   FROM tipos   WHERE tipo = te.tipo),
                    (SELECT id_marca  FROM marcas  WHERE marca = te.marca),
                    (SELECT id_modelo FROM modelos WHERE modelo_equipo = te.modelo),
                    (SELECT id_escala FROM escalas WHERE escala = te.escala),
                    te.sector, te.estado, te.ult_observacion
                FROM temp_equipos te");

    $pdo->exec("DROP TEMPORARY TABLE temp_equipos");

    $pdo->commit();

    sendSuccess(['guardado' => true], "Equipo guardado exitosamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | EXCEPCION | " . ($numero_serie ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("No se pudo guardar el equipo. Intente nuevamente.", 500);
}