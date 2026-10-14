<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

header('Content-Type: application/json');

$archivo_log = 'C:/xampp/htdocs/api/Programa Nuevo Base de datos/logs/errores_importacion.log';

try {
    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    $id = isset($_POST['id']) ? $_POST['id'] : null;
    $id_equipo = isset($_POST['id_equipo']) ? $_POST['id_equipo'] : null;
    $estado = isset($_POST['estado']) ? $_POST['estado'] : null;

    // Descomentá esto para validar
    if (!$id_equipo || !$id || !$estado) {
        echo json_encode([
            "success" => false, 
            "message" => "Faltan parámetros",
            "debug" => ["id" => $id, "id_equipo" => $id_equipo, "estado" => $estado]
        ]);
        exit;
    }

    // Primero verificá que el estado exista
    $stmtCheck = $pdo->prepare("SELECT id_estado FROM estados_taller WHERE estado = :estado");
    $stmtCheck->execute([':estado' => $estado]);
    $estadoRow = $stmtCheck->fetch();
    
    if (!$estadoRow) {
        echo json_encode([
            "success" => false, 
            "message" => "El estado '$estado' no existe en estados_taller"
        ]);
        exit;
    }

    $sql = "UPDATE equipo_estado
            SET id_estado = :id_estado
            WHERE id_equipo = :id_equipo AND id = :id";

    $stmt = $pdo->prepare($sql);
    $stmt->execute([
        ':id_estado' => $estadoRow['id_estado'],
        ':id_equipo' => $id_equipo,
        ':id' => $id
    ]);

    $rowsAffected = $stmt->rowCount();

    if ($rowsAffected === 0) {
        echo json_encode([
            "success" => false, 
            "message" => "No se encontró registro con id=$id e id_equipo=$id_equipo en equipo_estado"
        ]);
        exit;
    }

    echo json_encode(["success" => true, "message" => "Se actualizó correctamente", "rows" => $rowsAffected]);

} catch (PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | EXCEPCION | " . ($id_equipo ?? 'N/A') . " | " . $e->getMessage();
    file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
    echo json_encode(["success" => false, "message" => "Error: " . $e->getMessage()]);
    exit;
}