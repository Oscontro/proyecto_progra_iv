<?php
require_once 'auth.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

// Columna de taller_egresos => nombre del repuesto (como en la tabla repuestos).
const REPUESTOS_EGRESO = [
    'repuesto_potenciometro' => 'POTENCIOMETRO',
    'repuesto_carcaza'       => 'CARCAZA',
    'repuesto_switch_ptt'    => 'SWITCH PTT',
    'repuesto_plastico_ptt'  => 'PLASTICO PTT',
    'repuesto_goma_ptt'      => 'GOMA PTT',
    'repuesto_display'       => 'DISPLAY',
    'repuesto_parlante'      => 'PARLANTE',
    'repuesto_microfono'     => 'MICROFONO',
    'repuesto_antena'        => 'ANTENA',
    'repuesto_bateria'       => 'BATERIA',
    'repuesto_clip_cintura'  => 'CLIP DE CINTURA',
    'repuesto_conector_rf'   => 'CONECTOR RF',
    'repuesto_otros'         => 'OTROS',
];

try {
    $pdo = getConnection();

    // Una fila por cada egreso de taller con el año, la escala y el modelo
    // del equipo, más las marcas de los repuestos utilizados.
    $columnas = implode(', ', array_map(fn($c) => "te.$c", array_keys(REPUESTOS_EGRESO)));
    $sql = "SELECT YEAR(te.fecha_egreso) AS anio,
                   es.escala,
                   mo.modelo_equipo AS modelo,
                   $columnas
            FROM taller_egresos te
            JOIN taller_ingresos ti ON ti.id_ingreso = te.id_ingreso
            JOIN equipos e          ON e.id_equipo   = ti.id_equipo
            JOIN modelos mo         ON mo.id_modelo  = e.modelo
            LEFT JOIN escalas es    ON es.id_escala  = e.escala
            WHERE te.fecha_egreso IS NOT NULL";

    // Se devuelve una fila por repuesto usado: {anio, escala, modelo, repuesto, cantidad}.
    // El agrupamiento (por año, escala, modelo) lo hace el cliente.
    $usos = [];

    // 1) Columnas fijas de taller_egresos (egresos viejos y "Otros"): cantidad 1.
    foreach ($pdo->query($sql) as $fila) {
        foreach (REPUESTOS_EGRESO as $columna => $nombre) {
            if (!empty($fila[$columna])) {
                $usos[] = [
                    'anio'     => (int)$fila['anio'],
                    'escala'   => $fila['escala'],
                    'modelo'   => $fila['modelo'],
                    'repuesto' => $nombre,
                    'cantidad' => 1,
                ];
            }
        }
    }

    // 2) Repuestos reales del catálogo con su cantidad (migración 2026-10-14).
    $sql_catalogo = "SELECT YEAR(te.fecha_egreso) AS anio,
                            es.escala,
                            mo.modelo_equipo AS modelo,
                            ter.nombre_repuesto AS repuesto,
                            ter.cantidad
                     FROM taller_egreso_repuestos ter
                     JOIN taller_egresos te  ON te.id_egreso  = ter.id_egreso
                     JOIN taller_ingresos ti ON ti.id_ingreso = te.id_ingreso
                     JOIN equipos e          ON e.id_equipo   = ti.id_equipo
                     JOIN modelos mo         ON mo.id_modelo  = e.modelo
                     LEFT JOIN escalas es    ON es.id_escala  = e.escala
                     WHERE te.fecha_egreso IS NOT NULL";
    foreach ($pdo->query($sql_catalogo) as $fila) {
        $usos[] = [
            'anio'     => (int)$fila['anio'],
            'escala'   => $fila['escala'],
            'modelo'   => $fila['modelo'],
            'repuesto' => $fila['repuesto'],
            'cantidad' => (int)$fila['cantidad'],
        ];
    }

    echo json_encode($usos, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    $linea = date('Y-m-d H:i:s') . " | estadistica_repuestos | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("Error al obtener el uso de repuestos", 500);
}
