<template>
  <div class="app-shell">
    <header class="border-b border-soft-700 bg-ink text-soft-50">
      <div class="mx-auto flex max-w-shell items-start justify-between gap-6 px-5 py-6 md:px-8 md:py-8">
        <div>
          <p class="text-sm md:text-base uppercase tracking-[0.08em] text-accent-400 mb-3 font-black">Антидипфейк: Вызов • IT-Планета 2026</p>
          <h1 class="font-display text-[3rem] md:text-[4.5rem] font-black italic leading-[0.98]">
            <span class="text-accent-400">Анализ</span>
            <span class="text-soft-50"> метаданных</span>
          </h1>
          <p class="-mt-2 max-w-2xl text-soft-200 text-base md:text-lg font-black">
            Выявите ИИ-модификации в изображениях, видео и документах
          </p>
        </div>

      </div>
    </header>

    <main class="mx-auto w-full max-w-shell flex-1 px-5 py-8 md:px-8 md:py-10">
      <FileUpload
        class="mb-8"
        :is-analyzing="isAnalyzing"
        :progress="uploadProgress"
        :error-message="analysisError"
        @file-uploaded="handleFileUploaded"
        @analysis-started="handleAnalysisStarted"
        @analysis-completed="handleAnalysisCompleted"
        @analysis-progress="handleAnalysisProgress"
        @analysis-error="handleAnalysisError"
        @analysis-reset="handleReset"
      />

      <div v-if="isAnalyzing" class="card-soft mb-8 p-6 border-accent-400">
        <div class="flex items-center gap-4">
          <div class="h-10 w-10 animate-spin rounded-full border-2 border-soft-200 border-t-accent-500" />
          <div>
            <p class="font-semibold text-ink">Выполняем анализ файла</p>
            <p class="text-sm text-soft-700">Это может занять некоторое время для больших видео и документов.</p>
          </div>
        </div>
      </div>

      <div v-else-if="!analysisResult" class="card-soft p-8 text-center">
        <p class="soft-label mb-2">Готово к работе</p>
        <h2 class="text-heading-xl font-bold text-ink">Загрузите файл для старта анализа</h2>
      </div>

      <ReportView
        v-if="analysisResult"
        :result="analysisResult"
        class="mb-8"
        @export-pdf="exportPDF"
        @export-json="exportJSON"
      />
    </main>

    <footer class="border-t border-soft-700 bg-ink">
      <div class="mx-auto max-w-shell px-5 py-6 text-center text-sm text-soft-200 md:px-8">
        <p>team @ӧшкамӧшка</p>
      </div>
    </footer>
  </div>
</template>

<script>
import FileUpload from './components/FileUpload.vue'
import ReportView from './components/ReportView.vue'

export default {
  name: 'App',
  components: {
    FileUpload,
    ReportView
  },
  data() {
    return {
      analysisResult: null,
      isAnalyzing: false,
      uploadProgress: 0,
      analysisError: null
    }
  },
  computed: {
    statusMessage() {
      if (this.analysisError) return this.analysisError
      if (this.isAnalyzing) return 'Файл анализируется, пожалуйста подождите.'
      if (this.analysisResult) return 'Анализ завершен. Можно изучить детали и экспортировать отчет.'
      return 'Ожидание файла для анализа.'
    }
  },
  methods: {
    handleAnalysisStarted() {
      this.isAnalyzing = true
      this.analysisError = null
      this.uploadProgress = Math.max(this.uploadProgress, 8)
    },
    handleAnalysisCompleted() {
      this.isAnalyzing = false
      if (this.analysisError && !this.analysisResult) {
        this.uploadProgress = 0
      }
    },
    handleFileUploaded(result) {
      this.analysisResult = result
      this.analysisError = null
      this.uploadProgress = 100
    },
    handleAnalysisProgress(value) {
      this.uploadProgress = value
    },
    handleAnalysisError(message) {
      this.analysisError = message
    },
    handleReset() {
      this.analysisResult = null
      this.analysisError = null
      this.uploadProgress = 0
    },
    exportPDF(url) {
      return url
    },
    exportJSON(data) {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'analysis_report.json'
      a.click()
      URL.revokeObjectURL(url)
    }
  }
}
</script>
