import client from './client';

/**
 * Recorre un endpoint paginado y devuelve todos los elementos.
 *
 * Los listados de administración (`/admin/users`, `/admin/corpus`) devolvían la tabla
 * entera en una sola respuesta: cientos de usuarios, o los ~1370 fragmentos del corpus
 * con su texto completo. Ahora el servidor acota cada consulta y publica el total en
 * la cabecera `X-Total-Count`.
 *
 * Las pantallas que necesitan la lista completa —el sorteo arma selectores sobre todos
 * los estudiantes y tutores— la siguen recibiendo, pero en tramos: lo que se acota es
 * el trabajo del servidor por petición, no el resultado.
 *
 * El paso siguiente natural es que las pantallas de sólo lectura muestren una página y
 * un botón de "cargar más", y dejen de pedir el total.
 */
export async function fetchAllPages<T>(
  path: string,
  options: { pageSize?: number; maxPages?: number; config?: object } = {}
): Promise<T[]> {
  const pageSize = options.pageSize ?? 100;
  // Tope de seguridad: si el servidor dejara de informar el total, o lo informara
  // mal, esto evita un bucle infinito de peticiones.
  const maxPages = options.maxPages ?? 100;

  const items: T[] = [];
  let offset = 0;

  for (let page = 0; page < maxPages; page++) {
    const res = await client.get<T[]>(path, {
      ...options.config,
      params: { limit: pageSize, offset },
    });

    const lote = res.data ?? [];
    items.push(...lote);

    // Un lote incompleto significa que no hay más: sirve incluso si falta la cabecera.
    if (lote.length < pageSize) break;

    offset += pageSize;

    const totalHeader = res.headers?.['x-total-count'];
    const total = totalHeader === undefined ? null : Number(totalHeader);
    if (total !== null && Number.isFinite(total) && offset >= total) break;
  }

  return items;
}
