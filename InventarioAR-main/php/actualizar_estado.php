<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$id_equipo = null;

try {
    // Cuerpo JSON (ApiClient y frontend web); $_POST queda como respaldo.
    $datos = getJsonInput() ?: $_POST;

    $id        = $datos['id'] ?? null;
    $id_equipo = $datos['id_equipo'] ?? null;
    $estado    = $datos['estado'] ?? null;

    if (!$id_equipo || !$id || !$estado) {
        sendError("Faltan parámetros", 400);
    }

    $pdo = getConnection();

    // Primero verificá que el estado exista
    $stmtCheck = $pdo->prepare("SELECT id_estado FROM estados_taller WHERE estado = :estado");
    $stmtCheck->execute([':estado' => $estado]);
    $estadoRow = $stmtCheck->fetch();

    if (!$estadoRow) {
        sendError("El estado '$estado' no existe en estados_taller", 400);
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

    // Ojo: rowCount() es 0 también si el estado ya era el mismo, por eso
    // se comprueba la existencia del registro en vez de las filas cambiadas.
    $stmtExiste = $pdo->prepare("SELECT 1 FROM equipo_estado WHERE id_equipo = ? AND id = ?");
    $stmtExiste->execute([$id_equipo, $id]);
    if (!$stmtExiste->fetchColumn()) {
        sendError("No se encontró registro con id=$id e id_equipo=$id_equipo en equipo_estado", 404);
    }

    sendSuccess(["rows" => $stmt->rowCount()], "Se actualizó correctamente");

} catch (PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | usuario=" . $user['id'] . " | actualizar_estado | "
           . ($id_equipo ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : "Error al actualizar el estado", 500);
}
