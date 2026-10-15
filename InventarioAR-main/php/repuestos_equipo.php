<?php
// Repuestos del catálogo vinculados al modelo del equipo de un ingreso a
// taller, con el stock disponible en ESE taller. Lo usa el egreso de taller.
//   GET repuestos_equipo.php?id_ingreso=N
//   -> { id_taller, taller, repuestos: [{ id_repuesto, numero_parte, nombre, stock_taller }] }
require_once 'auth.php';
$user = requireAuth();

try {
    $id_ingreso = $_GET['id_ingreso'] ?? null;
    if (!$id_ingreso || !ctype_digit((string)$id_ingreso)) {
        sendError("Falta el ingreso a taller", 400);
    }

    $pdo = getConnection();
    $stmt = $pdo->prepare(
        "SELECT ti.taller AS id_taller, t.taller, e.modelo
           FROM taller_ingresos ti
           JOIN equipos e  ON e.id_equipo = ti.id_equipo
           JOIN talleres t ON t.id_taller = ti.taller
          WHERE ti.id_ingreso = ?");
    $stmt->execute([$id_ingreso]);
    $ingreso = $stmt->fetch();
    if (!$ingreso) {
        sendError("No existe el ingreso a taller", 404);
    }

    $stmt = $pdo->prepare(
        "SELECT r.id_repuesto, r.numero_parte, r.nombre,
                COALESCE(rs.stock_actual, 0) AS stock_taller
           FROM modelo_repuesto mr
           JOIN repuestos r ON r.id_repuesto = mr.id_repuesto
           LEFT JOIN repuesto_stock rs ON rs.id_repuesto = r.id_repuesto AND rs.id_taller = ?
          WHERE mr.id_modelo = ?
          ORDER BY r.nombre");
    $stmt->execute([$ingreso['id_taller'], $ingreso['modelo']]);
    $repuestos = array_map(fn($r) => [
        'id_repuesto'  => (int)$r['id_repuesto'],
        'numero_parte' => $r['numero_parte'],
        'nombre'       => $r['nombre'],
        'stock_taller' => (int)$r['stock_taller'],
    ], $stmt->fetchAll());

    sendSuccess([
        'id_taller' => (int)$ingreso['id_taller'],
        'taller'    => $ingreso['taller'],
        'repuestos' => $repuestos,
    ]);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | repuestos_equipo | " . $e->getMessage();
    @file_put_contents(__DIR__ . '/logs/errores_importacion.log', $linea . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener los repuestos del equipo", 500);
}
