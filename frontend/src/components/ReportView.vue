<template>
  <div class="report-view">
  <div class="report-view-shell px-5 pt-5 sm:px-6 sm:pt-6 pb-5 sm:pb-6">
    <div class="mb-6 space-y-6">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div class="min-w-0">
          <h2 class="font-polonium text-3xl font-bold text-gray-900">Результаты проверки</h2>
          <p v-if="fileInfo" class="mt-1 text-sm text-gray-500">
            <span class="font-medium text-gray-900 break-words">{{ fileInfo.name }}</span>
            <span class="text-gray-500"> · {{ formatFileSize(fileInfo.size) }}</span>
          </p>
          <div
            v-if="documentAuthorRows.length"
            class="mt-3 flex min-w-0 flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-start sm:gap-6"
          >
            <div
              v-for="(row, idx) in documentAuthorRows"
              :key="`author-${idx}`"
              class="flex w-full min-w-0 flex-col gap-1 sm:w-auto"
            >
              <div class="text-sm font-medium text-gray-600">
                <template v-if="row.helpTooltip">
                  <span class="relative inline-block pr-6">
                    {{ row.label }}
                    <span
                      class="group absolute right-0 top-1/2 inline-flex -translate-y-1/2 cursor-help select-none"
                      tabindex="0"
                    >
                      <img
                        src="/iconhelp.png"
                        alt=""
                        width="20"
                        height="20"
                        class="h-5 w-5 object-contain"
                        decoding="async"
                      />
                      <span
                        role="tooltip"
                        class="pointer-events-none invisible absolute bottom-full left-1/2 z-30 mb-2 w-72 max-w-[min(18rem,calc(100vw-2rem))] -translate-x-1/2 whitespace-normal rounded-md bg-gray-900 px-2.5 py-2 text-left text-xs font-normal font-sans normal-case leading-snug tracking-normal text-white opacity-0 shadow-lg transition-opacity duration-150 group-focus-visible:visible group-focus-visible:opacity-100 group-hover:visible group-hover:opacity-100 sm:w-80"
                      >
                        {{ row.helpTooltip }}
                      </span>
                    </span>
                  </span>
                </template>
                <template v-else>{{ row.label }}</template>
              </div>
              <div class="break-words text-sm font-mono text-gray-900">{{ row.value }}</div>
            </div>
          </div>
        </div>
        <aside v-if="documentScores" class="w-full shrink-0 sm:w-max sm:max-w-none sm:self-start">
          <dl class="report-doc-summary__metrics font-polonium font-bold uppercase tracking-[0.1em] text-gray-900">
            <div class="report-doc-summary__row report-doc-summary__row--compact">
              <dt class="text-sm sm:text-base">Изображения</dt>
              <dd class="text-base sm:text-lg">{{ documentScores.imagesCombined }}</dd>
            </div>
            <div
              v-if="documentScores.showDocNlp"
              class="report-doc-summary__row report-doc-summary__row--compact"
            >
              <dt class="text-sm sm:text-base">Текст</dt>
              <dd class="text-base sm:text-lg">{{ documentScores.docNlp }}</dd>
            </div>
            <div class="report-doc-summary__row report-doc-summary__row--final">
              <dt class="text-sm sm:text-base">Итог</dt>
              <dd>{{ documentScores.fin }}</dd>
            </div>
          </dl>
        </aside>
      </div>

      <div class="-mt-2 sm:-mt-3">
        <MetadataTable :metadata="result.metadata" :file-type="result.file_type" :show-only-document-meta="true" />
      </div>

      <div v-if="evidenceList.length > 0" class="card p-4">
        <h3 class="font-polonium text-xl font-bold text-gray-900">Факты из метаданных</h3>
        <ul class="mt-3 space-y-2">
          <li v-for="(fact, index) in evidenceList" :key="index" class="text-sm text-gray-700 border-l-2 border-gray-200 pl-3">
            <span v-for="(paragraph, pIndex) in formatFactText(fact)" :key="pIndex">{{ paragraph }}{{ pIndex < formatFactText(fact).length - 1 ? '. ' : '' }}</span>
          </li>
        </ul>
      </div>
    </div>

    <div class="results-two-column mb-6">
      <aside class="results-sidebar">
        <h3 class="font-polonium text-xl font-bold text-gray-900 mb-3">Изображения в документе</h3>
        <nav class="results-nav">
          <button
            v-for="(img, index) in (result.metadata?.images || [])"
            :key="`img-${index}`"
            type="button"
            class="results-nav-item"
            :class="{ 'results-nav-item--active': selectedId === index }"
            @click="selectedId = index"
          >
            <span class="results-nav-item-label">{{ index + 1 }}. {{ img.filename || 'Без имени' }}</span>
            <span :class="['status-chip', 'status-chip-no-text', 'text-xs', aiChipClass((img.ai_indicators && img.ai_indicators.ai_probability) ?? 0)]" :aria-label="`ИИ: ${(img.ai_indicators && img.ai_indicators.ai_probability) ?? 0}%`"></span>
          </button>
        </nav>
        <p v-if="!(result.metadata?.images || []).length" class="text-sm text-gray-500">Нет изображений</p>
      </aside>
      <div class="results-detail" ref="detailPanel">
        <svg class="wave-strip-svg" viewBox="0 0 1 1.07" preserveAspectRatio="none" aria-hidden="true">
          <path :fill="waveFillColor" :d="wavePathD" />
        </svg>
        <div class="wave-strip-label" :class="waveLabelClass" aria-hidden="true">{{ waveLabel }}</div>
        <template v-if="selectedImage">
          <ImageDetailPanel :image="selectedImage" :image-index="selectedId" />
        </template>
        <p v-else-if="documentHasEmbeddedImages" class="text-sm text-gray-500">
          Выберите изображение в списке слева
        </p>
      </div>
    </div>

    <div class="report-actions-row grid gap-3 sm:grid-cols-2 mt-6">
      <button type="button" @click="handleExportPDF" class="primary-btn w-full">Скачать PDF</button>
      <button type="button" @click="handleExportJSON" class="secondary-btn w-full">Скачать JSON</button>
    </div>

    <p class="mt-2 text-xs text-gray-500 leading-snug">
      Оценки носят вероятностный характер. «Изображения» — среднее по вложениям того же итога, что в карточке каждой
      картинки (слияние эвристики и ML по метаданным). «Текст» — модель по статистике текста DOCX (не семантика). «Итог»
      для Word — среднее между «Изображения» и «Текст», если оба есть; иначе доступное значение.
    </p>
  </div>
  <div class="report-footer-band full-bleed" aria-hidden="true" />
  </div>
</template>

<script>
import MetadataTable from './MetadataTable.vue'
import ImageDetailPanel from './ImageDetailPanel.vue'
import { getReport } from '../services/api'

/** Подсказка у иконки «След генерации» */
const GENERATION_TRACE_HELP_TOOLTIP =
  'Если в метаданных файла в служебных свойствах (автор, описание и др.) видно, что документ создан или собран программно — например, через библиотеку python-docx, Pandoc и подобное, — показываем «Есть». Это не доказательство «текст написал ИИ», а признак того, что контейнер .docx собрали скриптом или библиотекой, а не обычным сохранением из Word.'

export default {
  name: 'ReportView',
  components: {
    MetadataTable,
    ImageDetailPanel
  },
  props: {
    result: {
      type: Object,
      required: true
    }
  },
  emits: ['export-pdf', 'export-json'],
  data() {
    return {
      selectedId: 0,
      wavePathD: 'M 0 0 L 1 0 L 1 1 L 0 1 Z',
      waveAnimId: null,
      waveStartTime: null
    }
  },
  computed: {
    documentTypeLabel() {
      const t = this.result.metadata?.document_type
      if (t === 'powerpoint') return 'PowerPoint'
      if (t === 'word') return 'Word'
      return 'Документ'
    },
    selectedImage() {
      const images = this.result.metadata?.images || []
      if (this.selectedId < 0 || this.selectedId >= images.length) return null
      return images[this.selectedId] || null
    },
    /** Есть ли вложенные изображения для анализа (иначе полоса «Вероятность ИИ» — прочерк, серый). */
    documentHasEmbeddedImages() {
      const m = this.result.metadata
      if (!m) return false
      const c = m.images_count
      if (typeof c === 'number') return c > 0
      return (m.images || []).length > 0
    },
    waveFillColor() {
      if (!this.documentHasEmbeddedImages) return '#D1D5DB'
      const pct = (this.selectedImage?.ai_indicators && this.selectedImage.ai_indicators.ai_probability) ?? 0
      const n = Number(pct)
      if (n < 35) return '#00FF00'
      if (n <= 70) return '#FFFF00'
      return '#FF1493'
    },
    waveLabel() {
      if (!this.documentHasEmbeddedImages) return 'Вероятность ИИ: -'
      const pct = (this.selectedImage?.ai_indicators && this.selectedImage.ai_indicators.ai_probability) ?? 0
      const n = Number(pct)
      if (n < 35) return 'Вероятность ИИ: низкая'
      if (n <= 70) return 'Вероятность ИИ: средняя'
      return 'Вероятность ИИ: высокая'
    },
    waveLabelClass() {
      if (!this.documentHasEmbeddedImages) return 'wave-strip-label--na'
      const pct = (this.selectedImage?.ai_indicators && this.selectedImage.ai_indicators.ai_probability) ?? 0
      const n = Number(pct)
      if (n < 35) return 'wave-strip-label--low'
      if (n <= 70) return 'wave-strip-label--mid'
      return 'wave-strip-label--high'
    },
    summary() {
      return this.result.summary || {}
    },
    aiIndicators() {
      return this.result.ai_indicators || {
        software_detected: [],
        anomalies: [],
        evidence_from_metadata: []
      }
    },
    evidenceList() {
      return this.aiIndicators.evidence_from_metadata || []
    },
    fileInfo() {
      return this.result.fileInfo || null
    },
    documentAuthorRows() {
      if (this.result.file_type !== 'document') return []
      const source = this.result.metadata?.document_metadata
      if (!source || typeof source !== 'object') return []
      const map = [
        ['creator', 'Автор'],
        ['last_modified_by', 'Последний редактор']
      ]
      const has = (v) => v !== null && v !== undefined && v !== ''
      const rows = map
        .filter(([key]) => has(source[key]))
        .map(([key, label]) => ({ label, value: source[key] }))
      const traceLabel =
        source.generation_trace_label ||
        (source.generation_trace_present ? 'Есть' : 'Нет')
      rows.push({
        label: 'След генерации',
        value: traceLabel,
        helpTooltip: GENERATION_TRACE_HELP_TOOLTIP
      })
      return rows
    },
    documentScores() {
      const s = this.result.summary
      const ai = this.result.ai_indicators
      const md = this.result.metadata
      if (!s && !ai) return null

      const imgs = md?.images || []
      let imagesCombined = '—'
      let imageAvgNum = null
      if (imgs.length > 0) {
        let sum = 0
        for (const img of imgs) {
          const ind = img.ai_indicators || {}
          const per =
            ind.final_score != null
              ? Number(ind.final_score)
              : Number(ind.ai_probability ?? 0)
          sum += Number.isFinite(per) ? per : 0
        }
        imageAvgNum = Math.round(sum / imgs.length)
        imagesCombined = `${imageAvgNum}%`
      }

      const showDocNlp = md && md.document_type === 'word'
      let docNlp = '—'
      let textNum = null
      if (showDocNlp) {
        if (s && s.doc_nlp_ml_available && s.doc_nlp_ml_score != null) {
          textNum = Number(s.doc_nlp_ml_score)
          docNlp = `${textNum}%`
        } else if (s && s.doc_nlp_ml_available === false) {
          docNlp = '-'
        } else docNlp = '—'
      }

      let fin = '—'
      if (showDocNlp) {
        if (imageAvgNum != null && textNum != null) {
          fin = `${Math.round((imageAvgNum + textNum) / 2)}%`
        } else if (imageAvgNum != null) {
          fin = `${imageAvgNum}%`
        } else if (textNum != null) {
          fin = `${textNum}%`
        }
      } else if (imageAvgNum != null) {
        fin = `${imageAvgNum}%`
      } else {
        fin =
          s && s.final_score != null
            ? `${s.final_score}%`
            : s && s.ai_probability != null
              ? `${s.ai_probability}%`
              : ai && ai.final_score != null
                ? `${ai.final_score}%`
                : '—'
      }

      return { imagesCombined, fin, showDocNlp, docNlp }
    }
  },
  methods: {
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    },
    aiChipClass(pct) {
      const n = Number(pct)
      if (n < 35) return 'status-chip-ai-low'
      if (n <= 70) return 'status-chip-ai-mid'
      return 'status-chip-ai-high'
    },
    getProbabilityLabel(probability) {
      if (probability < 30) return 'Низкая вероятность'
      if (probability < 70) return 'Средняя вероятность'
      return 'Высокая вероятность'
    },
    getProbabilityColor(probability) {
      if (probability <= 20) return 'rgba(47, 147, 230, 0.22)'
      if (probability <= 50) return 'rgba(47, 147, 230, 0.35)'
      return 'rgba(47, 147, 230, 0.5)'
    },
    formatFactText(text) {
      if (!text) return []
      return text.split(/\.\s+/).filter(Boolean)
    },
    handleExportPDF() {
      const reportUrl = getReport(this.result.report_url)
      window.open(reportUrl, '_blank')
      this.$emit('export-pdf', reportUrl)
    },
    handleExportJSON() {
      this.$emit('export-json', this.result)
    },
    buildWavePath(phase) {
      const n = 48
      const amplitude = 0.06
      const waves = 4
      let d = 'M 0 0 L 1 0 L 1 1'
      for (let i = 0; i <= n; i++) {
        const x = 1 - i / n
        const y = 1 + amplitude * Math.sin(2 * Math.PI * waves * x - phase)
        d += ` L ${x.toFixed(4)} ${y.toFixed(4)}`
      }
      d += ' L 0 1 Z'
      return d
    },
    waveTick(timestamp) {
      if (!this.waveStartTime) this.waveStartTime = timestamp
      const elapsed = (timestamp - this.waveStartTime) / 1000
      const period = 4
      const phase = (elapsed / period) * 2 * Math.PI
      this.wavePathD = this.buildWavePath(phase)
      this.waveAnimId = requestAnimationFrame((t) => this.waveTick(t))
    }
  },
  mounted() {
    this.waveAnimId = requestAnimationFrame((t) => this.waveTick(t))
  },
  beforeUnmount() {
    if (this.waveAnimId != null) cancelAnimationFrame(this.waveAnimId)
  }
}
</script>
