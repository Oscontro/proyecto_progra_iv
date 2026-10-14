<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$pdo = null;
$numero_serie = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $equipo        = $datos['equipo'] ?? [];
    $programacion  = $datos['frecuencias'] ?? [];
    $frecuencias   = $programacion['canales'] ?? [];

    $tipo             = $equipo['tipo'] ?? null;
    $marca            = $equipo['marca'] ?? null;
    $modelo_equipo    = $equipo['modelo_equipo'] ?? null;
    $numero_serie     = $equipo['numero_serie'] ?? null;
    $escala           = $equipo['escala'] ?? null;
    $sector           = $equipo['sector'] ?? null;
    $estado           = $equipo['estado'] ?? null;
    $valor_potencia   = $equipo['valor_potencia'] ?? null;
    $nombre_config    = !empty($equipo['nombre_plantilla']) ? $equipo['nombre_plantilla'] : null;
    $ult_observacion  = $equipo['observaciones'] ?? null;

    if (empty($numero_serie)) {
        sendError("numero_serie es obligatorio", 400);
        exit;
    }

    $pdo = getConnection();
    $pdo->beginTransaction();

    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    $sql = "UPDATE equipos e SET
            e.tipo = COALESCE((SELECT id_tipo FROM tipos WHERE tipo = NULLIF(:tipo, '')), e.tipo),
            e.marca = COALESCE((SELECT id_marca FROM marcas WHERE marca = NULLIF(:marca, '')), e.marca),
            e.modelo = COALESCE((SELECT id_modelo FROM modelos WHERE modelo_equipo = NULLIF(:modelo_equipo, '')), e.modelo),
            e.escala = COALESCE((SELECT id_escala FROM escalas WHERE escala = NULLIF(:escala, '')), e.escala),
            e.sector = COALESCE(NULLIF(:sector, ''), e.sector),
            e.estado = COALESCE(NULLIF(:estado, ''), e.estado),
            e.valor_potencia = NULLIF(:valor_potencia, ''),
            e.nombre_plantilla = NULLIF(:nombre_plantilla, ''),
            e.ult_observacion = NULLIF(:ult_observacion, '')
            WHERE e.numero_serie = :numero_serie";

    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(":tipo", $tipo);
    $stmt->bindParam(":marca", $marca);
    $stmt->bindParam(":modelo_equipo", $modelo_equipo);
    $stmt->bindParam(":numero_serie", $numero_serie);
    $stmt->bindParam(":escala", $escala);
    $stmt->bindParam(":sector", $sector);
    $stmt->bindParam(":estado", $estado);
    $stmt->bindParam(":valor_potencia", $valor_potencia);
    $stmt->bindParam(":nombre_plantilla", $nombre_config);
    $stmt->bindParam(":ult_observacion", $ult_observacion);
    $stmt->execute();

    $rowsAffected = $stmt->rowCount();

    // Buscar el id_equipo correspondiente al numero_serie
    $stmt_id = $pdo->prepare("SELECT id_equipo FROM equipos WHERE numero_serie = ?");
    $stmt_id->execute([$numero_serie]);
    $id_equipo = $stmt_id->fetchColumn();

    if ($id_equipo === false) {
        $pdo->rollBack();
        sendError("No se encontró el equipo con numero_serie=$numero_serie", 404);
        exit;
    }

    // ── Programación de canales (opcional) ──
    // IMPORTANTE: esto es una MODIFICACIÓN, no un alta. Si el equipo ya tenía
    // una programación cargada, hay que reemplazarla, no acumular una nueva
    // cabecera cada vez que se guarda. Borramos la programación anterior de
    // este equipo antes de insertar la nueva.
    if (!empty($frecuencias)) {

        // canales_detalle depende de programacion_canales por id_programacion.
        // Si no tenés ON DELETE CASCADE configurado entre esas tablas, hay que
        // borrar primero los detalles y después la(s) cabecera(s) a mano:
        $stmt_borrar_detalle = $pdo->prepare(
            "DELETE cd FROM canales_detalle cd
             JOIN programacion_canales pc ON pc.id_programacion = cd.id_programacion
             WHERE pc.id_equipo = ?"
        );
        $stmt_borrar_detalle->execute([$id_equipo]);

        $pdo->prepare("DELETE FROM programacion_canales WHERE id_equipo = ?")
            ->execute([$id_equipo]);


        $pdo->prepare(
            "INSERT INTO programacion_canales
                (id_equipo, cantidad_canales, nombre_plantilla, usuario_programacion)
             VALUES (?, ?, ?, ?)"
        )->execute([$id_equipo, count($frecuencias), $nombre_config, $user['id']]);

        $id_programacion = (int)$pdo->lastInsertId();

        $stmt_canales = $pdo->prepare(
            "INSERT INTO canales_detalle
                (id_programacion, numero_canal, frecuencia_tx, frecuencia_rx, codificacion, codigo_squelch)
             VALUES (?, ?, ?, ?, ?, ?)"
        );

        foreach ($frecuencias as $i => $canal) {
            if (!isset($canal['numero_canal'])) {
                throw new RuntimeException("El canal en la posición $i no tiene numero_canal");
            }
            $stmt_canales->execute([
                $id_programacion,
                $canal['numero_canal'],
                $canal['frecuencia_tx']  ?? null,
                $canal['frecuencia_rx']  ?? null,
                $canal['codificacion']   ?? null,
                $canal['codigo_squelch'] ?? null,
            ]);
        }
    }

    $pdo->commit();

    if ($rowsAffected > 0 || !empty($frecuencias)) {
        sendSuccess(['numero_serie' => $numero_serie], "Equipo modificado correctamente");
    } else {
        sendSuccess(['numero_serie' => $numero_serie], "No hubo cambios que aplicar");
    }

} catch (Throwable $e) {
    if ($pdo instanceof PDO && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $linea = date('Y-m-d H:i:s') . " | modi_equipo | serie=" . ($numero_serie ?? 'N/A')
           . " | usuario=" . ($user['id'] ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);
    sendError("No se pudo modificar el equipo. Intente nuevamente.", 500);
}