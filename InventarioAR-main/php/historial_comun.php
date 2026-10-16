<?php
// Historial de equipos y vehículos, y stock total de repuestos.
//
// Antes lo hacían triggers de la base (trg_equipos_after_insert,
// trg_equipos_after_update, trg_equipos_after_envio_taller,
// trg_taller_ingresos_after_insert, trg_taller_egresos_after_insert,
// trg_vehiculos_after_update y trg_stock_taller_after_*). El hosting gratuito
// no permite triggers, procedimientos ni vistas: la lógica vive acá y cada
// endpoint la llama dentro de su propia transacción.
//
// Uso para una modificación de equipos:
//   $antes = filaEquipo($pdo, $id);
//   UPDATE equipos ...
//   registrarCambiosEquipo($pdo, $antes, $id, $usuario);
require_once 'auth.php';

function registrarHistorialEquipo(PDO $pdo, int $id_equipo, ?int $usuario, string $tipo_evento,
                                  ?string $observaciones, ?string $campo = null,
                                  ?string $anterior = null, ?string $nuevo = null): void {
    $pdo->prepare(
        "INSERT INTO historial_equipos
            (id_equipo, usuario_evento, tipo_evento, campo_modificado, valor_anterior, valor_nuevo, observaciones)
         VALUES (?, ?, ?, ?, ?, ?, ?)"
    )->execute([$id_equipo, $usuario, $tipo_evento, $campo, $anterior, $nuevo, $observaciones]);
}

function registrarHistorialVehiculo(PDO $pdo, int $id_vehiculo, ?int $usuario, string $tipo_evento,
                                    ?string $observaciones): void {
    $pdo->prepare(
        "INSERT INTO historial_vehiculos (id_vehiculo, usuario_evento, tipo_evento, observaciones)
         VALUES (?, ?, ?, ?)"
    )->execute([$id_vehiculo, $usuario, $tipo_evento, $observaciones]);
}

/** Fila del equipo con los nombres de sus catálogos, para comparar antes/después. */
function filaEquipo(PDO $pdo, int $id_equipo): ?array {
    $stmt = $pdo->prepare(
        "SELECT e.id_equipo, e.numero_serie, e.tipo, e.marca, e.modelo, e.escala, e.sector, e.estado,
                e.en_papelera, e.en_taller, e.fecha_ingreso,
                t.tipo AS tipo_nombre, ma.marca AS marca_nombre, m.modelo_equipo AS modelo_nombre,
                es.escala AS escala_nombre, et.estado AS estado_taller
           FROM equipos e
           LEFT JOIN tipos t    ON t.id_tipo    = e.tipo
           LEFT JOIN marcas ma  ON ma.id_marca  = e.marca
           LEFT JOIN modelos m  ON m.id_modelo  = e.modelo
           LEFT JOIN escalas es ON es.id_escala = e.escala
           LEFT JOIN estados_taller et ON et.id_estado = e.id_estado
          WHERE e.id_equipo = ?");
    $stmt->execute([$id_equipo]);
    return $stmt->fetch(PDO::FETCH_ASSOC) ?: null;
}

/** Alta de un equipo: evento ALTA_EQUIPO y observación de sistema. */
function registrarAltaEquipo(PDO $pdo, int $id_equipo, ?int $usuario): void {
    $e = filaEquipo($pdo, $id_equipo);
    registrarHistorialEquipo($pdo, $id_equipo, $usuario, 'ALTA_EQUIPO',
        "Equipo creado: {$e['numero_serie']} - {$e['marca_nombre']} {$e['modelo_nombre']}");
    $pdo->prepare(
        "INSERT INTO observaciones_equipos (id_equipo, usuario_observacion, texto_observacion, tipo_observacion)
         VALUES (?, ?, ?, 'SISTEMA')"
    )->execute([$id_equipo, $usuario,
                'Equipo ingresado al sistema el ' . date('d/m/Y H:i', strtotime($e['fecha_ingreso']))]);
}

/** Igual que la comparación de la base (collation _ci): sin distinguir mayúsculas. */
function textoCambio(?string $antes, ?string $despues): bool {
    return mb_strtolower((string)$antes) !== mb_strtolower((string)$despues);
}

/** Registra en el historial lo que cambió del equipo entre $antes y su estado actual. */
function registrarCambiosEquipo(PDO $pdo, array $antes, int $id_equipo, ?int $usuario): void {
    $despues = filaEquipo($pdo, $id_equipo);

    if (!$antes['en_taller'] && $despues['en_taller']) {
        registrarHistorialEquipo($pdo, $id_equipo, $usuario, 'ENVIADO_A_TALLER',
            'Equipo enviado a taller: ' . ($despues['estado_taller'] ?? 'Sin especificar'));
    }

    // Catálogos: se registra el nombre, no el id.
    $catalogos = [
        'tipo' => ['CAMBIO_TIPO', 'Tipo cambiado'], 'marca' => ['CAMBIO_MARCA', 'Marca cambiada'],
        'modelo' => ['CAMBIO_MODELO', 'Modelo cambiado'], 'escala' => ['CAMBIO_ESCALA', 'Escala cambiada'],
    ];
    foreach ($catalogos as $campo => [$evento, $titulo]) {
        if ((int)$antes[$campo] !== (int)$despues[$campo]) {
            $de = $antes["{$campo}_nombre"];
            $a  = $despues["{$campo}_nombre"];
            registrarHistorialEquipo($pdo, $id_equipo, $usuario, $evento,
                "$titulo de \"$de\" a \"$a\"", $campo, $de, $a);
        }
    }
    foreach (['sector' => ['CAMBIO_SECTOR', 'Sector'], 'estado' => ['CAMBIO_ESTADO', 'Estado']] as $campo => [$evento, $titulo]) {
        if (textoCambio($antes[$campo], $despues[$campo])) {
            registrarHistorialEquipo($pdo, $id_equipo, $usuario, $evento,
                "$titulo cambiado de \"{$antes[$campo]}\" a \"{$despues[$campo]}\"",
                $campo, $antes[$campo], $despues[$campo]);
        }
    }

    if (!$antes['en_papelera'] && $despues['en_papelera']) {
        registrarHistorialEquipo($pdo, $id_equipo, $usuario, 'ENVIADO_PAPELERA', 'Equipo enviado a la papelera');
    }
    if ($antes['en_papelera'] && !$despues['en_papelera']) {
        registrarHistorialEquipo($pdo, $id_equipo, $usuario, 'RESTAURADO_PAPELERA', 'Equipo restaurado desde la papelera');
    }
}

/** repuestos.stock_actual es la suma del stock de todos los talleres. */
function recalcularStockRepuesto(PDO $pdo, int $id_repuesto): void {
    $pdo->prepare(
        "UPDATE repuestos
            SET stock_actual = (SELECT COALESCE(SUM(stock_actual), 0) FROM repuesto_stock WHERE id_repuesto = ?)
          WHERE id_repuesto = ?"
    )->execute([$id_repuesto, $id_repuesto]);
}
