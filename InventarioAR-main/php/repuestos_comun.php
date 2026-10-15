<?php
// Funciones compartidas por los endpoints de repuestos.
//
// Modelo de datos:
//   repuesto_stock (id_repuesto, id_taller) -> stock_actual y fuera_servicio
//                                              POR TALLER (fuente de verdad).
//   repuestos.en_uso                        -> conteo general en uso.
//   repuestos.stock_actual                  -> total de stock (suma de los
//                                              talleres). Lo mantienen los
//                                              triggers trg_stock_taller_*
//                                              de repuesto_stock: no se toca
//                                              desde PHP.
require_once 'auth.php';

/** Entero >= $minimo, o corta con 400. */
function leerEntero($valor, string $campo, int $minimo = 0): int {
    if (!is_numeric($valor) || (int)$valor != $valor || (int)$valor < $minimo) {
        sendError("$campo tiene que ser un número entero mayor o igual a $minimo", 400);
    }
    return (int)$valor;
}

/** id_taller a partir del nombre ("Aeroparque", "Ezeiza"), o corta con 400. */
function idTaller(PDO $pdo, $nombre): int {
    if (!$nombre) {
        sendError("Falta el taller", 400);
    }
    $stmt = $pdo->prepare("SELECT id_taller FROM talleres WHERE taller = ?");
    $stmt->execute([$nombre]);
    $id = $stmt->fetchColumn();
    if ($id === false) {
        sendError("Taller no encontrado: $nombre", 400);
    }
    return (int)$id;
}

/** El repuesto tiene que existir, o corta con 404. */
function exigirRepuesto(PDO $pdo, $id_repuesto): int {
    if (!$id_repuesto) {
        sendError("Falta id_repuesto", 400);
    }
    $stmt = $pdo->prepare("SELECT COUNT(*) FROM repuestos WHERE id_repuesto = ?");
    $stmt->execute([$id_repuesto]);
    if ($stmt->fetchColumn() == 0) {
        sendError("No se encontró el repuesto con id_repuesto = $id_repuesto", 404);
    }
    return (int)$id_repuesto;
}

/** Crea la fila de stock del taller si no existe (todo en 0). */
function asegurarFilaStock(PDO $pdo, int $id_repuesto, int $id_taller): void {
    $pdo->prepare(
        "INSERT IGNORE INTO repuesto_stock (id_repuesto, id_taller, stock_actual, fuera_servicio)
         VALUES (?, ?, 0, 0)"
    )->execute([$id_repuesto, $id_taller]);
}

/** Registra el error en el log y responde 500 sin exponer el detalle. */
function fallaRepuesto(Throwable $e, string $operacion, $id_repuesto, ?array $user, string $mensaje): void {
    global $pdo;
    if (isset($pdo) && $pdo instanceof PDO && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | $operacion | id_repuesto=" . ($id_repuesto ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents(__DIR__ . '/logs/errores_importacion.log', $linea . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : $mensaje, 500);
}
