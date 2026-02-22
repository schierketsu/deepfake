<template>
  <div class="content-block p-6 md:p-8">
    <div class="mb-4 flex items-center justify-between gap-4">
      <div>
        <p class="soft-label mb-2">Шаг 1</p>
        <h2 class="text-heading-xl font-bold text-ink">Загрузка файла</h2>
      </div>
    </div>

    <div
      @click="openFileDialog"
      @drop="handleDrop"
      @dragover.prevent
      @dragenter.prevent
      @dragleave="isDragging = false"
      @dragenter="isDragging = true"
      :class="[
        'rounded-3xl border p-8 text-center transition-all duration-200 cursor-pointer',
        isDragging ? 'border-accent-400 bg-accent-100 shadow-soft-lg' : 'border-soft-300 bg-soft-100 hover:bg-soft-50'
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
        accept="image/jpeg,image/jpg,image/png,image/heic,image/heif,video/mp4,video/quicktime,video/x-matroska,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        class="hidden"
      />

      <div class="mx-auto flex max-w-2xl flex-col items-center gap-4">
        <div class="text-base md:text-xl font-black italic text-ink">
          JPEG, PNG, HEIC | MP4, MOV, MKV | DOCX, PPTX
        </div>
        <p class="text-heading-lg font-semibold text-ink">
          Перетащите файл сюда или нажмите для выбора
        </p>
        <button
          type="button"
          @click.stop="openFileDialog"
          class="primary-btn mt-1"
          :disabled="isAnalyzing"
        >
          Выбрать файл
        </button>
      </div>
    </div>

    <div v-if="effectiveError" class="mt-5 rounded-2xl border border-danger/40 bg-danger/10 p-4">
      <p class="text-sm text-ink">{{ effectiveError }}</p>
      <button type="button" class="secondary-btn mt-3" @click="openFileDialog">Выбрать другой файл</button>
    </div>
  </div>
</template>

<script>
import { analyzeImage, analyzeVideo, analyzeDocument } from '../services/api'

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
      this.uploadProgress = 0
      this.$emit('analysis-reset')

      if (file.size > this.MAX_FILE_SIZE) {
        this.error = `Файл слишком большой. Максимальный размер: ${this.formatFileSize(this.MAX_FILE_SIZE)}`
        this.$emit('analysis-error', this.error)
        return
      }

      const isImage = file.type.startsWith('image/')
      const isVideo = file.type.startsWith('video/')
      const isDocx = file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || (file.name && file.name.toLowerCase().endsWith('.docx'))

      if (!isImage && !isVideo && !isDocx) {
        this.error = 'Неподдерживаемый тип файла. Используйте изображения, видео или Word (.docx).'
        this.$emit('analysis-error', this.error)
        return
      }

      this.selectedFile = file
      this.analyzeFile(file)
    },

    async analyzeFile(file) {
      this.$emit('analysis-started')
      this.setProgress(8)
      this.$emit('analysis-error', null)

      try {
        let result
        this.setProgress(24)

        if (file.type.startsWith('image/')) {
          result = await analyzeImage(file)
        } else if (file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || (file.name && file.name.toLowerCase().endsWith('.docx'))) {
          result = await analyzeDocument(file)
        } else {
          result = await analyzeVideo(file)
        }

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
          this.error = 'Эндпоинт анализа документа не найден (404). Проверьте, что backend обновлен и маршрут /api/analyze/document доступен.'
        } else if (status === 413) {
          this.error = 'Файл превышает допустимый размер на сервере.'
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

    clearFile() {
      this.selectedFile = null
      this.error = null
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
