<template>
  <div class="app-shell">
    <header class="header-dark border-b border-[#333]">
      <div class="mx-auto max-w-6xl px-4 py-5 sm:px-6 sm:py-6">
        <div>
          <h1 class="font-polonium text-6xl sm:text-[86px] font-normal leading-[74px] normal-case tracking-normal text-[#FFF5E5]">
            необманывай.рф
          </h1>
          <p class="mt-1 text-sm text-[#FFF5E5]">
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

    <main class="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 sm:py-8">
      <div v-if="isAnalyzing" class="card mb-6 p-4 flex items-center gap-4">
        <div class="h-8 w-8 animate-spin rounded-full border-2 border-gray-200 border-t-gray-700" />
        <div>
          <p class="font-medium text-ink">Анализ документа…</p>
          <p class="text-sm text-gray-500">Подождите, это может занять время.</p>
        </div>
      </div>

      <div v-else-if="!analysisResult" class="card p-8 text-center">
        <p class="text-sm text-gray-500 mb-2">Готово к проверке</p>
        <h2 class="font-polonium text-3xl font-bold text-gray-900">Загрузите DOCX или PPTX</h2>
      </div>

      <ReportView
        v-if="analysisResult"
        :result="analysisResult"
        class="mb-8"
        @export-pdf="exportPDF"
        @export-json="exportJSON"
      />
    </main>

    <footer class="border-t border-gray-200 bg-white mt-auto">
      <div class="mx-auto max-w-6xl px-4 py-4 text-center text-sm text-gray-500">
        <p>team @шаньга</p>
        <p class="mt-1">Антидипфейк: Вызов • IT-Планета 2026</p>
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
