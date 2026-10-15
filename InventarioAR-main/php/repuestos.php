<?php
// Catálogo de repuestos con sus modelos, stock por taller y unidades en uso.
// Tres consultas en total (antes eran tres por cada repuesto).
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $pdo = getConnection();

    // ── 1) Datos base del repuesto ──
    $repuestos = $pdo->query(
        "SELECT id_repuesto, numero_parte, nombre, descripcion, stock_actual, en_uso
           FROM repuestos
          ORDER BY id_repuesto"
    )->fetchAll(PDO::FETCH_ASSOC);

    // ── 2) Modelos asociados a cada repuesto ──
    $modelos = [];
    $filas = $pdo->query(
        "SELECT id_repuesto, id_modelo FROM modelo_repuesto"
    )->fetchAll(PDO::FETCH_ASSOC);
    foreach ($filas as $fila) {
        $modelos[$fila['id_repuesto']][] = (int)$fila['id_modelo'];
    }

    // ── 3) Stock por taller ──
    $talleres = [];
    $filas = $pdo->query(
        "SELECT rs.id_repuesto, t.taller, rs.stock_actual, rs.fuera_servicio, rs.fecha_ingreso
           FROM repuesto_stock rs
           JOIN talleres t ON t.id_taller = rs.id_taller"
    )->fetchAll(PDO::FETCH_ASSOC);
    foreach ($filas as $fila) {
        $talleres[$fila['id_repuesto']][$fila['taller']] = [
            'stock_actual'   => (int)$fila['stock_actual'],
            'fuera_servicio' => (int)$fila['fuera_servicio'],
            'fecha_ingreso'  => $fila['fecha_ingreso'],
        ];
    }

    // ── Armar el resultado final, un elemento por repuesto ──
    $resultado = [];
    foreach ($repuestos as $r) {
        $id = $r['id_repuesto'];
        $resultado[] = [
            'id_repuesto'  => (int)$id,
            'numero_parte' => $r['numero_parte'],
            'nombre'       => $r['nombre'],
            'descripcion'  => $r['descripcion'],
            'stock_actual' => (int)$r['stock_actual'],
            'modelos'      => $modelos[$id] ?? [],
            'en_uso'       => (int)$r['en_uso'],
            'talleres'     => $talleres[$id] ?? [],
        ];
    }

    echo json_encode($resultado, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | repuestos | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener repuestos", 500);
}
