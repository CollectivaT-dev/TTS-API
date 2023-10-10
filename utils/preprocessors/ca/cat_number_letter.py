MAX_NUMERO = 999999999999

UNIDADES = (
    'zero',
    'u',
    'dos',
    'tres',
    'quatre',
    'cinc',
    'sis',
    'set',
    'vuit',
    'nou'
)

DECENAS = (
    'deu', #????
    'onze',
    'dotze',
    'tretze',
    'catorze',
    'quinze',
    'setze',
    'disset',
    'divuit',
    'dinou'
)

DIEZ_DIEZ = (
    'zero',
    'deu',
    'vint',
    'trenta',
    'quaranta',
    'cinquanta',
    'seixanta',
    'setanta',
    'vuitanta',
    'noranta'
)

CIENTOS = (
    '_',
    'cent',
    'dos-cents',
    'tres-cents',
    'quatre-cents',
    'cinc-cents',
    'sis-cents',
    'set-cents',
    'vuit-cents',
    'nou-cents'
)

def num_let(numero):
    numero_entero = int(numero)
    letras_decimal = ''
    parte_decimal = int(round((abs(numero) - abs(numero_entero)) * 100))
    if parte_decimal > 9:
        letras_decimal = 'coma %s' % num_let(parte_decimal)
    elif parte_decimal > 0:
        letras_decimal = 'coma cero %s' % num_let(parte_decimal)
    if (numero_entero <= 99):
        resultado = leer_decenas(numero_entero)
    elif (numero_entero <= 999):
        resultado = leer_centenas(numero_entero)
    elif (numero_entero <= 999999):
        resultado = leer_miles(numero_entero)
    elif (numero_entero <= 999999999):
        resultado = leer_millones(numero_entero)
    else:
        resultado = leer_millardos(numero_entero)
    resultado = resultado.replace('uno mil', 'un mil')
    resultado = resultado.strip()
    resultado = resultado.replace(' _ ', ' ')
    resultado = resultado.replace('  ', ' ')
    if parte_decimal > 0:
        resultado = '%s %s' % (resultado, letras_decimal)
    return resultado
    
    
def leer_decenas(numero):
    if numero < 10:
        return UNIDADES[numero]
    decena, unidad = divmod(numero, 10)
    if numero <= 19:
        resultado = DECENAS[unidad]
    elif numero == 20:
        resultado = 'vint'
    elif numero <= 29:
        resultado = 'vint-i-%s' % UNIDADES[unidad]
    else:
        resultado = DIEZ_DIEZ[decena]
        if unidad > 0:
            resultado = '%s-i-%s' % (resultado, UNIDADES[unidad])
    return resultado

def leer_centenas(numero):
    centena, decena = divmod(numero, 100)
    if decena == 0 and centena == 1:
        resultado = 'cent'
    else:
        resultado = CIENTOS[centena]
        if decena > 0:
            resultado = '%s %s' % (resultado, leer_decenas(decena))
    return resultado

def leer_miles(numero):
    millar, centena = divmod(numero, 1000)
    resultado = ''
    if (millar == 1):
        resultado = ''
    if (millar >= 2) and (millar <= 9):
        resultado = UNIDADES[millar]
    elif (millar >= 10) and (millar <= 99):
        resultado = leer_decenas(millar)
    elif (millar >= 100) and (millar <= 999):
        resultado = leer_centenas(millar)
    resultado = '%s mil' % resultado
    if centena > 0:
        resultado = '%s %s' % (resultado, leer_centenas(centena))
    return resultado

def leer_millones(numero):
    millon, millar = divmod(numero, 1000000)
    resultado = ''
    if (millon == 1):
        resultado = ' un milió '
    if (millon >= 2) and (millon <= 9):
        resultado = UNIDADES[millon]
    elif (millon >= 10) and (millon <= 99):
        resultado = leer_decenas(millon)
    elif (millon >= 100) and (millon <= 999):
        resultado = leer_centenas(millon)
    if millon > 1:
        resultado = '%s milions' % resultado
    if (millar > 0) and (millar <= 999):
        resultado = '%s %s' % (resultado, leer_centenas(millar))
    elif (millar >= 1000) and (millar <= 999999):
        resultado = '%s %s' % (resultado, leer_miles(millar))
    return resultado

def leer_millardos(numero):
    millardo, millon = divmod(numero, 1000000)
    return '%s milions %s' % (leer_miles(millardo), leer_millones(millon))