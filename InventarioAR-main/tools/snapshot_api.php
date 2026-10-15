<?php
/**
 * Captura y compara respuestas de los endpoints de LECTURA de la API.
 * Sirve como red de seguridad durante la migración: se captura una
 * línea base antes de un cambio, otra después, y se comparan.
 *
 * Uso (desde la carpeta InventarioAR-main):
 *   php tools/snapshot_api.php capturar <carpeta_salida>
 *   php tools/snapshot_api.php comparar <carpeta_a> <carpeta_b>
 *
 * Variables de entorno para "capturar":
 *   API_BASE   URL base de la API (por defecto http://localhost/proyecto_progra_iv/InventarioAR-main/php)
 *   API_USER / API_PASS  usuario administrador: se ingresa por web/ingresar.php
 *              (formulario con token CSRF) y se usa la cookie de la sesión de PHP.
 *
 * Solo se llaman endpoints de lectura: no modifica datos (salvo la fecha de
 * última conexión del usuario que ingresa).
 */

const ENDPOINTS = [
    // Catálogos
    'escalas.php', 'estados.php', 'estados_taller.php', 'marcas.php', 'marcas.php?id_tipo=1',
    'modelos.php', 'modelos.php?id_tipo=1&id_marca=1',
    'modelo_con_marca.php', 'plantillas.php', 'potencias.php', 'sectores.php',
    'talleres.php', 'tipos.php', 'anios.php',
    // Inventario / taller / repuestos / papelera
    'consultaInventario.php', 'vista_taller.php', 'repuestos.php', 'inventario_historial.php',
    'historialEquipo.php?id_equipo={id_equipo}',
    'cargar_programacion.php?id_equipo={id_equipo}',
    // Estadísticas
    'estadisticas_resumen.php', 'estadistica_equipos.php', 'estadistica_stock.php',
    'estadistica_incidencias.php', 'estadistica_bajas.php', 'estadistica_repuestos.php',
    // Administración (requiere admin)
    'usuarios.php',
];

// Archivo de cookies de la sesión de PHP mientras dura la captura.
function archivoCookies(): string {
    static $archivo = null;
    return $archivo ??= tempnam(sys_get_temp_dir(), 'snap');
}

/** Pedido HTTP con la cookie de sesión. $form: POST de formulario; $api: agrega X-Requested-With. */
function pedir(string $url, ?array $form = null, bool $api = true): array {
    $ch = curl_init($url);
    $headers = ['Accept: application/json, text/html'];
    if ($api) {
        $headers[] = 'X-Requested-With: XMLHttpRequest';
    }
    if ($form !== null) {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($form));
    }
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER     => $headers,
        CURLOPT_TIMEOUT        => 30,
        CURLOPT_COOKIEFILE     => archivoCookies(),
        CURLOPT_COOKIEJAR      => archivoCookies(),
    ]);
    $cuerpo = curl_exec($ch);
    $codigo = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $destino = (string)curl_getinfo($ch, CURLINFO_REDIRECT_URL);
    curl_close($ch);
    return [$codigo, $cuerpo === false ? '' : $cuerpo, $destino];
}

/** Ingresa como lo haría el navegador: pide el formulario (token CSRF) y lo envía. */
function ingresar(string $base, string $usuario, string $clave): void {
    $web = preg_replace('~/php$~', '/web', $base);
    [, $html] = pedir("$web/ingresar.php", null, false);
    if (!preg_match('/name="csrf" value="([0-9a-f]+)"/', $html, $m)) {
        fwrite(STDERR, "No se encontró el formulario de ingreso en $web/ingresar.php\n");
        exit(1);
    }
    [$codigo, , $destino] = pedir("$web/ingresar.php", ['csrf' => $m[1], 'usuario' => $usuario, 'clave' => $clave], false);
    if ($codigo !== 303 || !str_ends_with($destino, 'app.php')) {
        fwrite(STDERR, "Login fallido ($codigo -> $destino)\n");
        exit(1);
    }
}

// Valores de ejemplo para los endpoints con parámetros, tomados de datos reales.
function valoresEjemplo(string $base): array {
    $valores = ['id_equipo' => '1', 'numero_serie' => ''];
    [$codigo, $cuerpo] = pedir("$base/consultaInventario.php");
    $datos = json_decode($cuerpo, true);
    if (isset($datos['data'])) {
        $datos = $datos['data'];
    }
    if ($codigo === 200 && is_array($datos) && isset($datos[0])) {
        $valores['id_equipo']    = (string)($datos[0]['id_equipo'] ?? '1');
        $valores['numero_serie'] = (string)($datos[0]['numero_serie'] ?? '');
    }
    return $valores;
}

function nombreArchivo(string $endpoint): string {
    return preg_replace('/[^A-Za-z0-9_.-]+/', '_', $endpoint) . '.json';
}

function capturar(string $salida): void {
    $base    = rtrim(getenv('API_BASE') ?: 'http://localhost/proyecto_progra_iv/InventarioAR-main/php', '/');
    $usuario = getenv('API_USER');
    $clave   = getenv('API_PASS');
    if (!$usuario || !$clave) {
        fwrite(STDERR, "Definí API_USER y API_PASS (usuario administrador).\n");
        exit(1);
    }
    if (!is_dir($salida) && !mkdir($salida, 0777, true)) {
        fwrite(STDERR, "No se pudo crear $salida\n");
        exit(1);
    }

    ingresar($base, $usuario, $clave);
    $valores = valoresEjemplo($base);
    foreach (ENDPOINTS as $endpoint) {
        $ruta = preg_replace_callback('/\{(\w+)\}/', fn($m) => rawurlencode($valores[$m[1]] ?? ''), $endpoint);
        [$codigo, $cuerpo] = pedir("$base/$ruta");
        $decodificado = json_decode($cuerpo, true);
        $registro = [
            'endpoint' => $endpoint,
            'status'   => $codigo,
            'es_json'  => json_last_error() === JSON_ERROR_NONE,
            'body'     => json_last_error() === JSON_ERROR_NONE ? $decodificado : $cuerpo,
        ];
        file_put_contents("$salida/" . nombreArchivo($endpoint),
            json_encode($registro, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
        printf("%-50s %d%s\n", $endpoint, $codigo, $registro['es_json'] ? '' : '  (NO JSON)');
    }
    pedir("$base/logout.php", []);
    @unlink(archivoCookies());
}

function normalizarOrden(array $registro): array {
    $ordenar = function (array $lista): array {
        if (!array_is_list($lista)) {
            return $lista;
        }
        usort($lista, fn($x, $y) => strcmp(json_encode($x), json_encode($y)));
        return $lista;
    };
    $cuerpo = $registro['body'] ?? null;
    if (is_array($cuerpo) && isset($cuerpo['data']) && is_array($cuerpo['data'])) {
        $registro['body']['data'] = $ordenar($cuerpo['data']);
    } elseif (is_array($cuerpo)) {
        $registro['body'] = $ordenar($cuerpo);
    }
    return $registro;
}

function comparar(string $a, string $b): void {
    $diferencias = 0;
    foreach (ENDPOINTS as $endpoint) {
        $archivo = nombreArchivo($endpoint);
        $ra = @file_get_contents("$a/$archivo");
        $rb = @file_get_contents("$b/$archivo");
        if ($ra === false || $rb === false) {
            printf("%-50s FALTA en %s\n", $endpoint, $ra === false ? $a : $b);
            $diferencias++;
            continue;
        }
        // El orden de las filas no cuenta: varias consultas no tienen un
        // ORDER BY que desempate y MariaDB puede devolverlas en otro orden.
        $ja = normalizarOrden(json_decode($ra, true));
        $jb = normalizarOrden(json_decode($rb, true));
        if ($ja === $jb) {
            printf("%-50s igual\n", $endpoint);
            continue;
        }
        $diferencias++;
        $detalle = $ja['status'] !== $jb['status']
            ? "status {$ja['status']} -> {$jb['status']}"
            : 'cuerpo distinto';
        printf("%-50s DISTINTO (%s)\n", $endpoint, $detalle);
    }
    echo $diferencias === 0 ? "\nSin diferencias.\n" : "\n$diferencias endpoint(s) con diferencias.\n";
    exit($diferencias === 0 ? 0 : 2);
}

$modo = $argv[1] ?? '';
if ($modo === 'capturar' && isset($argv[2])) {
    capturar($argv[2]);
} elseif ($modo === 'comparar' && isset($argv[2], $argv[3])) {
    comparar($argv[2], $argv[3]);
} else {
    fwrite(STDERR, "Uso:\n  php tools/snapshot_api.php capturar <salida>\n  php tools/snapshot_api.php comparar <a> <b>\n");
    exit(1);
}
