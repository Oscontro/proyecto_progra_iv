<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 
header('Content-Type: application/json; charset=utf-8');

try {
    $pdo = getConnection();
    // Configuraciones recomendadas para estabilidad y rendimiento
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    $sql = "SELECT 
                tipo,
                marca,
                modelo_equipo,
                serie,
                taller,
                fecha_recepcion,
                COALESCE(fecha_ingreso, '-') AS fecha_ingreso,
                dias,
                estado_taller,
                observaciones,
                id_equipo,
                escala,
                sector,
                id_recepcion,
                id_ingreso,
                id AS id_estado,
                id_taller
            FROM (
                -- Equipos en el taller con su última recepción, ingreso, estado y
                -- observación. Era la vista vista_taller_v2: el hosting no permite
                -- crear vistas.
                SELECT STRAIGHT_JOIN
                       t.tipo, ma.marca, m.modelo_equipo, e.numero_serie AS serie, tal.taller,
                       tar.fecha_recepcion, tai.fecha_ingreso,
                       TO_DAYS(COALESCE(tae.fecha_egreso, CURDATE())) - TO_DAYS(tar.fecha_recepcion) AS dias,
                       est.estado AS estado_taller, obs.observacion AS observaciones, e.id_equipo,
                       es.escala, e.sector, tar.id_recepcion, tai.id_ingreso, esta.id, tal.id_taller
                FROM equipos e
                LEFT JOIN tipos t   ON t.id_tipo   = e.tipo
                LEFT JOIN marcas ma ON ma.id_marca = e.marca
                LEFT JOIN modelos m ON m.id_modelo = e.modelo
                LEFT JOIN taller_recepcion tar ON tar.id_equipo = e.id_equipo
                     AND tar.id_recepcion = (SELECT MAX(tr.id_recepcion) FROM taller_recepcion tr WHERE tr.id_equipo = e.id_equipo)
                LEFT JOIN talleres tal ON tal.id_taller = tar.id_taller
                LEFT JOIN taller_ingresos tai ON tai.id_equipo = e.id_equipo
                     AND tai.id_ingreso = (SELECT MAX(ti.id_ingreso) FROM taller_ingresos ti
                                           WHERE ti.id_equipo = e.id_equipo AND ti.fecha_ingreso >= tar.fecha_recepcion)
                LEFT JOIN taller_egresos tae ON tae.id_ingreso = tai.id_ingreso
                LEFT JOIN equipo_estado esta ON esta.id_equipo = e.id_equipo
                     AND esta.id = (SELECT MAX(ee.id) FROM equipo_estado ee WHERE ee.id_equipo = e.id_equipo)
                LEFT JOIN estados_taller est ON est.id_estado = esta.id_estado
                LEFT JOIN observaciones_taller obs ON obs.id_equipo = e.id_equipo
                     AND obs.id = (SELECT MAX(ot.id) FROM observaciones_taller ot WHERE ot.id_equipo = e.id_equipo)
                LEFT JOIN escalas es ON es.id_escala = e.escala
                WHERE e.en_taller = 1
            ) AS taller
            ORDER BY fecha_recepcion ASC";
            
    $stmt = $pdo->prepare($sql);
    $stmt->execute(); 

    $datos = $stmt->fetchAll(); 
    
    // Devolvemos el array puro para que el Front-end lo procese
    echo json_encode($datos, JSON_UNESCAPED_UNICODE);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener los equipos en taller", 500);
}
?>