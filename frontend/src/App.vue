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

        <a
          href="https://github.com/schierketsu"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex h-12 w-12 items-center justify-center rounded-2xl border border-soft-300 bg-white text-ink transition hover:bg-soft-100"
          title="Открыть GitHub"
          aria-label="Открыть GitHub"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
        </a>
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
