<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAdmin(); 

try {
    $pdo = getConnection();
    // Configuraciones recomendadas para estabilidad y rendimiento
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    $sql = "SELECT 
                id_usuario, 
                legajo,
                username,
                nombre,
                apellido,
                email,
                IF(es_administrador = 1, 'Administrador', 'Técnico') AS perfil,
                IF(activo = 1, True, False) AS activo ,
                IF(debe_cambiar_clave = 1, False, True) AS debe_cambiar_clave ,
                fecha_ultima_conexion AS ultima_conexion
            FROM usuarios
            ORDER BY id_usuario";
            
    $stmt = $pdo->prepare($sql);
    $stmt->execute(); 

    $usuarios = $stmt->fetchAll(); 
    
    // Devolvemos el array puro para que el Front-end lo procese
    echo json_encode($usuarios, JSON_UNESCAPED_UNICODE);
    
} catch(PDOException $e) {
    http_response_code(500);
    echo json_encode(["error" => "Error en la base de datos: " . $e->getMessage()]);
}
?>