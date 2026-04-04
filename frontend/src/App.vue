<template>
  <div class="app-shell">
    <header class="header-dark border-b border-[#333]">
      <div class="mx-auto max-w-6xl px-3 py-4 sm:px-6 sm:py-6">
        <div>
          <h1 class="font-polonium text-[clamp(2rem,9.5vw,2.75rem)] leading-[1.05] sm:text-[86px] sm:leading-[74px] font-normal normal-case tracking-normal text-[#FFF5E5] break-words">
            необманывай.рф
          </h1>
          <p class="mt-1 text-xs leading-snug text-[#FFF5E5] sm:text-sm sm:leading-normal">
            Проверьте, сделал ли студент работу самостоятельно
          </p>
        </div>
        <FileUpload
          class="mt-6 mb-0"
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
      </div>
    </header>

    <main
      class="mx-auto w-full max-w-6xl flex-1 px-3 pt-5 sm:px-6 sm:pt-8"
      :class="
        analysisResult
          ? 'pb-0 sm:pb-0'
          : !isAnalyzing
            ? 'pb-12 sm:pb-16'
            : 'pb-6 sm:pb-8'
      "
    >
      <div v-if="isAnalyzing" class="card mb-6 p-4 flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:gap-4">
        <div class="h-8 w-8 animate-spin rounded-full border-2 border-gray-200 border-t-gray-700" />
        <div>
          <p class="font-medium text-ink">Анализ документа…</p>
          <p class="text-sm text-gray-500">Подождите, это может занять время.</p>
        </div>
      </div>

      <div v-else-if="!analysisResult" class="card mb-0 px-4 py-6 text-center sm:p-8">
        <p class="text-sm text-gray-500 mb-2">Готово к проверке</p>
        <h2 class="font-polonium text-2xl font-bold leading-tight text-gray-900 sm:text-3xl sm:leading-normal">
          Загрузите DOCX или PPTX
        </h2>
      </div>

      <ReportView
        v-if="analysisResult"
        :result="analysisResult"
        @export-pdf="exportPDF"
        @export-json="exportJSON"
      />
    </main>

    <footer class="site-footer mt-auto">
      <div
        class="mx-auto max-w-6xl px-3 pb-3 text-center text-sm text-[#FFF5E5]/80 sm:px-6 sm:pb-4"
        :class="
          analysisResult
            ? 'max-sm:pt-5'
            : !isAnalyzing
              ? 'pt-6 sm:pt-8'
              : 'pt-4'
        "
      >
        <p>team @шаньга</p>
        <p class="mt-0.5">Антидипфейк: Вызов • IT-Планета 2026</p>
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
