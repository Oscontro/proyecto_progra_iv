<?php
// Importación desde Excel del cliente de escritorio: un equipo por pedido,
// con los campos sueltos (sin el envoltorio "equipo" de alta_equipo.php).
//
// Usa la misma lógica que alta_equipo.php (equipos_comun.php). Antes tenía
// su propio circuito con una tabla temporal, que buscaba el modelo solo por
// nombre (fallaba si dos marcas tenían un modelo con el mismo nombre),
// creaba modelos sin tipo y convertía series como "0012345" en "12345".
// Los valores nuevos de catálogo se siguen creando sin preguntar, como
// espera el escritorio; la web importa con alta_equipo.php y confirma.
require_once 'equipos_comun.php';
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$numero_serie = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }
    $numero_serie = $datos['numero_serie'] ?? null;

    $pdo = getConnection();
    $resultado = altaEquipo($pdo, $user, $datos, [], true);

    sendSuccess(['guardado' => true, 'id_equipo' => $resultado['id_equipo']], "Equipo guardado exitosamente");

} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | ingreso_equipos | serie=" . ($numero_serie ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : "No se pudo guardar el equipo. Intente nuevamente.", 500);
}
