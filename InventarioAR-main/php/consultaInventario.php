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
            FROM vista_equipos_v4 
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