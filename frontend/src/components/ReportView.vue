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
              <div class="text-sm font-medium text-gray-600">{{ row.label }}</div>
              <div class="break-words text-sm font-mono text-gray-900">{{ row.value }}</div>
            </div>
          </div>
        </div>
        <aside v-if="documentScores" class="w-full shrink-0 sm:w-max sm:max-w-none sm:self-start">
          <dl class="report-doc-summary__metrics font-polonium font-bold uppercase tracking-[0.1em] text-gray-900">
            <div class="report-doc-summary__row">
              <dt class="text-sm sm:text-base">Эвристика</dt>
              <dd class="text-base sm:text-lg">{{ documentScores.meta }}</dd>
            </div>
            <div class="report-doc-summary__row">
              <dt class="text-sm sm:text-base">ML</dt>
              <dd class="text-base sm:text-lg">{{ documentScores.vis }}</dd>
            </div>
            <div class="report-doc-summary__row">
              <dt class="text-sm sm:text-base">Итог</dt>
              <dd class="text-base sm:text-lg">{{ documentScores.fin }}</dd>
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
        <p v-else class="text-sm text-gray-500">Выберите изображение в списке слева</p>
      </div>
    </div>

    <div class="report-actions-row grid gap-3 sm:grid-cols-2 mt-6">
      <button type="button" @click="handleExportPDF" class="primary-btn w-full">Скачать PDF</button>
      <button type="button" @click="handleExportJSON" class="secondary-btn w-full">Скачать JSON</button>
    </div>

    <p class="mt-2 text-xs text-gray-500 leading-snug">
      Оценки носят вероятностный характер. Эвристика и ML используют только метаданные файла (табличные признаки),
      не анализируют «сюжет» изображения.
    </p>
  </div>
  <div class="report-footer-band full-bleed" aria-hidden="true" />
  </div>
</template>

<script>
import MetadataTable from './MetadataTable.vue'
import ImageDetailPanel from './ImageDetailPanel.vue'
import { getReport } from '../services/api'

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
    waveFillColor() {
      const pct = (this.selectedImage?.ai_indicators && this.selectedImage.ai_indicators.ai_probability) ?? 0
      const n = Number(pct)
      if (n < 35) return '#00FF00'
      if (n <= 70) return '#FFFF00'
      return '#FF1493'
    },
    waveLabel() {
      const pct = (this.selectedImage?.ai_indicators && this.selectedImage.ai_indicators.ai_probability) ?? 0
      const n = Number(pct)
      if (n < 35) return 'Вероятность ИИ: низкая'
      if (n <= 70) return 'Вероятность ИИ: средняя'
      return 'Вероятность ИИ: высокая'
    },
    waveLabelClass() {
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
      return map
        .filter(([key]) => has(source[key]))
        .map(([key, label]) => ({ label, value: source[key] }))
    },
    documentScores() {
      const s = this.result.summary
      const ai = this.result.ai_indicators
      if (!s && !ai) return null
      const meta = s && s.metadata_score != null ? `${s.metadata_score}%` : (ai && ai.metadata_score != null ? `${ai.metadata_score}%` : '—')
      let vis = '—'
      if (s && s.metadata_ml_available && s.ml_metadata_score != null) vis = `${s.ml_metadata_score}%`
      else if (s && s.metadata_ml_available === false) vis = '— (модель не загружена)'
      else if (ai && ai.metadata_ml_available && ai.ml_metadata_score != null) vis = `${ai.ml_metadata_score}%`
      else if (ai && ai.metadata_ml_available === false) vis = '— (модель не загружена)'
      const fin =
        s && s.final_score != null
          ? `${s.final_score}%`
          : s && s.ai_probability != null
            ? `${s.ai_probability}%`
            : ai && ai.final_score != null
              ? `${ai.final_score}%`
              : '—'
      return { meta, vis, fin }
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
