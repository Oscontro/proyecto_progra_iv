<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $datos =  getJsonInput();
       
    if (!$datos) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $nuevo_tipo = isset($datos['nuevo_tipo']) ? $datos['nuevo_tipo'] : null;
    $identificacion = isset($datos['identificacion']) ? $datos['identificacion'] : null;
    $nueva_escala = isset($datos['nueva_escala']) ? $datos['nueva_escala'] : null;
 
    $sql = "UPDATE vehiculos 
            SET tipo_vehiculo = :nuevo_tipo, escala = (SELECT id_escala FROM escalas WHERE escala = :nueva_escala)
            WHERE identificacion = :identificacion";
    
    $pdo = getConnection();
    // Configuraciones recomendadas para estabilidad y rendimiento
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);
    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(":nuevo_tipo", $nuevo_tipo);
    $stmt->bindParam(":nueva_escala", $nueva_escala);
    $stmt->bindParam(":identificacion", $identificacion);
    $stmt->execute();

    sendSuccess(["success" => true, "message" => "Vehículo actualizado correctamente"]);
    
} catch(PDOException $e) {
    sendError("Error: " . $e->getMessage(), 500);
    exit;
}