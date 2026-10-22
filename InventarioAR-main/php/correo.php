<?php
// Envío de correos del sistema.
//
// Con una API key de Resend (resend_api_key en config.local.php) los correos
// salen por la API HTTPS de Resend (https://resend.com/docs/api-reference/emails/send-email),
// que funciona aunque el hosting no tenga mail() ni permita SMTP.
// Sin API key se usa mail(), como pide la consigna.
//
// Requiere php/config.php (constantes RESEND_*, MAIL_REMITENTE).

const RESEND_URL = 'https://api.resend.com/emails';

/**
 * Envía un correo de texto plano. Devuelve si el servicio lo aceptó.
 * Nunca lanza excepciones: un fallo se registra en logs/php_errores.log y
 * quien llama decide qué mostrar (el correo no debe frenar la operación).
 *
 * $responderA: dirección ya validada con FILTER_VALIDATE_EMAIL (o null).
 */
function enviarCorreo(string $para, string $asunto, string $texto, ?string $responderA = null): bool {
    if (RESEND_API_KEY !== '') {
        return enviarConResend($para, $asunto, $texto, $responderA);
    }
    return enviarConMail($para, $asunto, $texto, $responderA);
}

function enviarConResend(string $para, string $asunto, string $texto, ?string $responderA): bool {
    $datos = ['from' => RESEND_REMITENTE, 'to' => [$para], 'subject' => $asunto, 'text' => $texto];
    if ($responderA !== null) {
        $datos['reply_to'] = $responderA;
    }
    $cuerpo = json_encode($datos, JSON_UNESCAPED_UNICODE);
    $cabeceras = [
        'Authorization: Bearer ' . RESEND_API_KEY,
        'Content-Type: application/json',
        'User-Agent: inventario-radios/1.0',
    ];

    if (function_exists('curl_init')) {
        $c = curl_init(RESEND_URL);
        curl_setopt_array($c, [
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => $cuerpo,
            CURLOPT_HTTPHEADER     => $cabeceras,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_TIMEOUT        => 10,
        ]);
        $respuesta = curl_exec($c);
        $estado = (int)curl_getinfo($c, CURLINFO_RESPONSE_CODE);
        $falla = $respuesta === false ? curl_error($c) : '';
    } else {
        // Sin la extensión cURL: la misma petición con los streams de PHP.
        $contexto = stream_context_create(['http' => [
            'method'        => 'POST',
            'header'        => implode("\r\n", $cabeceras),
            'content'       => $cuerpo,
            'timeout'       => 10,
            'ignore_errors' => true,   // leer también el cuerpo de las respuestas 4xx/5xx
        ]]);
        $respuesta = @file_get_contents(RESEND_URL, false, $contexto);
        $estado = preg_match('#^HTTP/\S+ (\d{3})#', $http_response_header[0] ?? '', $m) ? (int)$m[1] : 0;
        $falla = $respuesta === false ? 'sin respuesta' : '';
    }

    if ($estado >= 200 && $estado < 300) {
        return true;
    }
    // Resend explica el motivo en el cuerpo (p. ej. dominio no verificado o clave inválida).
    error_log("Resend: no se pudo enviar a $para (HTTP $estado) " . ($falla ?: substr((string)$respuesta, 0, 300)));
    return false;
}

function enviarConMail(string $para, string $asunto, string $texto, ?string $responderA): bool {
    // Muchos servidores (y los hostings gratuitos) no tienen el correo habilitado.
    // Si mail() está en disable_functions ni siquiera existe, y llamarla sería un error fatal.
    if (!function_exists('mail')) {
        return false;
    }
    $cabeceras = ['From: ' . MAIL_REMITENTE];
    if ($responderA !== null) {
        $cabeceras[] = 'Reply-To: ' . $responderA;   // ya validada: no admite saltos de línea
    }
    array_push($cabeceras, 'MIME-Version: 1.0', 'Content-Type: text/plain; charset=UTF-8', 'Content-Transfer-Encoding: 8bit');
    $asunto = '=?UTF-8?B?' . base64_encode($asunto) . '?=';
    return @mail($para, $asunto, $texto, implode("\r\n", $cabeceras));
}
