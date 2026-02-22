<template>
  <div class="content-block p-6 md:p-8">
    <div class="mb-8 flex flex-wrap items-start justify-between gap-4">
      <div>
        <p class="soft-label mb-2">Шаг 2</p>
        <h2 class="text-heading-xl md:text-display-lg font-black text-ink">Результаты анализа</h2>
        <div v-if="fileInfo" class="mt-3 text-sm text-soft-700">
          <p class="font-semibold text-ink break-words">{{ fileInfo.name }}</p>
          <p>{{ formatFileSize(fileInfo.size) }}</p>
        </div>
      </div>
      <div class="text-accent-300 text-4xl md:text-5xl font-black italic leading-none">
        {{ result.file_type === 'document' ? 'Word документ' : result.file_type }}
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
      <div class="card-soft relative min-h-[220px] overflow-hidden p-6 border-soft-700 bg-soft-900">
        <p class="mb-4 text-sm md:text-base uppercase tracking-[0.08em] text-soft-300 font-black">Вероятность ИИ-вмешательства</p>
        <div class="absolute inset-x-0 bottom-0 transition-all duration-500" :style="{ height: `${summary.ai_probability || 0}%`, backgroundColor: getProbabilityColor(summary.ai_probability || 0) }" />
        <div class="relative z-10">
          <p class="title-percent mt-16 text-soft-50 text-center text-[4.5rem] md:text-[5.5rem] italic">{{ summary.ai_probability || 0 }}%</p>
        </div>
      </div>

      <div class="grid gap-4">
        <div class="card-soft p-5">
          <p class="soft-label mb-1">Местоположение</p>
          <p class="text-body-lg text-ink">{{ summary.location || 'Не указано' }}</p>
        </div>
        <div class="card-soft p-5">
          <p class="soft-label mb-1">Дата и время</p>
          <p class="text-body-lg text-ink">{{ summary.date_time || 'Не указано' }}</p>
        </div>
        <div class="card-soft p-5">
          <p class="soft-label mb-1">Источник</p>
          <p class="text-body-lg text-ink break-words">{{ summary.source || 'Неизвестно' }}</p>
        </div>
      </div>
    </div>

    <div v-if="evidenceList.length > 0" class="mt-6 card-soft p-6">
      <h3 class="text-heading-lg font-bold text-ink">Факты из метаданных</h3>
      <p class="mt-1 text-sm text-soft-700">Вывод основан на C2PA/Content Credentials и цепочке доверия.</p>
      <ul class="mt-4 space-y-3">
        <li
          v-for="(fact, index) in evidenceList"
          :key="index"
          class="rounded-2xl border border-soft-200 bg-soft-50 p-4"
        >
          <p class="mb-2 text-sm font-semibold text-soft-700">Факт {{ index + 1 }}</p>
          <div class="space-y-2 text-sm text-ink">
            <p v-for="(paragraph, pIndex) in formatFactText(fact)" :key="pIndex">{{ paragraph }}</p>
          </div>
        </li>
      </ul>
    </div>

    <div v-if="aiIndicators.software_detected.length > 0 || aiIndicators.anomalies.length > 0" class="mt-6 card-soft p-6">
      <h3 class="text-heading-lg font-bold text-ink">Обнаруженные признаки ИИ</h3>

      <div v-if="aiIndicators.software_detected.length > 0" class="mt-4">
        <p class="soft-label mb-2">Обнаруженное ПО</p>
        <div class="flex flex-wrap gap-2">
          <span v-for="software in aiIndicators.software_detected" :key="software" class="status-chip bg-soft-900 text-soft-100">
            {{ software }}
          </span>
        </div>
      </div>

      <div v-if="aiIndicators.anomalies.length > 0" class="mt-4">
        <p class="soft-label mb-2">Аномалии</p>
        <div class="space-y-2">
          <div
            v-for="(anomaly, index) in aiIndicators.anomalies"
            :key="index"
            class="rounded-2xl border border-soft-200 bg-soft-50 p-3 text-sm text-ink"
          >
            {{ anomaly }}
          </div>
        </div>
      </div>
    </div>

    <div class="mt-6">
      <div class="card-soft overflow-hidden">
        <button
          @click="showMetadata = !showMetadata"
          class="flex w-full items-center justify-between bg-white p-4 text-left"
        >
          <h3 class="text-heading-lg font-bold text-ink">Детальные метаданные</h3>
          <svg
            class="h-5 w-5 text-ink transition-transform duration-200"
            :class="{ 'rotate-180': showMetadata }"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div v-show="showMetadata" class="border-t border-soft-200 bg-soft-50 p-5">
          <MetadataTable :metadata="result.metadata" :file-type="result.file_type" />
        </div>
      </div>
    </div>

    <div class="mt-6 grid gap-3 md:grid-cols-2">
      <button @click="handleExportPDF" class="primary-btn w-full">Экспорт PDF</button>
      <button @click="handleExportJSON" class="secondary-btn w-full">Экспорт JSON</button>
    </div>
  </div>
</template>

<script>
import MetadataTable from './MetadataTable.vue'
import { getReport } from '../services/api'

export default {
  name: 'ReportView',
  components: {
    MetadataTable
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
      showMetadata: false
    }
  },
  computed: {
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
