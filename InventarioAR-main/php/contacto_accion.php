<?php
// Acciones sobre una consulta de contacto (solo administradores):
//   { id_contacto, accion: "leido" | "no_leido" | "eliminar" }
require_once 'auth.php';
$user = requireAdmin();

const ACCIONES = ['leido', 'no_leido', 'eliminar'];

try {
    $datos = getJsonInput();
    $id = filter_var($datos['id_contacto'] ?? null, FILTER_VALIDATE_INT);
    $accion = $datos['accion'] ?? '';
    if (!$id || !in_array($accion, ACCIONES, true)) {
        sendError("Datos inválidos", 400);
    }

    $pdo = getConnection();
    $stmt = $accion === 'eliminar'
        ? $pdo->prepare("DELETE FROM contactos WHERE id_contacto = ?")
        : $pdo->prepare("UPDATE contactos SET leido = " . ($accion === 'leido' ? 1 : 0) . " WHERE id_contacto = ?");
    $stmt->execute([$id]);

    // rowCount es 0 también si ya tenía ese estado: se distingue "no existe".
    if ($stmt->rowCount() === 0) {
        $existe = $pdo->prepare("SELECT 1 FROM contactos WHERE id_contacto = ?");
        $existe->execute([$id]);
        if (!$existe->fetchColumn()) {
            sendError("La consulta no existe", 404);
        }
    }

    sendSuccess(['id_contacto' => $id, 'accion' => $accion],
                $accion === 'eliminar' ? "Consulta eliminada" : "Consulta actualizada");
} catch (Throwable $e) {
    @file_put_contents(__DIR__ . '/logs/errores_importacion.log',
        date('Y-m-d H:i:s') . " | usuario={$user['id']} | contacto_accion | " . $e->getMessage() . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : "No se pudo actualizar la consulta", 500);
}
