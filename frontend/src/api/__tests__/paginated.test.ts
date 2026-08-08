import { fetchAllPages } from '../paginated';
import client from '../client';

jest.mock('../client', () => ({
  __esModule: true,
  default: { get: jest.fn() },
}));

const get = client.get as jest.Mock;

function pagina(items: unknown[], total?: number) {
  return {
    data: items,
    headers: total === undefined ? {} : { 'x-total-count': String(total) },
  };
}

/**
 * `fetchAllPages` es lo que evita que paginar el backend rompa las pantallas de
 * administración: el sorteo arma selectores sobre el padrón completo, así que si el
 * helper corta antes de tiempo desaparecen estudiantes de la lista en silencio.
 */
describe('fetchAllPages', () => {
  beforeEach(() => get.mockReset());

  it('devuelve una sola página cuando el lote viene incompleto', async () => {
    get.mockResolvedValueOnce(pagina([1, 2, 3], 3));

    await expect(fetchAllPages<number>('/admin/users', { pageSize: 100 })).resolves.toEqual([
      1, 2, 3,
    ]);
    expect(get).toHaveBeenCalledTimes(1);
  });

  it('encadena páginas hasta juntar el total', async () => {
    get
      .mockResolvedValueOnce(pagina([1, 2], 5))
      .mockResolvedValueOnce(pagina([3, 4], 5))
      .mockResolvedValueOnce(pagina([5], 5));

    await expect(fetchAllPages<number>('/admin/users', { pageSize: 2 })).resolves.toEqual([
      1, 2, 3, 4, 5,
    ]);
    expect(get).toHaveBeenCalledTimes(3);
  });

  it('avanza el offset en cada petición', async () => {
    get
      .mockResolvedValueOnce(pagina([1, 2], 4))
      .mockResolvedValueOnce(pagina([3, 4], 4));

    await fetchAllPages<number>('/admin/corpus', { pageSize: 2 });

    expect(get.mock.calls[0][1].params).toEqual({ limit: 2, offset: 0 });
    expect(get.mock.calls[1][1].params).toEqual({ limit: 2, offset: 2 });
  });

  it('para cuando el total se alcanza justo en el borde', async () => {
    // Un lote completo que ya cubre el total no debe disparar otra petición.
    get.mockResolvedValueOnce(pagina([1, 2], 2));

    await expect(fetchAllPages<number>('/admin/users', { pageSize: 2 })).resolves.toEqual([
      1, 2,
    ]);
    expect(get).toHaveBeenCalledTimes(1);
  });

  it('funciona aunque falte la cabecera de total', async () => {
    get.mockResolvedValueOnce(pagina([1, 2])).mockResolvedValueOnce(pagina([3]));

    await expect(fetchAllPages<number>('/admin/users', { pageSize: 2 })).resolves.toEqual([
      1, 2, 3,
    ]);
  });

  it('respeta el tope de páginas si el servidor nunca corta', async () => {
    // Sin este tope, un total mal informado deja al cliente pidiendo para siempre.
    get.mockResolvedValue(pagina([1, 2], 999999));

    const items = await fetchAllPages<number>('/admin/users', {
      pageSize: 2,
      maxPages: 3,
    });

    expect(get).toHaveBeenCalledTimes(3);
    expect(items).toHaveLength(6);
  });

  it('devuelve vacío cuando no hay nada', async () => {
    get.mockResolvedValueOnce(pagina([], 0));

    await expect(fetchAllPages<number>('/admin/corpus')).resolves.toEqual([]);
  });

  it('propaga el error en vez de devolver una lista incompleta', async () => {
    get.mockResolvedValueOnce(pagina([1, 2], 10)).mockRejectedValueOnce(new Error('red'));

    await expect(fetchAllPages<number>('/admin/users', { pageSize: 2 })).rejects.toThrow(
      'red'
    );
  });
});
