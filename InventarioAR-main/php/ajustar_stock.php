<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';
$id_repuesto = null;
$en_uso = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $id_repuesto = $datos['id_repuesto'] ?? null;
    $en_uso      = $datos['en_uso'] ?? null;
    $talleres    = $datos['talleres'] ?? [];

    if (!$id_repuesto) {
        sendError("Falta id_repuesto", 400);
    }

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $stmt_existe = $pdo->prepare("SELECT COUNT(*) FROM repuestos WHERE id_repuesto = ?");
    $stmt_existe->execute([$id_repuesto]);
    if ($stmt_existe->fetchColumn() == 0) {
        sendError("No se encontró el repuesto con id_repuesto = $id_repuesto", 404);
    }

    $pdo->beginTransaction();

    $pdo->prepare(
        "UPDATE repuestos SET en_uso = ? WHERE id_repuesto = ?"
    )->execute([$en_uso, $id_repuesto]);

    $stmt_id_taller = $pdo->prepare("SELECT id_taller FROM talleres WHERE taller = ?");
    $stmt_stock_existe = $pdo->prepare(
        "SELECT COUNT(*) FROM repuesto_stock WHERE id_repuesto = ? AND id_taller = ?"
    );

    // Los ? están en el mismo orden en que se pasan los valores:
    // stock_actual, fuera_servicio, id_repuesto, id_taller.
    $stmt_update_stock = $pdo->prepare(
        "UPDATE repuesto_stock
            SET stock_actual = ?,
                fuera_servicio = ?,
                fecha_ingreso = NOW()
          WHERE id_repuesto = ? AND id_taller = ?"
    );
    $stmt_insert_stock = $pdo->prepare(
        "INSERT INTO repuesto_stock (id_repuesto, id_taller, stock_actual, fuera_servicio, fecha_ingreso)
         VALUES (?, ?, ?, ?, NOW())"
    );

    foreach ($talleres as $nombre_taller => $info) {
        $stmt_id_taller->execute([$nombre_taller]);
        $id_taller = $stmt_id_taller->fetchColumn();

        if ($id_taller === false) {
            throw new RuntimeException("Taller no encontrado: $nombre_taller");
        }

        $stock_actual   = (int)($info['stock'] ?? 0);
        $fuera_servicio = (int)($info['fuera_servicio'] ?? 0);
        // fecha_ingreso NO se lee del payload: siempre NOW() del servidor,
        // igual que en el alta. No confiamos en la fecha/hora del cliente.

        $stmt_stock_existe->execute([$id_repuesto, $id_taller]);
        if ($stmt_stock_existe->fetchColumn() > 0) {
            $stmt_update_stock->execute([
                $stock_actual,
                $fuera_servicio,
                $id_repuesto,
                $id_taller,
            ]);
        } else {
            $stmt_insert_stock->execute([
                $id_repuesto,
                $id_taller,
                $stock_actual,
                $fuera_servicio,
            ]);
        }
    }

    $pdo->commit();

    sendSuccess(['id_repuesto' => (int)$id_repuesto], "Repuesto actualizado correctamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | modificar_repuesto | id_repuesto=" . ($id_repuesto ?? 'N/A')
           . " | en_uso=" . ($en_uso ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("Error: " . $e->getMessage(), 500);
}