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



    $numero_parte = $datos['numero_parte'] ?? null;
    $nombre = $datos['nombre'] ?? null;
    $stock_aep = $datos['stock_aep'] ?? null;
    $stock_eze  = $datos['stock_eze'] ?? null;
    $en_uso = (int)$datos['en_uso'] ?? 0;
    $stock_actual = $datos['stock_actual'] ?? null;

    $modelos = $datos['modelos'] ?? [];
    $talleres = $datos['talleres'] ?? [];

    $fecha = date('Y-m-d H:i:s');

    if (!$numero_parte) {
        sendError("Falta el número de parte", 400);
    }

    $pdo = getConnection();
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    $stmt_check = $pdo->prepare("SELECT COUNT(*) FROM repuestos WHERE numero_parte = ?");
    $stmt_check->execute([$numero_parte]);
    if ($stmt_check->fetchColumn() > 0) {
        sendError("Ya existe un repuesto con el número de parte $numero_parte", 400);
    }

    $pdo->beginTransaction();
    $stmt_repuesto = $pdo->prepare(
        "INSERT INTO repuestos
            (numero_parte, nombre, stock_actual, fecha_ingreso, id_usuario, en_uso)
         VALUES (?, ?, ?, ?, ?, ?)"
    );
    $stmt_repuesto->execute([
        $numero_parte, $nombre, $stock_actual, $fecha, $user['id'],
        $en_uso]);

    $id_repuesto = (int)$pdo->lastInsertId();

    $stmt_modelo_repuesto = $pdo->prepare(
        "INSERT INTO modelo_repuesto
            (id_modelo, id_repuesto)
         VALUES (?, ?)"
    );
    foreach ($modelos as $id_modelo) {
        $stmt_modelo_repuesto->execute([$id_modelo, $id_repuesto]);
    }

    $stmt_id_taller = $pdo->prepare("SELECT id_taller FROM talleres WHERE taller = ?");
    $stmt_stock = $pdo->prepare(
        "INSERT INTO repuesto_stock
            (id_repuesto, id_taller, stock_actual, fuera_servicio, fecha_ingreso)
         VALUES (?, ?, ?, ?, NOW())"
    );
 
    foreach ($talleres as $nombre_taller => $info) {
        $stmt_id_taller->execute([$nombre_taller]);
        $id_taller = $stmt_id_taller->fetchColumn();
 
        if ($id_taller === false) {
            throw new RuntimeException("Taller no encontrado: $nombre_taller");
        }
 
        $stmt_stock->execute([
            $id_repuesto,
            $id_taller,
            (int)($info['stock'] ?? 0),
            (int)($info['fuera_servicio'] ?? 0),
        ]);
    }
 
    $pdo->commit();
 
    sendSuccess(['id_repuesto' => $id_repuesto], "Repuesto guardado exitosamente");
 
} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | guardar_repuesto | numero_parte=" . ($numero_parte ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("No se pudo guardar el repuesto. Intente nuevamente.", 500);
}