# 05 — Sub-Sprint 04 : Outils transversaux (i18n, Rapports, Utilitaires)

**Sprint parent :** `01_sprint.md`
**Statut :** ✅ Scaffold implémenté — renderer QtPainter à compléter (Sprint 02)

---

## i18n

- `tools/i18n/tr.py` — `tr(context, key)` → `QCoreApplication.translate()`
- Fichiers source `.ts` dans `resources/i18n/` (extraits via `pylupdate6`)
- Compilation `.qm` via `lrelease` au build
- Changement de langue à chaud via `SettingsService.set_language()` + `QTranslator`

## Moteur de rapports (Crystal Report style)

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 200" width="600" height="200">
  <rect width="600" height="200" fill="#f8f8f8" rx="6"/>
  <!-- Flow -->
  <rect x="10"  y="70" width="120" height="60" rx="4" fill="#e3f2fd" stroke="#1565c0"/>
  <text x="70"  y="95"  text-anchor="middle" font-size="10" font-weight="bold">JSON Template</text>
  <text x="70"  y="110" text-anchor="middle" font-size="9" fill="#555">DB report_templates</text>
  <line x1="130" y1="100" x2="160" y2="100" stroke="#333" stroke-width="1.5" marker-end="url(#a)"/>

  <rect x="160" y="70" width="120" height="60" rx="4" fill="#fff8e1" stroke="#f57f17"/>
  <text x="220" y="95"  text-anchor="middle" font-size="10" font-weight="bold">TemplateLoader</text>
  <text x="220" y="110" text-anchor="middle" font-size="9" fill="#555">→ ReportTemplate</text>
  <line x1="280" y1="100" x2="310" y2="100" stroke="#333" stroke-width="1.5" marker-end="url(#a)"/>

  <rect x="310" y="70" width="120" height="60" rx="4" fill="#e8f5e9" stroke="#2e7d32"/>
  <text x="370" y="95"  text-anchor="middle" font-size="10" font-weight="bold">DataBinder</text>
  <text x="370" y="110" text-anchor="middle" font-size="9" fill="#555">{field} → valeur</text>
  <line x1="430" y1="100" x2="460" y2="100" stroke="#333" stroke-width="1.5" marker-end="url(#a)"/>

  <rect x="460" y="70" width="125" height="60" rx="4" fill="#fce4ec" stroke="#c62828"/>
  <text x="522" y="90"  text-anchor="middle" font-size="10" font-weight="bold">QtPainter</text>
  <text x="522" y="104" text-anchor="middle" font-size="9" fill="#555">Renderer</text>
  <text x="522" y="118" text-anchor="middle" font-size="9" fill="#555">QPainter+QPrinter</text>

  <text x="300" y="170" text-anchor="middle" font-size="9" fill="#808080">Sortie : Aperçu QPixmap · Impression directe · Export PDF (QPdfWriter)</text>
  <defs><marker id="a" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
    <path d="M0,0 L8,4 L0,8 Z" fill="#333"/>
  </marker></defs>
</svg>
```

### Format de template JSON

```json
{
  "templateId": "invoice_v1",
  "title": {"fr": "Facture", "en": "Invoice"},
  "paperSize": "A4",
  "orientation": "portrait",
  "bands": [
    { "type": "header", "height": 60, "elements": [ ... ] },
    { "type": "detail", "height": 18, "datasource": "lignes", "elements": [ ... ] },
    { "type": "footer", "height": 50, "elements": [ ... ] }
  ]
}
```

Types d'éléments : `text | field | image | line | box`
Champs dynamiques : `{nom_champ}` résolu par `DataBinder`

## Devise

| Code | Symbole | Format fr |
|------|---------|-----------|
| TND (défaut) | DT | `1 234,567 DT` |
| EUR | € | `1 234,57 €` |
| USD | $ | `$ 1,234.57` |
| CAD | CA$ | `CA$ 1,234.57` |

## Snapshots BDD

- `SnapshotService.create()` → copie `garage.db` → `~/.garage_reparation/snapshots/garage_YYYYMMDD_HHMMSS.db`
- `SnapshotService.restore()` → remplace la BDD active (nécessite redémarrage)
- Réservé rôle **superadmin**
