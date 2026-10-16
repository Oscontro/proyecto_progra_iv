<?php
require_once 'equipos_comun.php';   // trae auth.php y conexion.php
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$pdo = null;
$numero_serie = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $equipo       = $datos['equipo'] ?? [];
    $programacion = $datos['frecuencias'] ?? [];
    $canales      = normalizarCanales((array)($programacion['canales'] ?? []));

    $id_equipo    = filter_var($equipo['id_equipo'] ?? null, FILTER_VALIDATE_INT);
    $tipo         = textoOpcional($equipo['tipo'] ?? null);
    $marca        = textoOpcional($equipo['marca'] ?? null);
    $modelo       = textoOpcional($equipo['modelo_equipo'] ?? null);
    $escala       = textoOpcional($equipo['escala'] ?? null);
    $sector       = textoOpcional($equipo['sector'] ?? null);
    $estado       = textoOpcional($equipo['estado'] ?? null);
    $observacion  = textoOpcional($equipo['observaciones'] ?? null);
    // Si no viene valor_potencia, la potencia guardada no se toca.
    $hay_potencia = array_key_exists('valor_potencia', $equipo);
    $potencia     = textoOpcional($equipo['valor_potencia'] ?? null);

    if (!$id_equipo) {
        sendError("Falta identificar el equipo", 400);
    }

    $pdo = getConnection();

    // ── El equipo tiene que existir y estar en el inventario activo ──
    $stmt = $pdo->prepare("SELECT id_equipo, numero_serie, tipo, marca, en_papelera, en_taller FROM equipos WHERE id_equipo = ?");
    $stmt->execute([$id_equipo]);
    $actual = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$actual) {
        sendError("No se encontró el equipo", 404);
    }
    if ($actual['en_papelera']) {
        sendError("El equipo está en la papelera: restáurelo antes de modificarlo", 409);
    }
    if ($actual['en_taller']) {
        sendError("El equipo está en taller: no se puede modificar hasta su egreso", 409);
    }
    $id_equipo    = (int)$actual['id_equipo'];
    $numero_serie = $actual['numero_serie'];

    // ── Catálogos: un valor desconocido es un error, no se ignora en silencio ──
    $buscar = function (string $sql, array $params) use ($pdo) {
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        $valor = $stmt->fetchColumn();
        return $valor === false ? null : (int)$valor;
    };

    $id_tipo = $tipo === null ? (int)$actual['tipo']
        : $buscar("SELECT id_tipo FROM tipos WHERE tipo = ?", [$tipo]);
    if ($id_tipo === null) {
        sendError("El tipo \"$tipo\" no existe", 400);
    }
    $id_marca = $marca === null ? (int)$actual['marca']
        : $buscar("SELECT id_marca FROM marcas WHERE marca = ?", [$marca]);
    if ($id_marca === null) {
        sendError("La marca \"$marca\" no existe", 400);
    }
    // El nombre de modelo puede repetirse entre marcas: se busca dentro de la marca y el tipo.
    $id_modelo = null;
    if ($modelo !== null) {
        $id_modelo = $buscar(
            "SELECT id_modelo FROM modelos WHERE modelo_equipo = ? AND marca = ? AND (tipo = ? OR tipo IS NULL)
              ORDER BY tipo IS NULL LIMIT 1",
            [$modelo, $id_marca, $id_tipo]);
        if ($id_modelo === null) {
            sendError("El modelo \"$modelo\" no corresponde a la marca y el tipo elegidos", 400);
        }
    } elseif ($tipo !== null || $marca !== null) {
        sendError("Debe elegir el modelo", 400);
    }
    $id_escala = null;
    if ($escala !== null) {
        $id_escala = $buscar("SELECT id_escala FROM escalas WHERE escala = ?", [$escala]);
        if ($id_escala === null) {
            sendError("La escala \"$escala\" no existe", 400);
        }
    }

    $pdo->beginTransaction();
    $antes = filaEquipo($pdo, (int)$id_equipo);

    $sets = [
        'tipo = :tipo',
        'marca = :marca',
        'modelo = COALESCE(:modelo, modelo)',
        'escala = COALESCE(:escala, escala)',
        'sector = COALESCE(:sector, sector)',
        'estado = COALESCE(:estado, estado)',
        'ult_observacion = :ult_observacion',
        'usuario_modificacion = :usuario',
    ];
    $params = [
        ':tipo' => $id_tipo, ':marca' => $id_marca, ':modelo' => $id_modelo, ':escala' => $id_escala,
        ':sector' => $sector, ':estado' => $estado, ':ult_observacion' => $observacion,
        ':usuario' => $user['id'], ':id_equipo' => $id_equipo,
    ];
    if ($hay_potencia) {
        $sets[] = 'valor_potencia = :valor_potencia';
        $params[':valor_potencia'] = $potencia;
    }

    // ── Programación de canales (opcional) ──
    // Es una MODIFICACIÓN: si el equipo ya tenía programación se reemplaza,
    // no se acumula una cabecera nueva en cada guardado. Sin canales, la
    // programación existente queda como está.
    if ($canales) {
        $nombre_plantilla = nombrePlantilla((array)$programacion['canales']);
        $sets[] = 'nombre_plantilla = :nombre_plantilla';
        $params[':nombre_plantilla'] = $nombre_plantilla;
    }

    $stmt = $pdo->prepare("UPDATE equipos SET " . implode(', ', $sets) . " WHERE id_equipo = :id_equipo");
    $stmt->execute($params);
    $rowsAffected = $stmt->rowCount();
    registrarCambiosEquipo($pdo, $antes, (int)$id_equipo, (int)$user['id']);

    if ($canales) {
        guardarProgramacion($pdo, $id_equipo, $canales, $nombre_plantilla, (int)$user['id']);
    }

    $pdo->commit();

    $cambios = $rowsAffected > 0 || (bool)$canales;
    sendSuccess(['numero_serie' => $numero_serie, 'cambios' => $cambios],
                $cambios ? "Equipo modificado correctamente" : "No hubo cambios que aplicar");

} catch (Throwable $e) {
    if ($pdo instanceof PDO && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | modi_equipo | serie=" . ($numero_serie ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : "No se pudo modificar el equipo. Intente nuevamente.", 500);
}
