<?php
// Envío de correos del sistema.
//
// Se usa el primer servicio configurado en config.local.php:
//   1. Brevo (brevo_api_key + brevo_remitente): API HTTPS de Brevo
//      (https://developers.brevo.com/reference/sendtransacemail). Alcanza con
//      verificar una dirección de remitente (p. ej. un Gmail), sin dominio propio,
//      y envía a cualquier destinatario.
//   2. Resend (resend_api_key): API HTTPS de Resend
//      (https://resend.com/docs/api-reference/emails/send-email). Sin dominio
//      verificado solo envía al email de la propia cuenta.
//   3. mail(), como pide la consigna.
// Las APIs HTTPS funcionan aunque el hosting no tenga mail() ni permita SMTP.
//
// Requiere php/config.php (constantes BREVO_*, RESEND_*, MAIL_REMITENTE).

const BREVO_URL = 'https://api.brevo.com/v3/smtp/email';
const RESEND_URL = 'https://api.resend.com/emails';

/**
 * Envía un correo de texto plano. Devuelve si el servicio lo aceptó.
 * Nunca lanza excepciones: un fallo se registra en logs/php_errores.log y
 * quien llama decide qué mostrar (el correo no debe frenar la operación).
 *
 * $responderA: dirección ya validada con FILTER_VALIDATE_EMAIL (o null).
 */
function enviarCorreo(string $para, string $asunto, string $texto, ?string $responderA = null): bool {
    if (BREVO_API_KEY !== '') {
        return enviarConBrevo($para, $asunto, $texto, $responderA);
    }
    if (RESEND_API_KEY !== '') {
        return enviarConResend($para, $asunto, $texto, $responderA);
    }
    return enviarConMail($para, $asunto, $texto, $responderA);
}

function enviarConBrevo(string $para, string $asunto, string $texto, ?string $responderA): bool {
    $datos = [
        'sender'      => ['name' => BREVO_REMITENTE_NOMBRE, 'email' => BREVO_REMITENTE],
        'to'          => [['email' => $para]],
        'subject'     => $asunto,
        'textContent' => $texto,
    ];
    if ($responderA !== null) {
        $datos['replyTo'] = ['email' => $responderA];
    }
    return postearCorreo('Brevo', BREVO_URL, ['api-key: ' . BREVO_API_KEY, 'Accept: application/json'], $datos, $para);
}

function enviarConResend(string $para, string $asunto, string $texto, ?string $responderA): bool {
    $datos = ['from' => RESEND_REMITENTE, 'to' => [$para], 'subject' => $asunto, 'text' => $texto];
    if ($responderA !== null) {
        $datos['reply_to'] = $responderA;
    }
    return postearCorreo('Resend', RESEND_URL, ['Authorization: Bearer ' . RESEND_API_KEY], $datos, $para);
}

/** POST JSON a la API de un servicio de correo. Devuelve si respondió 2xx. */
function postearCorreo(string $servicio, string $url, array $cabeceras, array $datos, string $para): bool {
    $cuerpo = json_encode($datos, JSON_UNESCAPED_UNICODE);
    $cabeceras[] = 'Content-Type: application/json';
    $cabeceras[] = 'User-Agent: inventario-radios/1.0';

    if (function_exists('curl_init')) {
        $c = curl_init($url);
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
        $respuesta = @file_get_contents($url, false, $contexto);
        $estado = preg_match('#^HTTP/\S+ (\d{3})#', $http_response_header[0] ?? '', $m) ? (int)$m[1] : 0;
        $falla = $respuesta === false ? 'sin respuesta' : '';
    }

    if ($estado >= 200 && $estado < 300) {
        return true;
    }
    // El servicio explica el motivo en el cuerpo (p. ej. remitente no verificado,
    // clave inválida o, en Brevo, IP no autorizada).
    error_log("$servicio: no se pudo enviar a $para (HTTP $estado) " . ($falla ?: substr((string)$respuesta, 0, 300)));
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
