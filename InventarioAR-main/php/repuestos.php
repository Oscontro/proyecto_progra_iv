<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $pdo = getConnection();

    // ── 1) Datos base del repuesto ──
    // Ajustá el nombre de la tabla y columnas a las reales.
    $repuestos = $pdo->query(
        "SELECT id_repuesto, numero_parte, nombre, descripcion, stock_actual
         FROM repuestos
         ORDER BY id_repuesto"
    )->fetchAll(PDO::FETCH_ASSOC);

    if (!$repuestos) {
        echo json_encode([], JSON_UNESCAPED_UNICODE);
        exit;
    }

    // ── 2) Modelos asociados a cada repuesto ──
    // Ajustá la tabla intermedia (asumo repuesto_modelo con id_repuesto, id_modelo).
    $stmt_modelos = $pdo->prepare(
        "SELECT id_modelo FROM modelo_repuesto WHERE id_repuesto = ?"
    );

    // ── 3) Stock por taller ──
    // Ajustá la tabla real (asumo stock_taller con id_repuesto, id_taller,
    // cantidad_actual, cantidad_reservada, fecha_ultimo_movimiento) y la
    // tabla de talleres (nombre_taller).
    $stmt_stock = $pdo->prepare(
        "SELECT t.taller,
                rs.stock_actual,
                rs.fuera_servicio,
                rs.fecha_ingreso
         FROM repuesto_stock rs
         JOIN talleres t ON t.id_taller = rs.id_taller
         WHERE rs.id_repuesto = ?"
    );

    // ── 4) Cantidad de equipos que usan ese repuesto actualmente ──
    // Ajustá según cómo relaciones repuesto con equipos en uso.
    $stmt_en_uso = $pdo->prepare(
        "SELECT COUNT(*) FROM repuestos
         WHERE id_repuesto = ? AND en_uso > 0"
    );

    // ── Armar el resultado final, un elemento por repuesto ──
    $resultado = [];

    foreach ($repuestos as $r) {
        $id = $r['id_repuesto'];

        // Modelos: lista simple de ids.
        $stmt_modelos->execute([$id]);
        $modelos = $stmt_modelos->fetchAll(PDO::FETCH_COLUMN);

        // Talleres: diccionario {nombre_taller: {...}}.
        $stmt_stock->execute([$id]);
        $filas_stock = $stmt_stock->fetchAll(PDO::FETCH_ASSOC);

        $talleres = [];
        foreach ($filas_stock as $fila) {
            $talleres[$fila['taller']] = [
                'stock_actual'    => (int)$fila['stock_actual'],
                'fuera_servicio' => (int)$fila['fuera_servicio'],
                'fecha_ingreso' => $fila['fecha_ingreso'],
            ];
        }

        // En uso: cantidad de equipos activos con ese repuesto.
        $stmt_en_uso = $pdo->prepare("SELECT en_uso FROM repuestos WHERE id_repuesto = ? ");
        $stmt_en_uso->execute([$id]);

        // 'EN USO' FUNCIONALIDAD FUTURA PARA AGREGAR
        $en_uso = (int)$stmt_en_uso->fetchColumn();
        
        $resultado[] = [
            'id_repuesto'   => (int)$r['id_repuesto'],
            'numero_parte'  => $r['numero_parte'],
            'nombre'        => $r['nombre'],
            'descripcion'   => $r['descripcion'],
            'stock_actual' => (int)$r['stock_actual'],
            'modelos'       => array_map('intval', $modelos),
            'en_uso'        => $en_uso,
            'talleres'      => $talleres,
        ];
    }

    echo json_encode($resultado, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | repuestos | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener repuestos", 500);
}