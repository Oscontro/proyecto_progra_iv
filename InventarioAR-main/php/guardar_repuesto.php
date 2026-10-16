<?php
// Alta de un repuesto en el catálogo, con sus modelos y el stock inicial por taller.
// Stock inicial: { talleres: { "<taller>": { stock } } }, o bien
// stock_aep / stock_eze (formato que manda el cliente de escritorio).
require_once 'repuestos_comun.php';
$user = requireAuth();

$numero_parte = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $numero_parte = trim((string)($datos['numero_parte'] ?? ''));
    $nombre       = trim((string)($datos['nombre'] ?? ''));
    $modelos      = $datos['modelos'] ?? [];
    $talleres     = $datos['talleres'] ?? null;

    if ($numero_parte === '') {
        sendError("Falta el número de parte", 400);
    }
    if ($nombre === '') {
        sendError("Falta el nombre del repuesto", 400);
    }
    if (!is_array($modelos) || !$modelos) {
        sendError("Vinculá al menos un modelo de equipo al repuesto", 400);
    }
    if (!is_array($talleres)) {
        $talleres = [
            'Aeroparque' => ['stock' => $datos['stock_aep'] ?? 0],
            'Ezeiza'     => ['stock' => $datos['stock_eze'] ?? 0],
        ];
    }

    $pdo = getConnection();

    // Validar todo antes de escribir nada.
    $ids_modelos = [];
    $stmt_modelo = $pdo->prepare("SELECT COUNT(*) FROM modelos WHERE id_modelo = ?");
    foreach ($modelos as $id_modelo) {
        $id_modelo = leerEntero($id_modelo, 'El modelo', 1);
        $stmt_modelo->execute([$id_modelo]);
        if ($stmt_modelo->fetchColumn() == 0) {
            sendError("No existe el modelo $id_modelo", 400);
        }
        $ids_modelos[$id_modelo] = true;
    }
    $stocks = [];
    foreach ($talleres as $nombre_taller => $info) {
        $stocks[] = [idTaller($pdo, $nombre_taller),
                     leerEntero($info['stock'] ?? 0, "El stock inicial de $nombre_taller", 0)];
    }

    $stmt_check = $pdo->prepare("SELECT COUNT(*) FROM repuestos WHERE numero_parte = ?");
    $stmt_check->execute([$numero_parte]);
    if ($stmt_check->fetchColumn() > 0) {
        sendError("Ya existe un repuesto con el número de parte $numero_parte", 409);
    }

    $pdo->beginTransaction();
    $pdo->prepare(
        "INSERT INTO repuestos (numero_parte, nombre, stock_actual, fecha_ingreso, id_usuario, en_uso)
         VALUES (?, ?, 0, NOW(), ?, 0)"
    )->execute([$numero_parte, $nombre, $user['id']]);
    $id_repuesto = (int)$pdo->lastInsertId();

    $stmt = $pdo->prepare("INSERT INTO modelo_repuesto (id_modelo, id_repuesto) VALUES (?, ?)");
    foreach (array_keys($ids_modelos) as $id_modelo) {
        $stmt->execute([$id_modelo, $id_repuesto]);
    }

    $stmt = $pdo->prepare(
        "INSERT INTO repuesto_stock (id_repuesto, id_taller, stock_actual, fuera_servicio, fecha_ingreso)
         VALUES (?, ?, ?, 0, NOW())");
    foreach ($stocks as [$id_taller, $stock]) {
        $stmt->execute([$id_repuesto, $id_taller, $stock]);
    }
    recalcularStockRepuesto($pdo, $id_repuesto);
    $pdo->commit();

    sendSuccess(['id_repuesto' => $id_repuesto], "Repuesto guardado exitosamente");

} catch (Throwable $e) {
    fallaRepuesto($e, "guardar_repuesto numero_parte=$numero_parte", null, $user,
                  "No se pudo guardar el repuesto. Intente nuevamente.");
}
