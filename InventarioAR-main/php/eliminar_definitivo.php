<?php
// Elimina DEFINITIVAMENTE un equipo o vehículo de la base (solo admin).
// Solo se puede eliminar algo que esté en la papelera: nunca un ítem activo.
// Ojo: el borrado arrastra en cascada su historial, observaciones, etc.
require_once 'auth.php';
$user = requireAdmin();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$origen = null;
$id_referencia = null;
$numero_serie = null;

try {
    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);

    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $origen         = $datos['origen'] ?? null;
    $id_referencia  = $datos['id_referencia'] ?? null;
    $numero_serie   = $datos['numero_serie'] ?? null;

    if (!$id_referencia || $numero_serie === null || $numero_serie === '') {
        sendError("Falta el id o el número de serie", 400);
    }

    if ($origen === 'equipo') {
        $tabla = 'equipos';
        $sqlBuscar = "SELECT en_papelera FROM equipos WHERE id_equipo = ? AND numero_serie = ?";
        $sqlBorrar = "DELETE FROM equipos WHERE id_equipo = ? AND numero_serie = ? AND en_papelera = 1";
        $nombre = 'equipo';
    } elseif ($origen === 'vehiculo') {
        $tabla = 'vehiculos';
        $sqlBuscar = "SELECT de_baja FROM vehiculos WHERE id_vehiculo = ? AND identificacion = ?";
        $sqlBorrar = "DELETE FROM vehiculos WHERE id_vehiculo = ? AND identificacion = ? AND de_baja = 1";
        $nombre = 'vehículo';
    } else {
        sendError("Origen inválido", 400);
    }

    $stmt = $pdo->prepare($sqlBuscar);
    $stmt->execute([$id_referencia, $numero_serie]);
    $enPapelera = $stmt->fetchColumn();

    if ($enPapelera === false) {
        sendError("No se encontró el $nombre con el id y número de serie proporcionados", 404);
    }
    if (!$enPapelera) {
        sendError("Solo se pueden eliminar definitivamente ítems que estén en la papelera", 409);
    }

    // La condición de papelera se repite en el DELETE por si cambió entre las dos consultas.
    $stmt = $pdo->prepare($sqlBorrar);
    $stmt->execute([$id_referencia, $numero_serie]);
    if ($stmt->rowCount() === 0) {
        sendError("El $nombre ya no está en la papelera", 409);
    }

    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id'] . " | eliminar_definitivo | "
           . "$tabla id=$id_referencia serie=$numero_serie";
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);

    sendSuccess(['dado_de_baja' => true], ucfirst($nombre) . " eliminado correctamente");

} catch (PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | usuario=" . $user['id'] . " | eliminar_definitivo | "
           . ($origen ?? 'N/A') . " " . ($id_referencia ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);

    // 23000: otra tabla lo referencia con una restricción (p. ej. estados_taller).
    if ($e->getCode() === '23000') {
        sendError("No se puede eliminar: tiene registros asociados que lo impiden", 409);
    }
    sendError(API_DEBUG ? $e->getMessage() : "No se pudo eliminar, intente nuevamente", 500);
}
