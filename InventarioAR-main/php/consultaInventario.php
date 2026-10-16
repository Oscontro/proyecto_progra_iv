<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    // Configuraciones recomendadas para estabilidad y rendimiento
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    $sql = "SELECT 
                id_equipo, 
                COALESCE(tipo, '') as tipo, 
                COALESCE(marca, '') as marca, 
                COALESCE(modelo_equipo, '') as modelo_equipo, 
                COALESCE(numero_serie, '') as numero_serie, 
                COALESCE(escala, '') as escala, 
                COALESCE(sector, '') as sector, 
                COALESCE(estado, '') as estado, 
                COALESCE(potencia, '') as potencia, 
                COALESCE(nombre_plantilla, 'Equipo programado sin plantilla') as nombre_plantilla, 
                COALESCE(ult_observacion, '') as ult_observacion
            FROM (
                -- Equipos en uso (ni en taller ni en la papelera). Era la vista
                -- vista_equipos_v4: el hosting no permite crear vistas.
                SELECT e.id_equipo, e.numero_serie, t.tipo, ma.marca, m.modelo_equipo, es.escala,
                       e.sector, e.estado, m.potencia, pc.nombre_plantilla, e.ult_observacion,
                       e.fecha_modificacion
                FROM equipos e
                LEFT JOIN programacion_canales pc ON pc.id_equipo = e.id_equipo
                LEFT JOIN modelos m  ON m.id_modelo  = e.modelo
                LEFT JOIN marcas ma  ON ma.id_marca  = m.marca
                LEFT JOIN escalas es ON es.id_escala = e.escala
                LEFT JOIN tipos t    ON t.id_tipo    = e.tipo
                WHERE e.en_papelera = 0 AND e.en_taller = 0
            ) AS equipos_en_uso
            ORDER BY fecha_modificacion DESC";
            
    $stmt = $pdo->prepare($sql);
    $stmt->execute(); 

    $equipos = $stmt->fetchAll(); 
    
    // Devolvemos el array puro para que el Front-end lo procese
    echo json_encode($equipos, JSON_UNESCAPED_UNICODE);
    
} catch(PDOException $e) {
    http_response_code(500);
    echo json_encode(["error" => "Error en la base de datos: " . $e->getMessage()]);
}
?>