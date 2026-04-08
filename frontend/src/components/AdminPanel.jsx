import { useState, useEffect, useCallback } from 'react'

const API_BASE = '/api/v1'

const ESTADO_COLORS = {
  pendiente_anticipo: '#f59e0b',
  aprobada: '#22c55e',
  rechazada_anticipo: '#ef4444',
  pendiente: '#f59e0b',
  validado: '#22c55e',
  rechazado: '#ef4444',
}

export default function AdminPanel() {
  const [ordenes, setOrdenes] = useState([])
  const [selected, setSelected] = useState(null)
  const [pagado, setPagado] = useState(false)
  const [observacion, setObservacion] = useState('')
  const [archivo, setArchivo] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [resultado, setResultado] = useState(null)

  const fetchOrdenes = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/administracion/ordenes`)
      const json = await res.json()
      setOrdenes(json.data || [])
    } catch {
      setOrdenes([])
    }
  }, [])

  useEffect(() => {
    fetchOrdenes()
  }, [fetchOrdenes])

  const handleSelect = (orden) => {
    setSelected(orden)
    setPagado(orden.anticipo?.pagado || false)
    setObservacion(orden.anticipo?.observacion || '')
    setArchivo(null)
    setResultado(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selected?.anticipo) return

    setSubmitting(true)
    setResultado(null)

    const formData = new FormData()
    formData.append('pagado', pagado)
    formData.append('observacion', observacion)
    if (archivo) formData.append('factura', archivo)

    try {
      const res = await fetch(
        `${API_BASE}/administracion/anticipos/${selected.anticipo.id}/validar`,
        { method: 'PUT', body: formData }
      )
      const json = await res.json()
      setResultado({ status: res.status, data: json })
      if (res.ok) await fetchOrdenes()
    } catch (err) {
      setResultado({ status: 'error', data: { error: err.message } })
    } finally {
      setSubmitting(false)
    }
  }

  const pendientes = ordenes.filter((o) => o.anticipo?.estado === 'pendiente')
  const procesadas = ordenes.filter((o) => o.anticipo?.estado !== 'pendiente')

  return (
    <div className="admin-panel">
      <div className="admin-list">
        <h3>Ordenes Pendientes ({pendientes.length})</h3>
        {pendientes.length === 0 && (
          <p className="admin-empty">Sin ordenes pendientes</p>
        )}
        {pendientes.map((o) => (
          <div
            key={o.id}
            className={`admin-of-card ${selected?.id === o.id ? 'selected' : ''}`}
            onClick={() => handleSelect(o)}
          >
            <div className="admin-of-header">
              <span className="admin-of-id">OF-{o.id}</span>
              <span
                className="admin-estado"
                style={{ color: ESTADO_COLORS[o.estado] || '#94a3b8' }}
              >
                {o.estado}
              </span>
            </div>
            <div className="admin-of-cliente">{o.cliente}</div>
            <div className="admin-of-desc">{o.descripcion}</div>
            <div className="admin-of-monto">
              Anticipo: ${Number(o.anticipo?.monto_estimado || 0).toLocaleString()}
            </div>
          </div>
        ))}

        {procesadas.length > 0 && (
          <>
            <h3 className="admin-section-title">Procesadas ({procesadas.length})</h3>
            {procesadas.map((o) => (
              <div
                key={o.id}
                className={`admin-of-card processed ${selected?.id === o.id ? 'selected' : ''}`}
                onClick={() => handleSelect(o)}
              >
                <div className="admin-of-header">
                  <span className="admin-of-id">OF-{o.id}</span>
                  <span
                    className="admin-estado"
                    style={{ color: ESTADO_COLORS[o.anticipo?.estado] || '#94a3b8' }}
                  >
                    {o.anticipo?.estado}
                  </span>
                </div>
                <div className="admin-of-cliente">{o.cliente}</div>
              </div>
            ))}
          </>
        )}
      </div>

      <div className="admin-detail">
        {!selected ? (
          <div className="admin-placeholder">
            <p>Selecciona una OF para validar</p>
          </div>
        ) : (
          <>
            <div className="admin-detail-header">
              <h3>OF-{selected.id}</h3>
              <span
                className="admin-estado-badge"
                style={{
                  backgroundColor: ESTADO_COLORS[selected.estado] || '#6b7280',
                }}
              >
                {selected.estado}
              </span>
            </div>

            <div className="admin-detail-grid">
              <div className="admin-field-ro">
                <label>Cliente</label>
                <span>{selected.cliente}</span>
              </div>
              <div className="admin-field-ro">
                <label>Descripcion</label>
                <span>{selected.descripcion}</span>
              </div>
              <div className="admin-field-ro">
                <label>Plazo</label>
                <span>{selected.plazo_entrega}</span>
              </div>
              <div className="admin-field-ro">
                <label>Monto Anticipo</label>
                <span>${Number(selected.anticipo?.monto_estimado || 0).toLocaleString()}</span>
              </div>
            </div>

            {selected.anticipo?.estado === 'pendiente' ? (
              <form className="admin-form" onSubmit={handleSubmit}>
                <h4>Validacion de Anticipo</h4>

                <div className="admin-toggle-row">
                  <label>Anticipo Pagado</label>
                  <div
                    className={`toggle ${pagado ? 'toggle-on' : ''}`}
                    onClick={() => setPagado(!pagado)}
                  >
                    <div className="toggle-knob" />
                    <span className="toggle-label">{pagado ? 'SI' : 'NO'}</span>
                  </div>
                </div>

                <div className="admin-field">
                  <label>Factura / Comprobante de Pago</label>
                  <input
                    type="file"
                    className="admin-file-input"
                    onChange={(e) => setArchivo(e.target.files[0] || null)}
                  />
                  {archivo && (
                    <span className="admin-file-name">{archivo.name}</span>
                  )}
                </div>

                <div className="admin-field">
                  <label>Observacion</label>
                  <textarea
                    className="admin-textarea"
                    rows={3}
                    placeholder="Observaciones sobre la validacion..."
                    value={observacion}
                    onChange={(e) => setObservacion(e.target.value)}
                  />
                </div>

                <button
                  type="submit"
                  className={`submit-btn ${pagado ? 'btn-approve' : 'btn-reject'}`}
                  disabled={submitting}
                >
                  {submitting
                    ? 'Procesando...'
                    : pagado
                      ? 'Aprobar Anticipo'
                      : 'Rechazar Anticipo'}
                </button>
              </form>
            ) : (
              <div className="admin-resolved">
                <h4>Anticipo {selected.anticipo?.estado}</h4>
                {selected.anticipo?.factura_archivo && (
                  <div className="admin-field-ro">
                    <label>Factura</label>
                    <span>{selected.anticipo.factura_archivo.nombre}</span>
                  </div>
                )}
                {selected.anticipo?.observacion && (
                  <div className="admin-field-ro">
                    <label>Observacion</label>
                    <span>{selected.anticipo.observacion}</span>
                  </div>
                )}
              </div>
            )}

            {resultado && (
              <div className="response-panel">
                <div className="response-header">
                  <span className={`status-code ${resultado.status < 300 ? 'success' : 'error'}`}>
                    Status: {resultado.status}
                  </span>
                </div>
                <pre>{JSON.stringify(resultado.data, null, 2)}</pre>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
