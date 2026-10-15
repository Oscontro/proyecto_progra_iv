<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$pdo = null;
$numero_serie = null;

// Textos que el cliente de escritorio muestra en lugar de una plantilla real.
const PLANTILLA_PLACEHOLDERS = ['', 'Sin plantilla cargada', 'Equipo programado sin plantilla'];
const CODIFICACIONES = ['SQL', 'DPL', 'TPL'];

function textoOpcional($valor): ?string {
    $valor = trim((string)($valor ?? ''));
    return $valor === '' ? null : $valor;
}

// canales_detalle guarda las frecuencias como DECIMAL(10,3).
function frecuencia($valor, int $canal, string $campo): ?string {
    $valor = str_replace(',', '.', trim((string)($valor ?? '')));
    if ($valor === '') {
        return null;
    }
    if (!preg_match('/^\d{1,7}(\.\d{1,3})?$/', $valor)) {
        sendError("Canal $canal: la frecuencia $campo \"$valor\" no es válida (formato 000.000)", 400);
    }
    return $valor;
}

/** Valida y normaliza los canales que manda el cliente. */
function normalizarCanales(array $canales): array {
    $resultado = [];
    $vistos = [];
    foreach ($canales as $i => $canal) {
        $numero = filter_var($canal['numero_canal'] ?? null, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1, 'max_range' => 999]]);
        if ($numero === false) {
            sendError("El canal en la posición $i no tiene un número válido", 400);
        }
        if (isset($vistos[$numero])) {
            sendError("El canal $numero está repetido", 400);
        }
        $vistos[$numero] = true;

        // El escritorio manda "Ninguno" cuando no se marcó codificación.
        $codificacion = strtoupper(trim((string)($canal['codificacion'] ?? '')));
        if ($codificacion === '' || $codificacion === 'NINGUNO') {
            $codificacion = null;
        } elseif (!in_array($codificacion, CODIFICACIONES, true)) {
            sendError("Canal $numero: codificación \"$codificacion\" no válida", 400);
        }
        // El código solo tiene sentido para DPL y TPL.
        $codigo = in_array($codificacion, ['DPL', 'TPL'], true) ? textoOpcional($canal['codigo_squelch'] ?? null) : null;

        $resultado[] = [
            'numero_canal'   => $numero,
            'frecuencia_tx'  => frecuencia($canal['frecuencia_tx'] ?? null, $numero, 'TX'),
            'frecuencia_rx'  => frecuencia($canal['frecuencia_rx'] ?? null, $numero, 'RX'),
            'codificacion'   => $codificacion,
            'codigo_squelch' => $codigo !== null ? mb_substr($codigo, 0, 50) : null,
        ];
    }
    return $resultado;
}

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $equipo       = $datos['equipo'] ?? [];
    $programacion = $datos['frecuencias'] ?? [];
    $canales      = normalizarCanales((array)($programacion['canales'] ?? []));

    $id_equipo    = $equipo['id_equipo'] ?? null;
    $numero_serie = textoOpcional($equipo['numero_serie'] ?? null);
    $tipo         = textoOpcional($equipo['tipo'] ?? null);
    $marca        = textoOpcional($equipo['marca'] ?? null);
    $modelo       = textoOpcional($equipo['modelo_equipo'] ?? null);
    $escala       = textoOpcional($equipo['escala'] ?? null);
    $sector       = textoOpcional($equipo['sector'] ?? null);
    $estado       = textoOpcional($equipo['estado'] ?? null);
    $observacion  = textoOpcional($equipo['observaciones'] ?? null);
    // La web manda "valor_potencia"; el escritorio, "potencia". Si no viene
    // ninguna de las dos, la potencia guardada no se toca.
    $hay_potencia = array_key_exists('valor_potencia', $equipo) || array_key_exists('potencia', $equipo);
    $potencia     = textoOpcional($equipo['valor_potencia'] ?? $equipo['potencia'] ?? null);

    if (!$id_equipo && !$numero_serie) {
        sendError("Falta identificar el equipo", 400);
    }

    $pdo = getConnection();

    // ── El equipo tiene que existir y estar en el inventario activo ──
    $stmt = $id_equipo
        ? $pdo->prepare("SELECT id_equipo, numero_serie, tipo, marca, en_papelera, en_taller FROM equipos WHERE id_equipo = ?")
        : $pdo->prepare("SELECT id_equipo, numero_serie, tipo, marca, en_papelera, en_taller FROM equipos WHERE numero_serie = ?");
    $stmt->execute([$id_equipo ?: $numero_serie]);
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
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

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
        $nombre_plantilla = textoOpcional($programacion['canales'][0]['nombre_config'] ?? null);
        if (in_array((string)$nombre_plantilla, PLANTILLA_PLACEHOLDERS, true)) {
            $nombre_plantilla = null;
        }
        $sets[] = 'nombre_plantilla = :nombre_plantilla';
        $params[':nombre_plantilla'] = $nombre_plantilla;
    }

    $stmt = $pdo->prepare("UPDATE equipos SET " . implode(', ', $sets) . " WHERE id_equipo = :id_equipo");
    $stmt->execute($params);
    $rowsAffected = $stmt->rowCount();

    if ($canales) {
        // canales_detalle se borra en cascada con su cabecera.
        $pdo->prepare("DELETE FROM programacion_canales WHERE id_equipo = ?")->execute([$id_equipo]);

        $pdo->prepare(
            "INSERT INTO programacion_canales
                (id_equipo, cantidad_canales, nombre_plantilla, usuario_programacion)
             VALUES (?, ?, ?, ?)"
        )->execute([$id_equipo, count($canales), $nombre_plantilla, $user['id']]);

        $id_programacion = (int)$pdo->lastInsertId();

        $stmt_canales = $pdo->prepare(
            "INSERT INTO canales_detalle
                (id_programacion, numero_canal, frecuencia_tx, frecuencia_rx, codificacion, codigo_squelch)
             VALUES (?, ?, ?, ?, ?, ?)"
        );
        foreach ($canales as $canal) {
            $stmt_canales->execute([
                $id_programacion,
                $canal['numero_canal'],
                $canal['frecuencia_tx'],
                $canal['frecuencia_rx'],
                $canal['codificacion'],
                $canal['codigo_squelch'],
            ]);
        }
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
