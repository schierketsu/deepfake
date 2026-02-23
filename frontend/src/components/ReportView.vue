<template>
  <div class="content-block p-5 sm:p-6">
    <div class="flex flex-wrap items-start justify-between gap-4 mb-6">
      <div>
        <h2 class="font-polonium text-3xl font-bold text-gray-900">Результаты проверки</h2>
        <div v-if="fileInfo" class="mt-1 text-sm text-gray-500">
          <p class="font-medium text-gray-900 break-words">{{ fileInfo.name }}</p>
          <p>{{ formatFileSize(fileInfo.size) }}</p>
        </div>
      </div>
      <img
        v-if="documentLogo"
        :src="documentLogo"
        :alt="documentTypeLabel"
        class="h-8 w-auto object-contain"
      />
      <span v-else class="text-sm text-gray-600">{{ documentTypeLabel }}</span>
    </div>

    <div class="mb-6">
      <MetadataTable :metadata="result.metadata" :file-type="result.file_type" :show-only-document-meta="true" />
    </div>

    <div v-if="evidenceList.length > 0" class="card p-4 mb-6">
      <h3 class="font-polonium text-xl font-bold text-gray-900">Факты из метаданных</h3>
      <ul class="mt-3 space-y-2">
        <li v-for="(fact, index) in evidenceList" :key="index" class="text-sm text-gray-700 border-l-2 border-gray-200 pl-3">
          <span v-for="(paragraph, pIndex) in formatFactText(fact)" :key="pIndex">{{ paragraph }}{{ pIndex < formatFactText(fact).length - 1 ? '. ' : '' }}</span>
        </li>
      </ul>
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
            <span class="status-chip text-xs">ИИ: {{ (img.ai_indicators && img.ai_indicators.ai_probability) ?? 0 }}%</span>
          </button>
        </nav>
        <p v-if="!(result.metadata?.images || []).length" class="text-sm text-gray-500">Нет изображений</p>
      </aside>
      <div class="results-detail" ref="detailPanel">
        <template v-if="selectedImage">
          <ImageDetailPanel :image="selectedImage" :image-index="selectedId" />
        </template>
        <p v-else class="text-sm text-gray-500">Выберите изображение в списке слева</p>
      </div>
    </div>

    <div class="grid gap-3 sm:grid-cols-2">
      <button @click="handleExportPDF" class="primary-btn w-full">Скачать PDF</button>
      <button @click="handleExportJSON" class="secondary-btn w-full">Скачать JSON</button>
    </div>
  </div>
</template>

<script>
import MetadataTable from './MetadataTable.vue'
import ImageDetailPanel from './ImageDetailPanel.vue'
import { getReport } from '../services/api'
import logowordUrl from '../public/logoword.png'
import logopptxUrl from '../public/logopptx.png'

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
      selectedId: 0
    }
  },
  computed: {
    documentTypeLabel() {
      const t = this.result.metadata?.document_type
      if (t === 'powerpoint') return 'PowerPoint'
      if (t === 'word') return 'Word'
      return 'Документ'
    },
    documentLogo() {
      const t = this.result.metadata?.document_type
      if (t === 'word') return logowordUrl
      if (t === 'powerpoint') return logopptxUrl
      return null
    },
    selectedImage() {
      const images = this.result.metadata?.images || []
      if (this.selectedId < 0 || this.selectedId >= images.length) return null
      return images[this.selectedId] || null
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
    }
  }
}
</script>
