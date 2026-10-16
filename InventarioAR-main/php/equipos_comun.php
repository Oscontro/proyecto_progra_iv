<?php
// Funciones compartidas por los endpoints de equipos: alta (alta_equipo.php)
// y modificación (modiEquipo.php).
//
// Catálogos:
//   tipos, marcas, escalas -> por nombre.
//   modelos               -> por nombre DENTRO de una marca, con su tipo.
//                            marcas.php ofrece las marcas de un tipo a partir
//                            de modelos.tipo: un modelo sin tipo no aparece en
//                            los desplegables, por eso se crea siempre con tipo.
require_once 'historial_comun.php';

const CODIFICACIONES = ['SQL', 'DPL', 'TPL'];

function textoOpcional($valor): ?string {
    $valor = trim((string)($valor ?? ''));
    return $valor === '' ? null : $valor;
}

/** Texto obligatorio con largo máximo; corta con 400 si falta o sobra. */
function textoObligatorio($valor, string $campo, int $maximo): string {
    // En los catálogos los espacios repetidos generarían valores "distintos".
    $valor = textoOpcional(preg_replace('/\s+/u', ' ', (string)($valor ?? '')));
    if ($valor === null) {
        sendError("Falta $campo", 400);
    }
    if (mb_strlen($valor) > $maximo) {
        sendError(ucfirst($campo) . " admite hasta $maximo caracteres", 400);
    }
    return $valor;
}

/**
 * N° de serie en MAYÚSCULAS y sin espacios. Si Excel lo convirtió en número
 * ("1.4002234E+7", "14002234.0") se recupera el entero; un serie numérico
 * común ("0012345") se deja como está, sin perder los ceros.
 */
function normalizarSerie($valor): string {
    $serie = strtoupper(preg_replace('/\s+/u', '', (string)($valor ?? '')));
    if (preg_match('/^\d+(\.\d+)?E\+?\d+$/', $serie) || preg_match('/^\d+\.0+$/', $serie)) {
        $serie = number_format((float)$serie, 0, '', '');
    }
    if ($serie === '') {
        sendError("Falta el número de serie", 400);
    }
    if (mb_strlen($serie) > 100) {
        sendError("El número de serie admite hasta 100 caracteres", 400);
    }
    return $serie;
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

        // Sin codificación: null (o vacío).
        $codificacion = strtoupper(trim((string)($canal['codificacion'] ?? '')));
        if ($codificacion === '') {
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

/** Nombre de la plantilla (nombre_config del primer canal), o null si no tiene. */
function nombrePlantilla(array $canales): ?string {
    $nombre = textoOpcional($canales[0]['nombre_config'] ?? null);
    return $nombre === null ? null : mb_substr($nombre, 0, 150);
}

/** Reemplaza la programación de canales de un equipo (canales ya normalizados). */
function guardarProgramacion(PDO $pdo, int $id_equipo, array $canales, ?string $nombre_plantilla, int $id_usuario): void {
    // canales_detalle se borra en cascada con su cabecera.
    $pdo->prepare("DELETE FROM programacion_canales WHERE id_equipo = ?")->execute([$id_equipo]);

    $pdo->prepare(
        "INSERT INTO programacion_canales
            (id_equipo, cantidad_canales, nombre_plantilla, usuario_programacion)
         VALUES (?, ?, ?, ?)"
    )->execute([$id_equipo, count($canales), $nombre_plantilla, $id_usuario]);
    $id_programacion = (int)$pdo->lastInsertId();

    $stmt = $pdo->prepare(
        "INSERT INTO canales_detalle
            (id_programacion, numero_canal, frecuencia_tx, frecuencia_rx, codificacion, codigo_squelch)
         VALUES (?, ?, ?, ?, ?, ?)"
    );
    foreach ($canales as $canal) {
        $stmt->execute([
            $id_programacion,
            $canal['numero_canal'],
            $canal['frecuencia_tx'],
            $canal['frecuencia_rx'],
            $canal['codificacion'],
            $canal['codigo_squelch'],
        ]);
    }
}

function buscarId(PDO $pdo, string $sql, array $params): ?int {
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $id = $stmt->fetchColumn();
    return $id === false || $id === null ? null : (int)$id;
}

/**
 * Alta de un equipo.
 *
 *   $equipo:       tipo, marca, modelo, numero_serie, escala, sector, estado,
 *                  potencia, ult_observacion
 *   $programacion: { canales: [...] } (opcional)
 *   $crearNuevos:  si es false y hay valores de catálogo que no existen, corta
 *                  con 409 (code CATALOGO_NUEVO) y la lista en "nuevos", para
 *                  que el usuario confirme antes de crearlos.
 *   $soloValidar:  valida todo y devuelve lo que se crearía, sin guardar.
 *
 * Devuelve ['id_equipo' => int|null, 'numero_serie' => string, 'nuevos' => [...]].
 */
function altaEquipo(PDO $pdo, array $user, array $equipo, array $programacion,
                    bool $crearNuevos, bool $soloValidar = false): array {
    $tipo     = textoObligatorio($equipo['tipo'] ?? null, 'el tipo', 100);
    $marca    = textoObligatorio($equipo['marca'] ?? null, 'la marca', 100);
    $modelo   = textoObligatorio($equipo['modelo'] ?? null, 'el modelo', 150);
    $serie    = normalizarSerie($equipo['numero_serie'] ?? null);
    $escala   = mb_strtoupper(textoObligatorio($equipo['escala'] ?? null, 'la escala', 3));
    $sector   = textoObligatorio($equipo['sector'] ?? null, 'el sector', 100);
    $estado   = textoObligatorio($equipo['estado'] ?? null, 'el estado', 100);
    $potencia = textoOpcional($equipo['potencia'] ?? null);
    $obs      = textoOpcional($equipo['ult_observacion'] ?? null);
    if ($potencia !== null && mb_strlen($potencia) > 50) {
        sendError("La potencia admite hasta 50 caracteres", 400);
    }
    if ($obs !== null && mb_strlen($obs) > 255) {
        sendError("Las observaciones admiten hasta 255 caracteres", 400);
    }
    $canales = normalizarCanales((array)($programacion['canales'] ?? []));
    $plantilla = nombrePlantilla((array)($programacion['canales'] ?? []));

    // ── N° de serie único (también contra los equipos en la papelera) ──
    $stmt = $pdo->prepare("SELECT en_papelera FROM equipos WHERE numero_serie = ?");
    $stmt->execute([$serie]);
    $existente = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($existente) {
        sendError("Ya existe un equipo con el número de serie $serie"
                  . ($existente['en_papelera'] ? ' (está en la papelera)' : ''), 409, ['code' => 'DUPLICADO']);
    }

    // ── Catálogos: qué existe y qué habría que crear ──
    $id_tipo   = buscarId($pdo, "SELECT MIN(id_tipo) FROM tipos WHERE tipo = ?", [$tipo]);
    $id_marca  = buscarId($pdo, "SELECT MIN(id_marca) FROM marcas WHERE marca = ?", [$marca]);
    $id_escala = buscarId($pdo, "SELECT MIN(id_escala) FROM escalas WHERE escala = ?", [$escala]);
    $id_modelo = null;
    $modelo_sin_tipo = false;
    if ($id_marca !== null) {
        $stmt = $pdo->prepare(
            "SELECT m.id_modelo, m.tipo, t.tipo AS nombre_tipo
               FROM modelos m LEFT JOIN tipos t ON t.id_tipo = m.tipo
              WHERE m.modelo_equipo = ? AND m.marca = ?
              ORDER BY m.id_modelo");
        $stmt->execute([$modelo, $id_marca]);
        $candidatos = $stmt->fetchAll(PDO::FETCH_ASSOC);
        foreach ($candidatos as $c) {
            if ($id_tipo !== null && (int)$c['tipo'] === $id_tipo) {
                $id_modelo = (int)$c['id_modelo'];
                break;
            }
        }
        if ($id_modelo === null) {
            foreach ($candidatos as $c) {
                if ($c['tipo'] === null) {            // modelo viejo sin tipo: se completa
                    $id_modelo = (int)$c['id_modelo'];
                    $modelo_sin_tipo = true;
                    break;
                }
            }
        }
        if ($id_modelo === null && $candidatos) {
            $tipos = implode(', ', array_unique(array_column($candidatos, 'nombre_tipo')));
            sendError("El modelo \"$modelo\" de $marca está registrado como tipo $tipos, no como $tipo", 400);
        }
    }

    $nuevos = [];
    if ($id_tipo === null)   $nuevos[] = ['catalogo' => 'tipo',   'valor' => $tipo];
    if ($id_marca === null)  $nuevos[] = ['catalogo' => 'marca',  'valor' => $marca];
    if ($id_modelo === null) $nuevos[] = ['catalogo' => 'modelo', 'valor' => $modelo, 'marca' => $marca, 'tipo' => $tipo];
    if ($id_escala === null) $nuevos[] = ['catalogo' => 'escala', 'valor' => $escala];

    if ($soloValidar) {
        return ['id_equipo' => null, 'numero_serie' => $serie, 'nuevos' => $nuevos];
    }
    if ($nuevos && !$crearNuevos) {
        $lista = implode(', ', array_map(fn($n) => "{$n['catalogo']} \"{$n['valor']}\"", $nuevos));
        sendError("Se van a crear valores nuevos en los catálogos: $lista", 409,
                  ['code' => 'CATALOGO_NUEVO', 'nuevos' => $nuevos]);
    }

    // ── Alta ──
    $pdo->beginTransaction();

    if ($id_tipo === null) {
        $pdo->prepare("INSERT INTO tipos (tipo, usuario_creacion) VALUES (?, ?)")->execute([$tipo, $user['id']]);
        $id_tipo = (int)$pdo->lastInsertId();
    }
    if ($id_marca === null) {
        $pdo->prepare("INSERT INTO marcas (marca, usuario_creacion) VALUES (?, ?)")->execute([$marca, $user['id']]);
        $id_marca = (int)$pdo->lastInsertId();
    }
    if ($id_escala === null) {
        $pdo->prepare("INSERT INTO escalas (escala, usuario_creacion) VALUES (?, ?)")->execute([$escala, $user['id']]);
        $id_escala = (int)$pdo->lastInsertId();
    }
    if ($id_modelo === null) {
        $pdo->prepare("INSERT INTO modelos (modelo_equipo, marca, tipo, potencia, usuario_creacion) VALUES (?, ?, ?, ?, ?)")
            ->execute([$modelo, $id_marca, $id_tipo, $potencia, $user['id']]);
        $id_modelo = (int)$pdo->lastInsertId();
    } elseif ($modelo_sin_tipo) {
        $pdo->prepare("UPDATE modelos SET tipo = ? WHERE id_modelo = ? AND tipo IS NULL")->execute([$id_tipo, $id_modelo]);
    }

    $pdo->prepare(
        "INSERT INTO equipos
            (numero_serie, tipo, marca, modelo, escala, sector, estado, ult_observacion,
             valor_potencia, nombre_plantilla, usuario_creacion)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )->execute([$serie, $id_tipo, $id_marca, $id_modelo, $id_escala, $sector, $estado, $obs,
                $potencia, $canales ? $plantilla : null, $user['id']]);
    $id_equipo = (int)$pdo->lastInsertId();
    registrarAltaEquipo($pdo, $id_equipo, (int)$user['id']);

    if ($canales) {
        guardarProgramacion($pdo, $id_equipo, $canales, $plantilla, (int)$user['id']);
    }

    $pdo->commit();
    return ['id_equipo' => $id_equipo, 'numero_serie' => $serie, 'nuevos' => $nuevos];
}
