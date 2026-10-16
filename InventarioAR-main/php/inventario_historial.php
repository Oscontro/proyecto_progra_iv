<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    // Configuraciones recomendadas para estabilidad y rendimiento
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    $sql = "SELECT
                origen,
                id_referencia, 
                COALESCE(tipo, '') as tipo, 
                COALESCE(marca, '') as marca, 
                COALESCE(modelo_equipo, '') as modelo_equipo, 
                COALESCE(identificador, '') as numero_serie, 
                COALESCE(escala, '') as escala, 
                COALESCE(sector, '') as sector, 
                COALESCE(MAX(fecha_eliminacion), '') as fecha_eliminacion
            FROM (
                -- Equipos y vehículos en la papelera. Era la vista
                -- vista_papelera_unificada: el hosting no permite crear vistas.
                SELECT 'equipo' AS origen, e.id_equipo AS id_referencia, e.numero_serie AS identificador,
                       t.tipo, ma.marca, m.modelo_equipo, es.escala, e.sector, p.fecha_eliminacion
                FROM equipos e
                LEFT JOIN tipos t    ON t.id_tipo    = e.tipo
                LEFT JOIN modelos m  ON m.id_modelo  = e.modelo
                LEFT JOIN marcas ma  ON ma.id_marca  = m.marca
                LEFT JOIN escalas es ON es.id_escala = e.escala
                LEFT JOIN papelera p ON p.id_equipo  = e.id_equipo
                WHERE e.en_papelera = 1
                UNION ALL
                SELECT 'vehiculo', v.id_vehiculo, v.identificacion, v.tipo_vehiculo,
                       '', '', es.escala, '', pv.fecha_eliminacion
                FROM vehiculos v
                LEFT JOIN escalas es ON es.id_escala = v.escala
                LEFT JOIN papelera_vehiculos pv ON pv.id_vehiculo = v.id_vehiculo
                WHERE v.de_baja = 1
            ) AS papelera_unificada
            GROUP BY origen, id_referencia
            ORDER BY fecha_eliminacion DESC";
            
    $stmt = $pdo->prepare($sql);
    $stmt->execute(); 

    $datos = $stmt->fetchAll(); 
    
    // Devolvemos el array puro para que el Front-end lo procese
    echo json_encode($datos, JSON_UNESCAPED_UNICODE);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener la papelera", 500);
}
?>