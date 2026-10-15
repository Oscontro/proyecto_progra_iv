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
            FROM vista_papelera_unificada
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