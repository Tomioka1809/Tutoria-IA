import { normalizeApiError } from '../api-error';

/**
 * `normalizeApiError` decide qué mensaje ve el usuario y qué detalle del servidor se
 * le muestra. Lo segundo es lo delicado: el detalle viene del backend y puede
 * arrastrar un stack trace o un token. La redacción sólo sirve si está cubierta.
 */
describe('normalizeApiError', () => {
  describe('clasificación por código de estado', () => {
    const casos: [number, string, string, boolean][] = [
      [401, 'unauthorized', 'errors.unauthorized', false],
      [403, 'forbidden', 'errors.forbidden', false],
      [404, 'not_found', 'errors.notFound', false],
      [409, 'conflict', 'errors.conflict', false],
      [400, 'validation', 'errors.validation', false],
      [422, 'validation', 'errors.validation', false],
      [500, 'server', 'errors.server', true],
      [503, 'server', 'errors.server', true],
    ];

    it.each(casos)('%i -> %s', (status, kind, messageKey, retryable) => {
      const res = normalizeApiError({ response: { status, data: {} } });

      expect(res.kind).toBe(kind);
      expect(res.messageKey).toBe(messageKey);
      expect(res.retryable).toBe(retryable);
      expect(res.status).toBe(status);
    });
  });

  describe('fallos sin respuesta del servidor', () => {
    it('reconoce el timeout de axios', () => {
      const res = normalizeApiError({ code: 'ECONNABORTED', message: 'timeout of 60000ms' });

      expect(res.kind).toBe('timeout');
      expect(res.retryable).toBe(true);
    });

    it('reconoce el fallo de red', () => {
      const res = normalizeApiError({ isAxiosError: true, message: 'Network Error' });

      expect(res.kind).toBe('network');
      expect(res.retryable).toBe(true);
    });

    it('usa la clave de reserva para lo desconocido', () => {
      const res = normalizeApiError({}, 'errors.updateProfile');

      expect(res.kind).toBe('unknown');
      expect(res.messageKey).toBe('errors.updateProfile');
    });

    it('no explota con null ni con un string', () => {
      expect(normalizeApiError(null).kind).toBe('unknown');
      expect(normalizeApiError('vaya').kind).toBe('unknown');
    });
  });

  describe('extracción del detalle', () => {
    it('toma el campo detail de FastAPI', () => {
      const res = normalizeApiError({
        response: { status: 400, data: { detail: 'La contraseña es muy corta.' } },
      });

      expect(res.detail).toBe('La contraseña es muy corta.');
    });

    it('junta los errores de validación de Pydantic', () => {
      const res = normalizeApiError({
        response: {
          status: 422,
          data: { detail: [{ msg: 'campo requerido' }, { msg: 'debe ser entero' }] },
        },
      });

      expect(res.detail).toBe('campo requerido; debe ser entero');
    });

    it('sólo muestra el detalle en validación y conflicto', () => {
      // Un 500 puede traer cualquier cosa del servidor; no se le enseña al usuario.
      const res = normalizeApiError({
        response: { status: 500, data: { detail: 'algo interno se rompió' } },
      });

      expect(res.detail).toBeUndefined();
    });
  });

  describe('redacción de detalles peligrosos', () => {
    const debeOcultarse = [
      ['un stack trace de Python', 'Traceback (most recent call last): File "app.py", line 4'],
      ['un stack trace de JS', 'Error at handler (/app/index.js:12:5)'],
      ['una cabecera Authorization', 'Falló con Authorization: Bearer abc123'],
      ['un JWT', 'token eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI3In0.firma_de_prueba'],
      // 39 caracteres: AIza + 35, que es el formato real. El patrón exige ese
      // largo exacto, así que una cadena más larga no se reconoce como clave.
      ['una clave de Google', 'key AIzaSyB1234567890abcdefghijklmnopqrstuv'],
      ['una contraseña', 'fallo con password=secreta123'],
      ['un access_token', 'no se pudo leer access_token'],
    ];

    it.each(debeOcultarse)('oculta %s', (_caso, detalle) => {
      const res = normalizeApiError({
        response: { status: 400, data: { detail: detalle } },
      });

      expect(res.detail).toBeUndefined();
    });

    it('recorta los detalles muy largos', () => {
      const res = normalizeApiError({
        response: { status: 400, data: { detail: 'x'.repeat(500) } },
      });

      expect(res.detail!.length).toBeLessThanOrEqual(240);
    });

    it('normaliza los espacios', () => {
      const res = normalizeApiError({
        response: { status: 409, data: { detail: '  El correo   ya\n existe.  ' } },
      });

      expect(res.detail).toBe('El correo ya existe.');
    });

    it('descarta un detalle vacío', () => {
      const res = normalizeApiError({
        response: { status: 400, data: { detail: '   ' } },
      });

      expect(res.detail).toBeUndefined();
    });
  });
});
