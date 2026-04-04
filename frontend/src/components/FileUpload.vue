<template>
  <div class="content-block p-4 sm:p-6">
    <h2 class="font-polonium text-2xl font-bold text-gray-900 mb-3 sm:mb-4 sm:text-3xl">Загрузка файла</h2>

    <div
      @click="openFileDialog"
      @drop="handleDrop"
      @dragover.prevent
      @dragenter.prevent
      @dragleave="isDragging = false"
      @dragenter="isDragging = true"
      :class="[
        'file-upload-dropzone rounded-lg border-2 border-dashed p-5 text-center cursor-pointer transition-colors sm:p-8',
        isDragging ? 'file-upload-dropzone--drag border-[#212121] bg-gray-100' : 'border-[#212121] bg-[#FFFFFF] hover:bg-[#FFFFFF]'
      ]"
      role="button"
      tabindex="0"
      @keydown.enter.prevent="openFileDialog"
      @keydown.space.prevent="openFileDialog"
    >
      <input
        ref="fileInput"
        type="file"
        @change="handleFileSelect"
        accept=".docx,.pptx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation"
        class="hidden"
      />

      <div class="mx-auto flex max-w-3xl flex-col items-center gap-2">
        <p class="text-base font-medium text-gray-900">
          DOCX, PPTX
        </p>
        <p class="text-sm text-gray-500 mt-1">
          Перетащите документ сюда или нажмите для выбора
        </p>
        <button
          type="button"
          @click.stop="openFileDialog"
          class="primary-btn mt-3"
          :disabled="isAnalyzing"
        >
          Выбрать файл
        </button>
      </div>
    </div>

    <div
      v-if="effectiveError"
      class="file-upload-error-banner mt-4 rounded-lg border border-red-200 bg-red-50 p-4"
    >
      <p class="text-sm">{{ effectiveError }}</p>
      <button
        v-if="!formatUnsupported"
        type="button"
        class="secondary-btn mt-3"
        @click="openFileDialog"
      >
        Выбрать другой файл
      </button>
    </div>
  </div>
</template>

<script>
import { analyzeDocument } from '../services/api'

export default {
  name: 'FileUpload',
  props: {
    isAnalyzing: {
      type: Boolean,
      default: false
    },
    progress: {
      type: Number,
      default: 0
    },
    errorMessage: {
      type: String,
      default: null
    }
  },
  emits: ['file-uploaded', 'analysis-started', 'analysis-completed', 'analysis-progress', 'analysis-error', 'analysis-reset'],
  data() {
    return {
      selectedFile: null,
      isDragging: false,
      error: null,
      formatUnsupported: false,
      uploadProgress: 0,
      MAX_FILE_SIZE: 100 * 1024 * 1024
    }
  },
  computed: {
    safeProgress() {
      return Math.min(100, Math.max(this.progress || this.uploadProgress, 0))
    },
    effectiveError() {
      return this.error || this.errorMessage
    }
  },
  methods: {
    openFileDialog() {
      this.$refs.fileInput?.click()
    },
    handleDrop(event) {
      event.preventDefault()
      this.isDragging = false

      const files = event.dataTransfer.files
      if (files.length > 0) {
        this.processFile(files[0])
      }
    },

    handleFileSelect(event) {
      const files = event.target.files
      if (files.length > 0) {
        this.processFile(files[0])
      }
    },

    processFile(file) {
      this.error = null
      this.formatUnsupported = false
      this.uploadProgress = 0
      this.$emit('analysis-reset')

      if (file.size > this.MAX_FILE_SIZE) {
        this.error = `Файл слишком большой. Максимальный размер: ${this.formatFileSize(this.MAX_FILE_SIZE)}`
        this.$emit('analysis-error', this.error)
        return
      }

      const lowerName = (file.name || '').toLowerCase()
      const isDocx = file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || lowerName.endsWith('.docx')
      const isPptx = file.type === 'application/vnd.openxmlformats-officedocument.presentationml.presentation' || lowerName.endsWith('.pptx')

      if (!isDocx && !isPptx) {
        this.formatUnsupported = true
        this.error = 'Данный формат файла не поддерживается.'
        this.$emit('analysis-error', this.error)
        return
      }

      this.selectedFile = file
      this.analyzeFile(file)
    },

    async analyzeFile(file) {
      this.$emit('analysis-started')
      this.setProgress(8)
      this.formatUnsupported = false
      this.$emit('analysis-error', null)

      try {
        this.setProgress(24)
        const result = await analyzeDocument(file)

        this.setProgress(100)
        this.$emit('file-uploaded', {
          ...result,
          fileInfo: {
            name: file.name,
            size: file.size
          }
        })
      } catch (error) {
        const status = error.response?.status
        const detail = error.response?.data?.detail
        if (!error.response) {
          this.error = 'Сервер недоступен. Проверьте запуск backend на 127.0.0.1:8000.'
        } else if (status === 404) {
          this.error = 'Эндпоинт анализа офисного файла не найден (404). Проверьте, что backend обновлен и маршрут /api/analyze/document доступен.'
        } else if (status === 413) {
          this.error = 'Файл превышает допустимый размер на сервере.'
        } else if (status === 400 && this._isUnsupportedFormatDetail(detail)) {
          this.formatUnsupported = true
          this.error = 'Данный формат файла не поддерживается.'
        } else {
          this.error = typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? (detail[0]?.msg || detail[0] || 'Произошла ошибка при анализе файла')
              : 'Произошла ошибка при анализе файла'
        }
        this.$emit('analysis-error', this.error)
      } finally {
        this.$emit('analysis-completed')
      }
    },

    setProgress(value) {
      this.uploadProgress = value
      this.$emit('analysis-progress', value)
    },

    _isUnsupportedFormatDetail(detail) {
      const d =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? String(detail[0]?.msg || detail[0] || '')
            : ''
      return /DOCX/i.test(d) && /PPTX/i.test(d) && /поддержива/i.test(d)
    },

    clearFile() {
      this.selectedFile = null
      this.error = null
      this.formatUnsupported = false
      this.uploadProgress = 0
      this.$emit('analysis-reset')
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },

    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    }
  }
}
</script>
