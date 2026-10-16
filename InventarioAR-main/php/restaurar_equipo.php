<?php
require_once 'historial_comun.php';    // trae auth.php
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$id_equipo = null;

try {
    $pdo = getConnection();
    $datos = getJsonInput();

    if (!$datos) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $id_equipo = $datos['id_equipo'] ?? null;
    if (!$id_equipo) {
        sendError("Falta el id del equipo", 400);
    }

    $stmt = $pdo->prepare("SELECT en_papelera FROM equipos WHERE id_equipo = ?");
    $stmt->execute([$id_equipo]);
    $en_papelera = $stmt->fetchColumn();
    if ($en_papelera === false) {
        sendError("No existe el equipo", 404);
    }
    if (!$en_papelera) {
        sendError("El equipo no está en la papelera", 409);
    }

    // Antes era el procedimiento sp_restaurar_equipo_papelera (el hosting no
    // permite procedimientos).
    $pdo->beginTransaction();
    $antes = filaEquipo($pdo, (int)$id_equipo);
    $pdo->prepare("UPDATE equipos SET en_papelera = FALSE, usuario_modificacion = ? WHERE id_equipo = ?")
        ->execute([$user['id'], $id_equipo]);
    registrarCambiosEquipo($pdo, $antes, (int)$id_equipo, $user['id']);
    $pdo->prepare("UPDATE papelera SET puede_restaurar = FALSE WHERE id_equipo = ?")->execute([$id_equipo]);

    $pdo->commit();
    
    sendSuccess(["success" => true], "Se restauró equipo correctamente");

}  catch (Throwable $e) {
    // Solo hacemos rollback si efectivamente hay una transacción abierta.
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | restaurar_equipo_papelera | id_equipo=" . ($id_equipo ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);

    sendError("No se pudo restaurar equipo, intente nuevamente.", 500);
}